// Modo luto — Brasil eliminado da Copa (05/07/2026).
// PRETO_E_BRANCO deixa o site inteiro em preto e branco até ser desligado.
// A chuva com relâmpagos toca por 10s, uma vez por sessão do navegador.
// Para voltar ao normal: PRETO_E_BRANCO = false (ou apague este arquivo e as
// tags <script src="./luto.js"> das páginas).
(() => {
  const PRETO_E_BRANCO = true;
  const CHUVA = true;
  const CHUVA_MS = 10000;
  const UMA_VEZ_POR_SESSAO = true;
  const MUSICA = true; // Farewell My Lovely (tema triste do Chaves), ./luto.mp3, ~10s com fade

  const Z = 2147483000; // acima de tudo, abaixo do painel do diag.js? não importa: pointer-events none

  function onReady(fn) {
    if (document.body) fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  // ---- preto e branco (overlay com backdrop-filter: não mexe em layout nem
  // em elementos position:fixed, ao contrário de filter no <html>) ----
  if (PRETO_E_BRANCO) {
    onReady(() => {
      const bw = document.createElement("div");
      bw.style.cssText = `position:fixed;inset:0;z-index:${Z};pointer-events:none;` +
        "backdrop-filter:grayscale(1);-webkit-backdrop-filter:grayscale(1)";
      document.body.appendChild(bw);
    });
  }

  // ---- chuva + relâmpagos por 10 segundos ----
  if (!CHUVA) return;
  // ?luto na URL força a chuva+música de novo (para testar/demonstrar)
  const FORCAR = new URLSearchParams(location.search).has("luto");
  if (UMA_VEZ_POR_SESSAO && !FORCAR) {
    try {
      if (sessionStorage.getItem("luto_chuva")) return;
      sessionStorage.setItem("luto_chuva", "1");
    } catch (e) { /* sessionStorage bloqueado: mostra sempre */ }
  }

  onReady(() => {
    // música triste: navegadores bloqueiam áudio automático sem interação;
    // tenta tocar já e, se bloquear, toca no primeiro toque/clique/tecla.
    if (MUSICA) {
      const audio = new Audio("./luto.mp3");
      audio.volume = 1.0;
      // No celular só o FIM do gesto (pointerup/touchend/click) concede
      // permissão de som — pointerdown/touchstart NÃO contam. Tenta em cada
      // gesto até conseguir; play() em áudio já tocando é inofensivo.
      const EVS = ["pointerup", "touchend", "keydown", "click"];
      const tentar = () => {
        audio.play().then(() => {
          EVS.forEach((ev) => removeEventListener(ev, tentar, true));
        }).catch(() => {});
      };
      EVS.forEach((ev) => addEventListener(ev, tentar, true));
      tentar();
    }

    const canvas = document.createElement("canvas");
    canvas.style.cssText = `position:fixed;inset:0;z-index:${Z + 1};pointer-events:none;transition:opacity .9s`;
    document.body.appendChild(canvas);

    const flash = document.createElement("div");
    flash.style.cssText = `position:fixed;inset:0;z-index:${Z + 2};pointer-events:none;` +
      "background:radial-gradient(ellipse at 50% -20%,rgba(255,255,255,.95),rgba(220,230,255,.55) 45%,rgba(180,200,255,.2) 75%);" +
      "opacity:0;transition:opacity .12s ease-out";
    document.body.appendChild(flash);

    const ctx = canvas.getContext("2d");
    let W, H;
    const resize = () => {
      W = canvas.width = innerWidth;
      H = canvas.height = innerHeight;
    };
    resize();
    addEventListener("resize", resize);

    const N = Math.min(260, Math.floor(innerWidth / 5));
    const drops = Array.from({ length: N }, () => ({
      x: Math.random() * innerWidth,
      y: Math.random() * innerHeight,
      len: 12 + Math.random() * 18,
      speed: 9 + Math.random() * 9,
      drift: 1.2 + Math.random() * 1.4, // vento leve
      alpha: 0.25 + Math.random() * 0.45,
    }));

    let running = true;
    function frame() {
      if (!running) return;
      ctx.clearRect(0, 0, W, H);
      ctx.lineWidth = 1.2;
      ctx.lineCap = "round";
      for (const d of drops) {
        ctx.strokeStyle = `rgba(200,215,235,${d.alpha})`;
        ctx.beginPath();
        ctx.moveTo(d.x, d.y);
        ctx.lineTo(d.x - d.drift * 2.2, d.y - d.len);
        ctx.stroke();
        d.x += d.drift;
        d.y += d.speed;
        if (d.y > H + d.len) {
          d.y = -d.len - Math.random() * 40;
          d.x = Math.random() * (W + 60) - 30;
        }
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);

    // relâmpago: 2-3 tremeluzidas rápidas
    function relampago() {
      const flick = (times) => {
        if (!times) return;
        flash.style.opacity = (0.55 + Math.random() * 0.4).toFixed(2);
        setTimeout(() => {
          flash.style.opacity = "0";
          setTimeout(() => flick(times - 1), 60 + Math.random() * 120);
        }, 70 + Math.random() * 90);
      };
      flick(2 + Math.floor(Math.random() * 2));
    }
    [900, 3600, 6800, 8900].forEach((t) => setTimeout(relampago, t + Math.random() * 400));

    setTimeout(() => {
      canvas.style.opacity = "0";
      setTimeout(() => {
        running = false;
        canvas.remove();
        flash.remove();
        removeEventListener("resize", resize);
      }, 1000);
    }, CHUVA_MS);
  });
})();
