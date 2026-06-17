"""Regenerate public/predictions.json from the Bolão Excel sheet.

The sheet (`Bolão da Copa.xlsx`, sheet `PontuaçãoPorJogo`) has one column per
apostador; groups are 4-row blocks (A–L); the order a player lists the four
teams is their predicted finishing order (1st→4th). Names are in Portuguese, so
they're mapped to the English names the football-data.org API uses.

Usage:  python scripts/build_predictions.py "/path/to/Bolão da Copa.xlsx"

Run this only when the predictions change; the output is committed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl

OUT = Path(__file__).resolve().parent.parent / "public" / "predictions.json"

# Portuguese (sheet) -> English (API) nation names, for the 2026 groups.
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


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "Bolão da Copa.xlsx"
    rows = list(openpyxl.load_workbook(src, read_only=True, data_only=True)["PontuaçãoPorJogo"].iter_rows(values_only=True))
    name_cols = {i: v for i, v in enumerate(rows[0]) if v and i >= 2}
    starts = [(r[0], idx) for idx, r in enumerate(rows) if r[0] and isinstance(r[0], str) and len(r[0]) == 1 and r[0].isalpha()]

    players = list(name_cols.values())
    predictions = {p: {} for p in players}
    unknown = set()
    for g, start in starts:
        for col, player in name_cols.items():
            order = []
            for k in range(4):
                pt = rows[start + k][col]
                en = PT2EN.get(pt)
                if en is None:
                    unknown.add(pt)
                order.append(en or pt)
            predictions[player][g] = order

    if unknown:
        sys.exit(f"Unmapped team names (add to PT2EN): {sorted(unknown)}")

    out = {
        "players": players,
        "groups": [g for g, _ in starts],
        "scoring": "1 point per exact group position",
        "predictions": predictions,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUT} — {len(players)} players, {len(starts)} groups")


if __name__ == "__main__":
    main()
