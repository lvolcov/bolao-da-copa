"""Fetch World Cup knockout results and apply the winners to the Bolão data.

Two things happen:
  1. Pull every knockout match from football-data.org (/competitions/WC/matches),
     resolve the winner of each finished tie (incl. extra time / penalties), map
     the English club names to the Portuguese names the bolão uses, and write
     public/knockout_results.json.
  2. Patch the second-stage data file (secondstage/data.js): for each finished
     match, find the matching confronto by team pair and set its `winner`, so the
     scoring (the stage's weight per acerto — see STAGE_WEIGHTS) and the result UI
     light up automatically.

The token is read from FOOTBALL_DATA_TOKEN (a repo Actions secret) — never
committed. Run with --no-apply to only refresh the JSON without touching data.js.

Usage:  FOOTBALL_DATA_TOKEN=xxxx python scripts/fetch_knockout.py [--no-apply]
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "public" / "knockout_results.json"
DATA_JS = ROOT / "secondstage" / "data.js"
URL = "https://api.football-data.org/v4/competitions/WC/matches"

# Points per correct pick per stage (the pool's rules) — must match
# build_data.STAGE_WEIGHTS. Re-applied on every run so the live site is self-healing.
STAGE_WEIGHTS = {"r32": 2, "r16": 3, "qf": 4, "sf": 5, "final": 10}

# API stage code -> our stage key in data.js
STAGE_MAP = {
    "LAST_32": "r32",
    "LAST_16": "r16",
    "QUARTER_FINALS": "qf",
    "SEMI_FINALS": "sf",
    "FINAL": "final",
}

# English (API) -> Portuguese (bolão). Mirror of build_predictions.PT2EN, inverted.
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
EN2PT = {en: pt for pt, en in PT2EN.items()}


def to_pt(name: str | None) -> str | None:
    if not name:
        return None
    return EN2PT.get(name, name)  # fall back to the raw name if unmapped


def resolve_winner(home: str, away: str, score: dict) -> str | None:
    """Return the advancing club (English name) for a finished tie, or None.

    After a shootout the API often leaves `winner` null and `penalties` tied at
    the 5-round score (e.g. 5-5 before sudden death). `fullTime` carries the
    decisive aggregate (incl. the shootout), so it's the most reliable signal.
    """
    w = score.get("winner")
    if w == "HOME_TEAM":
        return home
    if w == "AWAY_TEAM":
        return away
    for key in ("fullTime", "penalties"):  # fullTime first — it includes the shootout
        d = score.get(key) or {}
        h, a = d.get("home"), d.get("away")
        if h is not None and a is not None and h != a:
            return home if h > a else away
    return None


def fetch() -> dict:
    token = os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        sys.exit("FOOTBALL_DATA_TOKEN is not set")
    req = urllib.request.Request(URL, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)

    out = []
    for m in data.get("matches", []):
        stage = STAGE_MAP.get(m.get("stage"))
        if not stage:
            continue  # group stage / third place — ignored
        home = (m.get("homeTeam") or {}).get("name")
        away = (m.get("awayTeam") or {}).get("name")
        if not home or not away:
            continue  # fixture not drawn yet
        score = m.get("score") or {}
        finished = m.get("status") == "FINISHED"
        winner_en = resolve_winner(home, away, score) if finished else None
        ft = score.get("fullTime") or {}
        reg = score.get("regularTime") or {}
        pens = score.get("penalties") or {}
        shootout = score.get("duration") == "PENALTY_SHOOTOUT"
        # match score = the football result (regulation/ET tie); fall back to fullTime
        base = reg if reg.get("home") is not None else ft
        score_str = f"{base.get('home')}-{base.get('away')}" if base.get("home") is not None else None
        # shootout score: prefer a decided penalties field, else the fullTime aggregate
        pen_str = None
        if shootout:
            if pens.get("home") is not None and pens.get("home") != pens.get("away"):
                pen_str = f"{pens.get('home')}-{pens.get('away')}"
            elif ft.get("home") is not None:
                pen_str = f"{ft.get('home')}-{ft.get('away')}"
        out.append({
            "stage": stage,
            "home": to_pt(home), "away": to_pt(away),
            "homeEn": home, "awayEn": away,
            "status": m.get("status"),
            "winner": to_pt(winner_en),
            "score": score_str,
            "pen": pen_str,
            "duration": score.get("duration"),
            "utcDate": m.get("utcDate"),
        })

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "results": out,
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    decided = sum(1 for r in out if r["winner"])
    print(f"Wrote {RESULTS} — {len(out)} knockout matches, {decided} decided")
    return payload


def apply(payload: dict) -> None:
    """Set winners on matching confrontos in secondstage/data.js (by team pair)."""
    raw = DATA_JS.read_text(encoding="utf-8").strip()
    K = json.loads(raw[raw.index("=") + 1:].rstrip(";"))
    by_key = {s["key"]: s for s in K["stages"]}
    for s in K["stages"]:
        s["weight"] = STAGE_WEIGHTS[s["key"]]

    applied = 0
    for r in payload["results"]:
        stage = by_key.get(r["stage"])
        if not stage:
            continue
        pair = {r["home"], r["away"]}
        for m in stage["matches"]:
            if {m["a"], m["b"]} != pair:
                continue
            # kickoff time (used by the pages to sort matches chronologically)
            if r.get("utcDate"):
                m["date"] = r["utcDate"]
            if r["winner"]:
                flip = r["away"] == m["a"]  # API fixture orientation reversed vs ours

                def orient(s):  # store scores from team A's perspective (UI reads them)
                    if s and flip:
                        h, a = s.split("-"); return f"{a}-{h}"
                    return s
                score, pen = orient(r["score"]), orient(r.get("pen"))
                if m.get("winner") != r["winner"] or m.get("score") != score or m.get("pen") != pen:
                    m["winner"] = r["winner"]
                    m["score"] = score
                    m["pen"] = pen
                    applied += 1
            break

    DATA_JS.write_text("window.KO=" + json.dumps(K, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"Applied {applied} winner(s) to {DATA_JS}")


def main() -> None:
    payload = fetch()
    if "--no-apply" not in sys.argv:
        apply(payload)


if __name__ == "__main__":
    main()
