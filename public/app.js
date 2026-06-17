// Bolão da Copa — client-side scoring + rendering.
// Reads the static predictions.json (everyone's picks) and the standings.json
// (refreshed by the scheduled GitHub Action), scores each apostador (1 point per
// exact group position), and renders the leaderboard, a per-player breakdown,
// and the live group tables. No build step — plain ES module.

const POS = { 1: "1º", 2: "2º", 3: "3º", 4: "4º" };

async function load(path) {
  const res = await fetch(`${path}?t=${Date.now()}`); // cache-bust so updates show
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

// actualOrder[group] = [teamAtPos1, teamAtPos2, teamAtPos3, teamAtPos4]
function actualOrder(standings) {
  const out = {};
  for (const [g, table] of Object.entries(standings.groups || {})) {
    out[g] = [...table].sort((a, b) => a.position - b.position).map((t) => t.team);
  }
  return out;
}

function scorePlayer(picks, actual, groups) {
  let pts = 0;
  for (const g of groups) {
    const pred = picks[g] || [];
    const real = actual[g] || [];
    for (let i = 0; i < 4; i++) if (pred[i] && pred[i] === real[i]) pts++;
  }
  return pts;
}

function medal(rank) {
  return rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `${rank}º`;
}

function renderLeaderboard(rows, maxPts) {
  const el = document.getElementById("leaderboard");
  el.innerHTML = rows
    .map((r, i) => {
      const rank = i + 1;
      const lead = rank <= 3;
      return `
      <button type="button" data-player="${r.player}" title="Ver palpites de ${r.player}"
        class="flex w-full items-center gap-3 rounded-xl border ${lead ? "border-emerald-500/40 bg-emerald-500/5" : "border-slate-800 bg-slate-900"} px-4 py-3 text-left transition hover:border-emerald-400 hover:bg-emerald-500/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500">
        <span class="w-8 shrink-0 text-center font-display text-lg font-extrabold ${lead ? "" : "text-slate-400"}">${medal(rank)}</span>
        <span class="flex-1 truncate font-medium">${r.player}</span>
        <span class="font-display text-lg font-extrabold tabular-nums text-emerald-400">${r.points}</span>
        <span class="text-xs text-slate-500">/ ${maxPts}</span>
      </button>`;
    })
    .join("");
}

function renderPlayerDetail(player, picks, actual, groups) {
  const el = document.getElementById("player-detail");
  el.innerHTML = groups
    .map((g) => {
      const pred = picks[g] || [];
      const real = actual[g] || [];
      const rows = pred
        .map((team, i) => {
          const ok = team === real[i];
          return `
          <li class="flex items-center justify-between gap-2 py-0.5 text-sm">
            <span class="flex items-center gap-1.5 ${ok ? "text-emerald-300" : "text-slate-300"}">
              <span class="w-5 text-xs text-slate-500">${POS[i + 1]}</span>${team}
            </span>
            <span>${ok ? "✓" : "<span class='text-slate-600'>·</span>"}</span>
          </li>`;
        })
        .join("");
      const got = pred.reduce((n, t, i) => n + (t === real[i] ? 1 : 0), 0);
      return `
      <div class="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div class="mb-1 flex items-center justify-between">
          <h3 class="font-display text-sm font-bold uppercase tracking-wide text-slate-400">Grupo ${g}</h3>
          <span class="text-xs font-bold text-emerald-400">${got}/4</span>
        </div>
        <ul>${rows}</ul>
      </div>`;
    })
    .join("");
}

function renderGroups(standings) {
  const el = document.getElementById("groups");
  const entries = Object.entries(standings.groups || {}).sort((a, b) => a[0].localeCompare(b[0]));
  el.innerHTML = entries
    .map(([g, table]) => {
      const rows = [...table]
        .sort((a, b) => a.position - b.position)
        .map((t) => {
          const top2 = t.position <= 2;
          return `
          <tr class="${top2 ? "" : "text-slate-400"}">
            <td class="py-1 pr-2 text-center text-xs ${top2 ? "font-bold text-emerald-400" : "text-slate-500"}">${t.position}</td>
            <td class="py-1"><span class="flex items-center gap-2">${t.crest ? `<img src="${t.crest}" alt="" class="h-4 w-4 object-contain" loading="lazy">` : ""}<span class="truncate">${t.team}</span></span></td>
            <td class="py-1 text-center tabular-nums text-xs">${t.played ?? 0}</td>
            <td class="py-1 text-center tabular-nums text-xs">${fmtGD(t.goalDifference)}</td>
            <td class="py-1 text-right font-bold tabular-nums">${t.points ?? 0}</td>
          </tr>`;
        })
        .join("");
      return `
      <div class="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h3 class="mb-2 font-display text-sm font-bold uppercase tracking-wide">Grupo ${g}</h3>
        <table class="w-full text-sm">
          <thead><tr class="text-[0.65rem] uppercase tracking-wide text-slate-500">
            <th class="pb-1"></th><th class="pb-1 text-left">Time</th><th class="pb-1">J</th><th class="pb-1">SG</th><th class="pb-1 text-right">P</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
    })
    .join("");
}

function fmtGD(v) {
  if (v == null) return "0";
  return v > 0 ? `+${v}` : `${v}`;
}

async function main() {
  let predictions, standings;
  try {
    [predictions, standings] = await Promise.all([load("./predictions.json"), load("./standings.json")]);
  } catch (e) {
    document.getElementById("leaderboard").innerHTML =
      `<p class="text-sm text-rose-400">Não foi possível carregar os dados (${e.message}).</p>`;
    return;
  }

  document.getElementById("updated").textContent = standings.updated
    ? new Date(standings.updated).toLocaleString("pt-BR")
    : "—";
  if (standings.season) document.getElementById("season").textContent = standings.season;

  const groups = predictions.groups;
  const actual = actualOrder(standings);
  const maxPts = groups.length * 4;

  const ranking = predictions.players
    .map((p) => ({ player: p, points: scorePlayer(predictions.predictions[p], actual, groups) }))
    .sort((a, b) => b.points - a.points || a.player.localeCompare(b.player));
  renderLeaderboard(ranking, maxPts);

  // player selector — default to the current leader
  const sel = document.getElementById("player-select");
  sel.innerHTML = predictions.players
    .slice()
    .sort((a, b) => a.localeCompare(b))
    .map((p) => `<option value="${p}">${p}</option>`)
    .join("");
  sel.value = ranking[0].player;
  const draw = () => renderPlayerDetail(sel.value, predictions.predictions[sel.value], actual, groups);
  sel.addEventListener("change", draw);
  draw();

  // Click a name in the leaderboard → select that player and scroll to palpites.
  document.getElementById("leaderboard").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-player]");
    if (!btn) return;
    sel.value = btn.dataset.player;
    draw();
    document.getElementById("palpites").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  renderGroups(standings);
}

main();
