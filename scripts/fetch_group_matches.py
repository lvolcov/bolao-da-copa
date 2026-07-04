"""Fetch every finished World Cup group-stage match into secondstage/group_matches.json.

The knockout stages already replay match-by-match in the "Evolução" chart
(secondstage/evolucao.html), computed client-side from data.js. The group stage
needs the same thing, but data.js only ever stores the *final* group tables
(groupActual/groupPreds) — there's no per-matchday history. This script pulls
the raw group-stage fixtures (team names, scores, kickoff) from football-data.org
so evolucao.html can replay them client-side: rebuild each group's table after
every match and re-rank it (points, then head-to-head among tied teams, then
goal difference, then goals scored, then alphabetical — the standard tie-break),
which is exactly how the World Cup's own regs resolve ties.

Team names here are in English, matching groupPreds/groupActual in data.js (the
group stage never went through the PT2EN mapping the knockout stage uses).

Usage:  FOOTBALL_DATA_TOKEN=xxxx python3 scripts/fetch_group_matches.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "secondstage" / "group_matches.json"
URL = "https://api.football-data.org/v4/competitions/WC/matches"


def main() -> None:
    token = os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        sys.exit("FOOTBALL_DATA_TOKEN is not set")
    req = urllib.request.Request(URL, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    matches = []
    for m in data.get("matches", []):
        if m.get("stage") != "GROUP_STAGE" or m.get("status") != "FINISHED":
            continue
        ft = (m.get("score") or {}).get("fullTime") or {}
        if ft.get("home") is None or ft.get("away") is None:
            continue
        matches.append({
            "group": (m.get("group") or "").replace("GROUP_", ""),
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "hg": ft["home"],
            "ag": ft["away"],
            "utcDate": m.get("utcDate"),
        })
    matches.sort(key=lambda m: m["utcDate"])

    OUT.write_text(json.dumps(matches, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} — {len(matches)} finished group matches")


if __name__ == "__main__":
    main()
