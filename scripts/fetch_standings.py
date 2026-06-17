"""Fetch current FIFA World Cup group standings into public/standings.json.

Run by the GitHub Action on a schedule. The football-data.org API token is read
from the FOOTBALL_DATA_TOKEN environment variable (a repo Actions secret) — it is
never committed. Only the trimmed standings we display are written out.

Usage:  FOOTBALL_DATA_TOKEN=xxxx python scripts/fetch_standings.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://api.football-data.org/v4/competitions/WC/standings"
OUT = Path(__file__).resolve().parent.parent / "public" / "standings.json"


def main() -> None:
    token = os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        sys.exit("FOOTBALL_DATA_TOKEN is not set")

    req = urllib.request.Request(URL, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    groups = {}
    for block in data.get("standings", []):
        label = (block.get("group") or "").replace("Group ", "").strip()
        if not label:
            continue
        groups[label] = [
            {
                "position": t.get("position"),
                "team": t["team"]["name"],
                "crest": t["team"].get("crest"),
                "played": t.get("playedGames"),
                "won": t.get("won"),
                "draw": t.get("draw"),
                "lost": t.get("lost"),
                "points": t.get("points"),
                "goalsFor": t.get("goalsFor"),
                "goalsAgainst": t.get("goalsAgainst"),
                "goalDifference": t.get("goalDifference"),
            }
            for t in block.get("table", [])
        ]

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "season": (data.get("season") or {}).get("startDate", "")[:4],
        "groups": groups,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUT} — {len(groups)} groups, updated {payload['updated']}")


if __name__ == "__main__":
    main()
