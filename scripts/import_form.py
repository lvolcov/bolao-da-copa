"""Load knockout picks from a Google Forms responses CSV into secondstage/data.js.

The form has one "Quem é você?" column and one column per confronto titled
"Jogo N: TimeA × TimeB — quem avança?". The stage is detected automatically by
matching the fixture pairs in the headers against each stage's matches in
data.js — so the same script works for oitavas, quartas, semi and final.

- Names must match K.players exactly; picks must be one of the two fixture teams
  (fails loudly otherwise, like build_data.py).
- If a player answered more than once, the LAST response in the file wins
  (the sheet is append-ordered).
- Players who haven't answered simply have no picks (the UI shows them pending).
- Tallies/backers are recomputed, `active` flips to the imported stage and the
  stage weights are re-stamped (STAGE_WEIGHTS must match build_data's).

Usage:  python3 scripts/import_form.py respostas_oitavas.csv
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "secondstage" / "data.js"

# Must match build_data.STAGE_WEIGHTS / fetch_knockout.STAGE_WEIGHTS.
STAGE_WEIGHTS = {"r32": 2, "r16": 3, "qf": 4, "sf": 5, "final": 10}

# separator needs surrounding whitespace, or the x inside "México" would match
GAME_RE = re.compile(r"Jogo\s*(\d+)\s*:\s*(.+?)\s+[×x]\s+(.+?)\s*—")
NAME_COL_RE = re.compile(r"quem é você", re.IGNORECASE)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 scripts/import_form.py <responses.csv>")
    rows = list(csv.reader(open(sys.argv[1], encoding="utf-8-sig")))
    header, body = rows[0], [r for r in rows[1:] if any(r)]

    name_col = next((i for i, h in enumerate(header) if NAME_COL_RE.search(h)), None)
    if name_col is None:
        sys.exit("No 'Quem é você?' column found")
    games = []  # (column index, game number, team a, team b)
    for i, h in enumerate(header):
        m = GAME_RE.search(h)
        if m:
            games.append((i, int(m.group(1)), m.group(2).strip(), m.group(3).strip()))
    games.sort(key=lambda g: g[1])
    if not games:
        sys.exit("No 'Jogo N: A × B' columns found")

    raw = DATA_JS.read_text(encoding="utf-8").strip()
    K = json.loads(raw[raw.index("=") + 1:].rstrip(";"))

    # detect the stage: every form fixture pair must equal the stage's match pair
    form_pairs = [{a, b} for _, _, a, b in games]
    stage = None
    for s in K["stages"]:
        if len(s["matches"]) == len(games) and all(
            {m["a"], m["b"]} == p for m, p in zip(s["matches"], form_pairs)
        ):
            stage = s
            break
    if stage is None:
        sys.exit("Form fixtures don't match any stage in data.js — "
                 "check the fixtures (step 2 of the README checklist) and the header order.")

    # last response per player wins
    by_player, unknown = {}, []
    for r in body:
        name = r[name_col].strip()
        if name not in K["players"]:
            unknown.append(name)
            continue
        by_player[name] = r
    if unknown:
        sys.exit(f"Names not in K.players: {sorted(set(unknown))}")

    errors, picks = [], {}
    for p, r in by_player.items():
        picks[p] = []
        for col, n, a, b in games:
            v = (r[col] or "").strip() or None
            if v is not None and v not in (a, b):
                errors.append(f"Jogo {n}: {p} picked '{v}', not in ({a}/{b})")
            picks[p].append(v)
    if errors:
        sys.exit("Pick mismatches:\n" + "\n".join(errors))

    stage["picks"] = picks
    for mi, m in enumerate(stage["matches"]):
        backA = [p for p in K["players"] if p in picks and picks[p][mi] == m["a"]]
        backB = [p for p in K["players"] if p in picks and picks[p][mi] == m["b"]]
        m["backA"], m["backB"] = backA, backB
        m["tallyA"], m["tallyB"] = len(backA), len(backB)

    for s in K["stages"]:
        s["active"] = s["key"] == stage["key"]
        s["weight"] = STAGE_WEIGHTS[s["key"]]

    DATA_JS.write_text("window.KO=" + json.dumps(K, ensure_ascii=False) + ";\n", encoding="utf-8")
    missing = [p for p in K["players"] if p not in picks]
    print(f"Imported {len(picks)}/{len(K['players'])} palpites into stage '{stage['key']}'")
    if missing:
        print(f"  pendentes: {', '.join(missing)}")
    for m in stage["matches"]:
        print(f"  {m['a']} {m['tallyA']} x {m['tallyB']} {m['b']}")


if __name__ == "__main__":
    main()
