#!/usr/bin/env bash
# Long-running bolão watcher. Repeatedly runs auto_update.sh, sleeping for the
# NEXT_MINUTES it reports (short near match end-times, long when idle), and
# pushes the live site the moment a result changes. Runs for ~22h then exits so
# the parent can re-arm it (a heartbeat); the GitHub schedule remains a backstop.
cd /opt/bolao-da-copa
deadline=$(( $(date +%s) + 22*3600 ))

while [ "$(date +%s)" -lt "$deadline" ]; do
  ts=$(date -u +%H:%M)
  out=$(bash scripts/auto_update.sh 2>&1) || out="auto_update error: $out"
  mins=$(printf '%s\n' "$out" | grep -o 'NEXT_MINUTES=[0-9]*' | cut -d= -f2)
  pushed=$(printf '%s\n' "$out" | grep -o 'PUSHED=[a-z]*' | cut -d= -f2)
  [ -z "$mins" ] && mins=30
  echo "[$ts UTC] pushed=${pushed:-?} next=${mins}min"
  printf '%s\n' "$out" | grep -E 'Wrote|Applied|error' | sed 's/^/    /'
  sleep $(( mins * 60 ))
done
echo "WATCH_LOOP_DONE $(date -u +%H:%M)"
