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
  ├─ fetch_standings.py           pulls WC group standings (Action + local)
  ├─ fetch_knockout.py            pulls knockout results + winners (Action + local)
  ├─ build_predictions.py         regenerates predictions.json from the .xlsx
  └─ build_data.py                regenerates secondstage/data.js from the .xlsx
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

## Second stage — knockout (mata-mata)

Once the group stage ends, the pool moves to the knockouts: each apostador picks
the winner of every tie, with **progressive points per correct pick** — 16-avos
+2, oitavas +3, quartas +4, semi +5, final (campeão) +10. The canonical weights
live in `STAGE_WEIGHTS` (in `build_data.py` and `fetch_knockout.py`, which
re-apply them to `data.js` on every run) and each stage's `weight` in `data.js`
drives all scoring and UI text. This lives under
`secondstage/` and is **the live GitHub Pages site** — the Action deploys this
folder, so the homepage opens straight on the Classificação. (The old group-stage
site stays in `public/` for reference but is no longer deployed.) It's also mirrored
on the home server's internal door for staging.

```
secondstage/            (LIVE site → github pages + internal door http://192.168.1.107:8137)
  ├─ data.js            window.KO = ALL the data (see below). The single source of truth.
  ├─ common.js          shared nav + scoring helper (group pts + weight × acertos)
  ├─ index.html         🏆 Classificação Geral — leaderboard + per-round breakdown
  ├─ confrontos.html    ⚔️ match cards w/ consensus bars (only stages with picks)
  ├─ matriz.html        🧮 matches × apostadores grid
  ├─ chaveamento.html   🗺️ bracket: real votes for the live round, projection ahead
  └─ grupos.html        📋 final group tables + each player's group-stage palpites
```

### The data model (`secondstage/data.js`)

One object, `window.KO`, holds everything:

- `players` — the 15 apostadores (order is canonical; the build scripts assert it).
- `groupPoints` — group-stage points per player (from the sheet's TOTAL row).
- `groupPreds` / `groupOrder` / `groupActual` / `teamMeta` — group palpites (English
  names), final/partial group order, and an English→{pt,crest} lookup.
- `groups` — the 12 final group tables (from `standings.json`).
- `crests` — Portuguese team name → crest URL.
- `stages` — the knockout rounds in order: `r32` (16-avos), `r16` (oitavas), `qf`,
  `sf`, `final`. Each stage has:
  - `key`, `label`, `full`, `weight` (points per acerto: r32 2, r16 3, qf 4,
    sf 5, final 10), `active` (the round being featured),
  - `matches` — the **fixtures**: `{a, b, crestA, crestB, tallyA, tallyB, backA,
    backB, winner, score}`. `winner`/`score` are filled by `fetch_knockout.py`;
    the tallies/backs are computed by `build_data.py` from everyone's picks.
  - `picks` — `{player: [pick per match]}`.

Scoring (in `common.js`) = `groupPoints` + Σ over stages of `weight × (picks that
match the match winner)`. It updates automatically as winners land.

### Serving the internal preview

A throwaway service in `/opt/docker-compose.yaml` serves the folder:

```bash
cd /opt && docker compose up -d bolao-2fase-preview   # → http://192.168.1.107:8137
```

(It bind-mounts `secondstage/` read-only and runs `python -m http.server 8137`, so
edits to the files show on the next refresh — no rebuild.)

### Live knockout results

`scripts/fetch_knockout.py` pulls `/competitions/WC/matches`, keeps the knockout
stages (API codes `LAST_32→r32`, `LAST_16→r16`, `QUARTER_FINALS→qf`,
`SEMI_FINALS→sf`, `FINAL→final`), resolves each finished tie's winner (extra
time / penalties handled, with a penalty-score fallback), maps names to Portuguese,
and **sets `winner`+`score`** on the matching confronto in `data.js`. The Action
runs it for real on every deploy (so the live site auto-scores as matches finish);
to update the internal door immediately, run it on the server:

```bash
cd /opt/bolao-da-copa && set -a && . ./.env && set +a && python3 scripts/fetch_knockout.py
```

(The API token lives in `/opt/bolao-da-copa/.env` — git-ignored. `.env` has
`FOOTBALL_DATA_TOKEN=…`.)

### ✅ Updating for the next stage (oitavas → final)

When a round finishes and the next one opens, do this in order:

1. **Score the round that just ended** — run `fetch_knockout.py` (command above).
   The leaderboard and result UI update automatically.
2. **Set the next stage's real fixtures in `data.js`.** Until a round is drawn its
   `matches` are a *projection* (favorites paired). Replace that stage's `matches`
   with the real 8/4/2/1 confrontos — `knockout_results.json` lists the drawn
   fixtures (home/away). Set `a`, `b`, `crestA`, `crestB` (crests come from
   `K.crests` / `teamMeta`); leave `tally*`/`back*`/`winner` empty.
3. **Load the new picks.** Via Google Forms (preferred since the oitavas): export
   the responses sheet as CSV and run
   ```bash
   cd /opt/bolao-da-copa && python3 scripts/import_form.py respostas_<fase>.csv
   ```
   (`scripts/create_form_oitavas.gs` is the template for creating the form; keep
   the "Jogo N: A × B" title format — the importer parses it and auto-detects the
   stage. The CSV is git-ignored: it contains emails.) Or, via the old Excel
   sheet: drop it in the repo root and run:
   ```bash
   cd /opt/bolao-da-copa && python3 scripts/build_data.py
   ```
   It reads the sheet, fills that stage's `picks`, recomputes the tallies/who-voted,
   refreshes the group data, and flips `active` to the most advanced stage with
   picks. It **fails loudly** if a pick isn't one of the two fixture teams (means
   the fixtures in step 2 are wrong or the sheet's match order changed) — and if the
   sheet labels the new block differently, add its prefix to `SECTION_MAP` in the
   script (e.g. the round-of-32 block is labelled `"Round 16"`).
4. **Refresh the door** (just reload — the preview reads the files live) and review.
5. **Run the tests** — they assert the stage weights (2/3/4/5/10), match counts and
   that no page hardcodes the old flat +2:
   ```bash
   cd /opt/bolao-da-copa && python3 -m unittest discover -s tests
   ```
6. When happy, delete the `.xlsx` from the repo root (the data now lives in `data.js`).

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
