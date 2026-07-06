// Modo luto — Brasil eliminado da Copa (05/07/2026).
// PRETO_E_BRANCO deixa o site inteiro em preto e branco até ser desligado.
// A CHUVA é constante (faz parte do luto). A INTRO (relâmpagos + música
// Farewell My Lovely do Chaves, ./luto.mp3 ~10s) toca uma vez por sessão;
// ?luto na URL força a intro de novo (para testar/demonstrar).
// Para voltar ao normal: flags abaixo = false (ou apague este arquivo e as
// tags <script src="./luto.js"> das páginas).
(() => {
  const PRETO_E_BRANCO = true;
  const CHUVA = true;
  const INTRO = true;
  const MUSICA = true;
  const RELAMPAGOS = [900, 3600, 6800, 8900]; // instantes dos relâmpagos (ms)

  const Z = 2147483000; // acima de tudo; overlays têm pointer-events:none

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

  // intro (relâmpagos + música) uma vez por sessão; ?luto força
  let comIntro = INTRO;
  if (comIntro && !new URLSearchParams(location.search).has("luto")) {
    try {
      if (sessionStorage.getItem("luto_intro")) comIntro = false;
      else sessionStorage.setItem("luto_intro", "1");
    } catch (e) { /* sessionStorage bloqueado: intro sempre */ }
  }

  // ---- chuva constante ----
  if (CHUVA) onReady(() => {
    const canvas = document.createElement("canvas");
    canvas.style.cssText = `position:fixed;inset:0;z-index:${Z + 1};pointer-events:none`;
    document.body.appendChild(canvas);

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

    function frame() {
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
  });

  // ---- intro: relâmpagos + música ----
  if (comIntro) onReady(() => {
    const flash = document.createElement("div");
    flash.style.cssText = `position:fixed;inset:0;z-index:${Z + 2};pointer-events:none;` +
      "background:radial-gradient(ellipse at 50% -20%,rgba(255,255,255,.95),rgba(220,230,255,.55) 45%,rgba(180,200,255,.2) 75%);" +
      "opacity:0;transition:opacity .12s ease-out";
    document.body.appendChild(flash);

    function relampago() { // 2-3 tremeluzidas rápidas
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
    RELAMPAGOS.forEach((t) => setTimeout(relampago, t + Math.random() * 400));
    setTimeout(() => flash.remove(), Math.max(...RELAMPAGOS) + 3000);

    if (!MUSICA) return;
    const audio = new Audio("./luto.mp3");
    audio.volume = 1.0;

    // Navegadores só liberam som depois de um gesto — e no celular o gesto
    // válido é o FIM do toque (pointerup/touchend/click), não o início.
    // Tenta já, tenta a cada gesto e, se nada tocar, mostra um botão 🔊
    // (clique em botão é gesto garantido em qualquer navegador).
    const btn = document.createElement("button");
    btn.textContent = "🔊";
    btn.title = "Tocar a trilha do luto";
    btn.style.cssText = `position:fixed;right:16px;bottom:16px;z-index:${Z + 3};display:none;` +
      "font-size:24px;line-height:1;padding:12px 14px;border-radius:9999px;cursor:pointer;" +
      "border:1px solid #475569;background:rgba(15,23,42,.9);box-shadow:0 4px 20px rgba(0,0,0,.5)";
    document.body.appendChild(btn);

    const EVS = ["pointerup", "touchend", "keydown", "click"];
    const tentar = () => { audio.play().catch(() => {}); };
    audio.addEventListener("playing", () => {
      EVS.forEach((ev) => removeEventListener(ev, tentar, true));
      btn.remove();
    });
    audio.addEventListener("ended", () => btn.remove());
    audio.addEventListener("error", () => {
      btn.remove();
      console.error("luto.mp3 não carregou", audio.error);
    });
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      audio.play().catch((err) => console.error("play() falhou até no botão:", err));
    });
    EVS.forEach((ev) => addEventListener(ev, tentar, true));
    tentar();
    setTimeout(() => { if (audio.paused) btn.style.display = "block"; }, 700);
  });
})();
