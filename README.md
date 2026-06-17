# 🏆⚽ Bolão da Copa 2026

A tiny, self-contained site for the Pelada MCR World Cup prediction pool. Each
participant predicted the finishing order of every group; the site fetches the
**live group standings** and scores everyone — **1 point per exact group
position** (max 48: 12 groups × 4 places).

It's deliberately decoupled from the main
[Pelada MCR Stats](https://lvolcov.github.io/pelada-mcr-stats/) site — its own
repo, its own GitHub Pages deploy — and the two link to each other.

**Live:** https://lvolcov.github.io/bolao-da-copa/

**Stack:** plain HTML + Tailwind (CDN) + a vanilla JS module — no backend, no
build step. Standings come from [football-data.org](https://www.football-data.org/)
via a scheduled GitHub Action.

## Features

- **Leaderboard** of apostadores, ranked by points (1 per exact group position).
- **Click any name** → jumps to "Palpites de" with that player selected, showing
  their pick vs the live table for each group (✓ when the position matches).
- **Live group tables** (A–L) with crests, refreshed automatically.
- **Installable (PWA)** — gold-trophy icon + web manifest, so it can be added to a
  phone home screen as "Bolão da Copa".
- **Back link** to the Pelada MCR Stats site (and that site links here).
- Mobile-first; works in the dark theme throughout.

## How it works

```
GitHub Action (every 20 min + on push)
  └─ scripts/fetch_standings.py  →  public/standings.json   (uses the API secret)

public/ (deployed to GitHub Pages)
  ├─ index.html · app.js          scores predictions vs standings in the browser
  ├─ predictions.json             everyone's picks (static, from the Excel sheet)
  ├─ standings.json               live group tables (refreshed by the Action)
  ├─ manifest.webmanifest         PWA metadata
  └─ favicon.ico · *.png · logo   icons (favicon, apple-touch, 192/512)

scripts/
  ├─ fetch_standings.py           pulls WC standings (Action + local)
  └─ build_predictions.py         regenerates predictions.json from the .xlsx
```

Scoring runs entirely in the browser: `app.js` loads the static `predictions.json`
and the `standings.json` (kept current by the Action) and compares each player's
predicted order against the live table.

## One-time setup

The repo already exists at `lvolcov/bolao-da-copa`. To make it deploy:

1. **Add the API token** as a secret: repo → *Settings → Secrets and variables →
   Actions → New repository secret* → name `FOOTBALL_DATA_TOKEN`, value = your
   football-data.org token. (Never commit the token — the workflow reads it from
   this secret.)
2. **Enable Pages**: repo → *Settings → Pages → Build and deployment → Source =
   GitHub Actions*. (Pages must be enabled here — the workflow no longer tries to
   create it, since the automatic token isn't allowed to.)
3. **Run it**: *Actions* tab → *Deploy Bolão to GitHub Pages* → *Run workflow*.

After that it redeploys on every push and **refreshes the standings every 20
minutes** (`cron: */20 * * * *`) — one API call per run, well within the free
tier's 10 req/min.

## Updating the predictions

The picks are static. If the sheet changes, regenerate the JSON:

```bash
pip install openpyxl
python scripts/build_predictions.py "/path/to/Bolão da Copa.xlsx"
git commit -am "update predictions" && git push
```

The sheet's `PontuaçãoPorJogo` tab has one column per apostador; each group is a
4-row block (A–L); the order a player lists the four teams is their predicted
finish (1st→4th). The script maps the Portuguese nation names to the English
names the API uses and **fails loudly** if it meets an unmapped team (add it to
`PT2EN` in the script).

## Local preview

```bash
cd public
python -m http.server 8130   # then open http://localhost:8130
```

To refresh standings locally: `FOOTBALL_DATA_TOKEN=xxx python scripts/fetch_standings.py`.

## Notes

- Standings are **provisional** while the group stage is in progress — the table
  order (and therefore the points) updates as matches are played.
- The bee/trophy icons live in `public/`; regenerate them only if rebranding.
