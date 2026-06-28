"""Rebuild secondstage/data.js from the Bolão Excel sheet.

This loads everyone's group-stage order and knockout picks out of the sheet
(`PontuaçãoPorJogo`), recomputes the vote tallies / who-voted-for-whom for every
knockout confronto, and writes them back into `secondstage/data.js` — without
touching the parts that are maintained elsewhere (crests, group tables, match
fixtures, results/winners). It also refreshes `public/predictions.json` for the
first-stage GitHub Pages site.

Run this whenever the picks change (e.g. a new stage's palpites came in):

    python scripts/build_data.py "Copy of Bolão da Copa.xlsx"

If no path is given it uses the newest *.xlsx in the repo root.

HOW STAGES MAP
--------------
Each knockout stage is a block of labelled rows in the sheet, one row per match,
one column per apostador. The row label prefix is mapped to the stage `key` in
data.js via SECTION_MAP below. The 32-team first knockout round ("16-avos") is
labelled "Round 16" in the sheet (16 matches). When the next stages open, the
sheet will add new blocks — just make sure their label prefix is in SECTION_MAP.

IMPORTANT for a NEW stage: the fixtures (team a vs b) for that stage must already
be set in data.js *before* running this, because tallies are computed by matching
each pick against the two teams of each confronto. See README → "Updating for the
next stage" for the full checklist.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "secondstage" / "data.js"
PREDICTIONS = ROOT / "public" / "predictions.json"
SHEET = "PontuaçãoPorJogo"

# Row-label prefix in the sheet  ->  stage key in data.js.
# Add a line here when a new stage's block appears with a different label.
SECTION_MAP = {
    "Round 16": "r32",   # 16-avos de final (32 teams, 16 matches)
    "Oitavas": "r16",
    "Round 8": "r16",
    "Quartas": "qf",
    "Round 4": "qf",
    "Semi": "sf",
    "Round 2": "sf",
    "Final": "final",
}

PT2EN = {
    "México": "Mexico", "Coreia do Sul": "South Korea", "República Tcheca": "Czechia", "África do Sul": "South Africa",
    "Suíça": "Switzerland", "Canadá": "Canada", "Bósnia e Herzegovina": "Bosnia-Herzegovina", "Catar": "Qatar",
    "Brasil": "Brazil", "Marrocos": "Morocco", "Escócia": "Scotland", "Haiti": "Haiti",
    "Estados Unidos": "United States", "Turquia": "Turkey", "Paraguai": "Paraguay", "Austrália": "Australia",
    "Alemanha": "Germany", "Costa do Marfim": "Ivory Coast", "Equador": "Ecuador", "Curaçao": "Curaçao",
    "Países Baixos": "Netherlands", "Japão": "Japan", "Suécia": "Sweden", "Tunísia": "Tunisia",
    "Bélgica": "Belgium", "Irã": "Iran", "Egito": "Egypt", "Nova Zelândia": "New Zealand",
    "Espanha": "Spain", "Uruguai": "Uruguay", "Arábia Saudita": "Saudi Arabia", "Cabo Verde": "Cape Verde Islands",
    "França": "France", "Noruega": "Norway", "Senegal": "Senegal", "Iraque": "Iraq",
    "Argentina": "Argentina", "Áustria": "Austria", "Argélia": "Algeria", "Jordânia": "Jordan",
    "Portugal": "Portugal", "Colômbia": "Colombia", "Congo": "Congo DR", "Uzbequistão": "Uzbekistan",
    "Inglaterra": "England", "Croácia": "Croatia", "Gana": "Ghana", "Panamá": "Panama",
}


def stage_for(label: str) -> str | None:
    for prefix, key in SECTION_MAP.items():
        if label.startswith(prefix):
            return key
    return None


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src:
        xs = sorted(glob.glob(str(ROOT / "*.xlsx")))
        if not xs:
            sys.exit("No .xlsx given and none found in repo root.")
        src = xs[-1]
    print(f"Reading {src}")

    rows = list(openpyxl.load_workbook(src, read_only=True, data_only=True)[SHEET].iter_rows(values_only=True))
    name_cols = {i: v for i, v in enumerate(rows[0]) if v and i >= 2}
    players = list(name_cols.values())

    raw = DATA_JS.read_text(encoding="utf-8").strip()
    K = json.loads(raw[raw.index("=") + 1:].rstrip(";"))
    if K["players"] != players:
        sys.exit(f"Player list/order differs from data.js!\n sheet: {players}\n data : {K['players']}")
    by_key = {s["key"]: s for s in K["stages"]}

    # --- group-stage predictions (English) + points (row 1 = TOTAL) ---
    starts = [(r[0], idx) for idx, r in enumerate(rows) if isinstance(r[0], str) and len(r[0]) == 1 and r[0].isalpha()]
    preds, unknown = {p: {} for p in players}, set()
    for g, start in starts:
        for col, p in name_cols.items():
            order = []
            for k in range(4):
                pt = rows[start + k][col]
                en = PT2EN.get(pt)
                if en is None and pt is not None:
                    unknown.add(pt)
                order.append(en or pt)
            preds[p][g] = order
    if unknown:
        sys.exit(f"Unmapped team names (add to PT2EN): {sorted(unknown)}")
    K["groupPreds"] = preds
    K["groupOrder"] = [g for g, _ in starts]
    K["groupPoints"] = {p: rows[1][i] for i, p in name_cols.items()}

    # --- knockout picks per stage ---
    sections: dict[str, list[int]] = {}
    for idx, r in enumerate(rows):
        if isinstance(r[0], str):
            key = stage_for(r[0])
            if key:
                sections.setdefault(key, []).append(idx)

    stages_with_picks = []
    for key, idxs in sections.items():
        stage = by_key.get(key)
        if not stage:
            print(f"  ! sheet has stage '{key}' but data.js has no such stage — skipped")
            continue
        if len(idxs) != len(stage["matches"]):
            sys.exit(f"Stage {key}: sheet has {len(idxs)} match rows but data.js has {len(stage['matches'])} confrontos")
        picks, errors = {}, []
        for p in players:
            picks[p] = []
        for mi, row_idx in enumerate(idxs):
            m = stage["matches"][mi]
            for col, p in name_cols.items():
                v = rows[row_idx][col]
                if v is not None and v not in (m["a"], m["b"]):
                    errors.append(f"{key} match{mi+1}: {p} picked '{v}', not in ({m['a']}/{m['b']})")
                picks[p].append(v)
        if errors:
            sys.exit("Pick mismatches (fixtures in data.js wrong, or sheet order changed):\n" + "\n".join(errors))
        for mi, m in enumerate(stage["matches"]):
            backA = [p for p in players if picks[p][mi] == m["a"]]
            backB = [p for p in players if picks[p][mi] == m["b"]]
            m["backA"], m["backB"] = backA, backB
            m["tallyA"], m["tallyB"] = len(backA), len(backB)
        stage["picks"] = picks
        if any(any(v) for v in picks.values()):
            stages_with_picks.append(key)

    # active = the most advanced stage that has any picks
    order = [s["key"] for s in K["stages"]]
    latest = max(stages_with_picks, key=order.index) if stages_with_picks else None
    for s in K["stages"]:
        s["active"] = s["key"] == latest

    DATA_JS.write_text("window.KO=" + json.dumps(K, ensure_ascii=False) + ";\n", encoding="utf-8")
    pj = json.loads(PREDICTIONS.read_text(encoding="utf-8"))
    pj.update(players=players, groups=K["groupOrder"], predictions=preds)
    PREDICTIONS.write_text(json.dumps(pj, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Wrote {DATA_JS} and {PREDICTIONS}")
    print(f"  stages with picks: {stages_with_picks} · active = {latest}")
    for key in stages_with_picks:
        n = sum(1 for p in players if all(by_key[key]['picks'][p]))
        print(f"  {key}: {n}/{len(players)} apostadores completos")


if __name__ == "__main__":
    main()
