"""Tests for the Bolão scoring rules (progressive knockout weights).

Announced rules: group stage 1 pt per exact position; then per correct pick —
16-avos (r32) +2 · oitavas (r16) +3 · quartas (qf) +4 · semi (sf) +5 ·
final/campeão +10. Third place match is not scored.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECOND = ROOT / "secondstage"

RULES = {"r32": 2, "r16": 3, "qf": 4, "sf": 5, "final": 10}
MATCH_COUNTS = {"r32": 16, "r16": 8, "qf": 4, "sf": 2, "final": 1}


def load_ko() -> dict:
    raw = (SECOND / "data.js").read_text(encoding="utf-8").strip()
    return json.loads(raw[raw.index("=") + 1:].rstrip(";"))


def module_constant(script: str, name: str):
    """Read a top-level constant from a script without importing it (avoids deps)."""
    tree = ast.parse((ROOT / "scripts" / script).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{script} has no top-level {name}")


def score(K: dict) -> dict[str, int]:
    """Python mirror of the scoring in secondstage/common.js."""
    totals = {}
    for p in K["players"]:
        pts = K["groupPoints"].get(p) or 0
        for s in K["stages"]:
            picks = s["picks"].get(p) or []
            for i, m in enumerate(s["matches"]):
                if m.get("winner") and i < len(picks) and picks[i] == m["winner"]:
                    pts += s["weight"]
        totals[p] = pts
    return totals


class TestDataWeights(unittest.TestCase):
    def setUp(self):
        self.K = load_ko()
        self.stages = {s["key"]: s for s in self.K["stages"]}

    def test_stage_weights_follow_the_rules(self):
        self.assertEqual({k: s["weight"] for k, s in self.stages.items()}, RULES)

    def test_stage_order_and_match_counts(self):
        self.assertEqual([s["key"] for s in self.K["stages"]], list(RULES))
        self.assertEqual({k: len(s["matches"]) for k, s in self.stages.items()}, MATCH_COUNTS)

    def test_final_is_a_single_match(self):
        # "acertar o campeão vale 10" — one match, no 3rd-place tie in the data
        self.assertEqual(len(self.stages["final"]["matches"]), 1)


class TestScriptsEnforceWeights(unittest.TestCase):
    def test_build_data_constant(self):
        self.assertEqual(module_constant("build_data.py", "STAGE_WEIGHTS"), RULES)

    def test_fetch_knockout_constant(self):
        self.assertEqual(module_constant("fetch_knockout.py", "STAGE_WEIGHTS"), RULES)

    def test_scripts_write_weight_back(self):
        # both scripts must stamp the weights onto every stage before writing data.js
        for script in ("build_data.py", "fetch_knockout.py"):
            src = (ROOT / "scripts" / script).read_text(encoding="utf-8")
            self.assertIn('s["weight"] = STAGE_WEIGHTS[s["key"]]', src, script)


class TestScoring(unittest.TestCase):
    def test_current_data_scores_consistently(self):
        K = load_ko()
        totals = score(K)
        # every total ≥ its group points, and knockout part is a sane sum
        for p in K["players"]:
            self.assertGreaterEqual(totals[p], K["groupPoints"].get(p) or 0, p)

    def test_perfect_player_maxes_at_92_knockout_points(self):
        # 16×2 + 8×3 + 4×4 + 2×5 + 1×10 = 92
        K = {
            "players": ["Perfeito"],
            "groupPoints": {"Perfeito": 0},
            "stages": [
                {
                    "key": k,
                    "weight": RULES[k],
                    "matches": [{"a": "X", "b": "Y", "winner": "X"}] * n,
                    "picks": {"Perfeito": ["X"] * n},
                }
                for k, n in MATCH_COUNTS.items()
            ],
        }
        self.assertEqual(score(K)["Perfeito"], 92)

    def test_each_stage_pays_its_own_weight(self):
        for key, w in RULES.items():
            K = {
                "players": ["A", "B"],
                "groupPoints": {"A": 0, "B": 0},
                "stages": [{
                    "key": key,
                    "weight": w,
                    "matches": [{"a": "X", "b": "Y", "winner": "Y"}],
                    "picks": {"A": ["Y"], "B": ["X"]},
                }],
            }
            totals = score(K)
            self.assertEqual(totals["A"], w, key)   # correct pick pays the weight
            self.assertEqual(totals["B"], 0, key)   # wrong pick pays nothing

    def test_undecided_matches_pay_nothing(self):
        K = {
            "players": ["A"],
            "groupPoints": {"A": 5},
            "stages": [{
                "key": "final",
                "weight": 10,
                "matches": [{"a": "X", "b": "Y", "winner": None}],
                "picks": {"A": ["X"]},
            }],
        }
        self.assertEqual(score(K)["A"], 5)


class TestNoStaleHardcodedPoints(unittest.TestCase):
    """The pages must not hardcode the old flat '+2 por acerto' anywhere."""

    STALE = re.compile(r"vale \+?2 pontos|\+2 por acerto|\+2</b> pra cada|✓ \+2\b|\+ 2 por acerto")

    def test_html_pages(self):
        for page in sorted(SECOND.glob("*.html")):
            hits = self.STALE.findall(page.read_text(encoding="utf-8"))
            self.assertEqual(hits, [], f"{page.name} still hardcodes flat +2: {hits}")

    def test_common_js_uses_stage_weight(self):
        src = (SECOND / "common.js").read_text(encoding="utf-8")
        self.assertIn("s.weight", src)
        self.assertEqual(self.STALE.findall(src), [])


class TestPagesFollowActiveStage(unittest.TestCase):
    """Pages must derive the featured stage from data.js, never hardcode a round."""

    def test_chaveamento_builds_columns_from_stages(self):
        src = (SECOND / "chaveamento.html").read_text(encoding="utf-8")
        # every column label comes from s.label — a quoted literal means a
        # hardcoded round crept back in
        self.assertNotIn('colWrap("', src)
        self.assertIn("K.stages.map", src)

    def test_confrontos_opens_on_active_stage(self):
        src = (SECOND / "confrontos.html").read_text(encoding="utf-8")
        self.assertIn("stages.findIndex(s => s.active)", src)

    def test_matriz_opens_on_active_stage(self):
        src = (SECOND / "matriz.html").read_text(encoding="utf-8")
        self.assertIn("K.stages.findIndex(s => s.active)", src)


if __name__ == "__main__":
    unittest.main()
