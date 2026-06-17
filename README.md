# 🐝⚽ Bolão da Copa 2026

A tiny, self-contained site for the Pelada MCR World Cup prediction pool. Each
participant predicted the finishing order of every group; the site fetches the
**live group standings** and scores everyone — **1 point per exact group
position** (max 48: 12 groups × 4 places).

It's deliberately decoupled from the main [Pelada MCR Stats](https://lvolcov.github.io/pelada-mcr-stats/)
site — its own repo, its own GitHub Pages deploy.

**Stack:** plain HTML + Tailwind (CDN) + a vanilla JS module. Standings come from
[football-data.org](https://www.football-data.org/) via a scheduled GitHub Action.
No backend, no build step.

## How it works

```
GitHub Action (every 2h + on push)
  └─ scripts/fetch_standings.py  →  public/standings.json   (uses the API secret)
public/ (deployed to Pages)
  ├─ index.html · app.js          scores predictions vs standings in the browser
  ├─ predictions.json             everyone's picks (static, from the Excel sheet)
  └─ standings.json               live group tables (refreshed by the Action)
```

## One-time setup

1. **Create a GitHub repo** (e.g. `bolao-da-copa`) and push this folder to `main`.
2. **Add the API token** as a secret: repo → *Settings → Secrets and variables →
   Actions → New repository secret* → name `FOOTBALL_DATA_TOKEN`, value = your
   football-data.org token. (Never commit the token.)
3. **Enable Pages**: repo → *Settings → Pages → Build and deployment → GitHub
   Actions*.
4. Done — the Action deploys on push and refreshes the standings every 2 hours.
   Trigger a run anytime from the *Actions* tab (*Run workflow*).

## Updating the predictions

The picks are static. If the sheet changes, regenerate the JSON:

```bash
pip install openpyxl
python scripts/build_predictions.py "/path/to/Bolão da Copa.xlsx"
```

(The script maps the Portuguese nation names to the API's English names and
fails loudly if it meets an unmapped team.)

## Local preview

```bash
cd public
python -m http.server 8130   # then open http://localhost:8130
```

To refresh standings locally: `FOOTBALL_DATA_TOKEN=xxx python scripts/fetch_standings.py`.

> Standings are **provisional** while the group stage is in progress — the table
> order (and therefore the points) updates as matches are played.
