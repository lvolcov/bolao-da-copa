// Diagnóstico visível: se algo quebrar (JS ou um arquivo que não carregou), mostra
// um aviso vermelho na tela em vez de deixar a página em branco sem pista nenhuma.
// Carregado como o PRIMEIRO script de cada página, antes de tudo mais.
(function () {
  var pending = [];
  function flush() {
    if (!document.body) return;
    while (pending.length) {
      var msg = pending.shift();
      var el = document.createElement("div");
      el.style.cssText = "position:fixed;left:8px;right:8px;bottom:8px;z-index:99999;background:#7f1d1d;color:#fff;padding:10px 14px;border-radius:12px;font:12px/1.4 monospace;white-space:pre-wrap;max-height:40vh;overflow:auto;box-shadow:0 4px 20px rgba(0,0,0,.5)";
      el.textContent = msg;
      document.body.appendChild(el);
    }
  }
  function show(msg) { pending.push(msg); flush(); }
  window.addEventListener("error", function (e) {
    if (e.target && e.target !== window && e.target.tagName) {
      show("Falha ao carregar: " + e.target.tagName + " " + (e.target.src || e.target.href || ""));
    } else {
      show("Erro JS: " + (e.message || e.type) + "\n" + (e.filename || "") + ":" + (e.lineno || "") + ":" + (e.colno || ""));
    }
  }, true);
  window.addEventListener("unhandledrejection", function (e) {
    show("Promise rejeitada: " + (e.reason && e.reason.message ? e.reason.message : e.reason));
  });
  document.addEventListener("DOMContentLoaded", flush);
})();
