// Shared helpers for the Bolão da Copa pages (nav, scoring, crests).
window.BOLAO = (() => {
  const K = window.KO;
  const NAV = [
    ["index", "🏆 Classificação"],
    ["confrontos", "⚔️ Confrontos"],
    ["matriz", "🧮 Matriz"],
    ["chaveamento", "🗺️ Chaveamento"],
    ["grupos", "📋 Grupos"],
  ];

  const PELADA_URL = "https://lvolcov.github.io/pelada-mcr-stats/";

  function renderNav(id) {
    const here = location.pathname.split("/").pop().replace(".html", "") || "index";
    const tabs = NAV.map(([f, n]) => {
      const me = (f === "index" ? ["index", ""] : [f]).includes(here);
      return `<a href="./${f}.html" class="rounded-full border px-3 py-1.5 ${me ? "border-emerald-400 bg-emerald-500/10 text-emerald-300" : "border-slate-700 text-slate-400 hover:border-slate-500"}">${n}</a>`;
    }).join("");
    const back = `<a href="${PELADA_URL}" class="group mb-1 flex w-full items-center gap-2 text-sm font-semibold text-slate-400 transition hover:text-sky-300">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 shrink-0 transition group-hover:-translate-x-1"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        <span>Pelada MCR Stats</span>
      </a>`;
    document.getElementById(id).innerHTML = back + tabs;
  }

  const crest = (c, cls = "h-5 w-5") => c ? `<img src="${c}" class="${cls} shrink-0 object-contain" loading="lazy">` : `<span class="${cls} shrink-0"></span>`;
  const crestOf = (team) => K.crests[team] || "";
  const favorite = (m) => (m.tallyA >= m.tallyB ? m.a : m.b);

  // points per player: group stage (authoritative) + each knockout stage (weight × correct).
  function score() {
    return K.players.map((p) => {
      const group = K.groupPoints[p] ?? 0;
      const byStage = {};
      let koTotal = 0;
      for (const s of K.stages) {
        const picks = s.picks[p] || [];
        let correct = 0;
        s.matches.forEach((m, i) => {
          if (m.winner && picks[i] === m.winner) correct++;
        });
        const pts = correct * s.weight;
        byStage[s.key] = pts;
        koTotal += pts;
      }
      const submitted = {};
      for (const s of K.stages) submitted[s.key] = (s.picks[p] || []).some(Boolean);
      return { player: p, group, byStage, total: group + koTotal, submitted };
    }).sort((a, b) => b.total - a.total || a.player.localeCompare(b.player));
  }

  return { K, NAV, renderNav, crest, crestOf, favorite, score };
})();
