#!/usr/bin/env bash
# Bolão auto-update: fetch knockout results, push to the live site only when a
# real result changed, and print NEXT_MINUTES — when the watcher should check
# again (sooner around match end-times, longer when nothing is imminent).
#
# Used by the self-rescheduling watcher (see send_later chain). Safe to run any
# time; it only commits/pushes when secondstage/data.js actually changed.
set -euo pipefail
cd /opt/bolao-da-copa
set -a; . ./.env; set +a

python3 scripts/fetch_knockout.py 2>&1 | sed 's/^/  /'

if ! git diff --quiet -- secondstage/data.js; then
  git add secondstage/data.js public/knockout_results.json
  git commit -q -m "auto: knockout results update [skip-watch]" \
    -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
  git push -q origin main
  echo "PUSHED=yes"
else
  git checkout -- public/knockout_results.json 2>/dev/null || true  # drop timestamp-only churn
  echo "PUSHED=no"
fi

# Decide when to look again, based on kickoff times + statuses.
python3 - <<'PY'
import json, datetime as dt
now = dt.datetime.now(dt.timezone.utc)
res = json.load(open("public/knockout_results.json"))["results"]
def ko(r):
    try: return dt.datetime.fromisoformat(r["utcDate"].replace("Z", "+00:00"))
    except Exception: return None

live = any(r["status"] in ("IN_PLAY", "PAUSED") for r in res)
pend = [ko(r) for r in res if r["status"] not in ("FINISHED",) and ko(r)]
# a match can run ~105min (reg) up to ~180min (ET+pens+API lag) after kickoff
in_window = any(k <= now <= k + dt.timedelta(minutes=180) for k in pend)

if live or in_window:
    mins = 12                      # a result is imminent — check soon
else:
    ends = [k + dt.timedelta(minutes=105) for k in pend if k + dt.timedelta(minutes=105) > now]
    if ends:
        mins = max(2, int((min(ends) - now).total_seconds() // 60))
    else:
        mins = 180                 # nothing upcoming — long idle check
mins = min(mins, 240)              # never sleep more than 4h
print(f"NEXT_MINUTES={mins}")
PY
