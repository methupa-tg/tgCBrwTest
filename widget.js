(function () {
  const STORAGE_KEY = "thyaga_session_id";
  const BASE_URL = "https://tgcbrwtest-production.up.railway.app";

  function getIframeSrc() {
    const sid = localStorage.getItem(STORAGE_KEY);
    return sid ? BASE_URL + "?session_id=" + encodeURIComponent(sid) : BASE_URL;
  }

  const btn = document.createElement("div");
  btn.id = "thyaga-chat-btn";
  btn.innerHTML = "🎁";
  btn.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #895eec, #2c1781);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(102,16,242,0.4);
    z-index: 9999;
    transition: transform 0.2s;
  `;
  btn.onmouseover = () => btn.style.transform = "scale(1.1)";
  btn.onmouseout = () => btn.style.transform = "scale(1)";

  const container = document.createElement("div");
  container.id = "thyaga-chat-container";
  const isMobile = window.innerWidth <= 480;
  container.style.cssText = `
    position: fixed;
    bottom: ${isMobile ? "0" : "90px"};
    right: ${isMobile ? "0" : "24px"};
    width: ${isMobile ? "100vw" : "420px"};
    height: ${isMobile ? "100dvh" : "620px"};
    border-radius: ${isMobile ? "0" : "16px"};
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    display: none;
    z-index: 9998;
    overflow: hidden;
  `;

  const refreshBtn = document.createElement("button");
  refreshBtn.innerHTML = "⟳";
  refreshBtn.style.cssText = `
    position: absolute;
    top: 8px;
    right: 8px;
    width: 26px;
    height: 26px;
    background: rgba(255,255,255,0.15);
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 15px;
    cursor: pointer;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    transition: background 0.15s, transform 0.15s;
  `;
  refreshBtn.title = "Refresh";
  refreshBtn.onmousedown = () => {
    refreshBtn.style.transform = "scale(0.82)";
    refreshBtn.style.background = "rgba(255,255,255,0.32)";
  };
  refreshBtn.onmouseup = () => {
    refreshBtn.style.transform = "scale(1)";
    refreshBtn.style.background = "rgba(255,255,255,0.15)";
    iframe.src = getIframeSrc();
  };
  refreshBtn.onmouseleave = () => {
    refreshBtn.style.transform = "scale(1)";
    refreshBtn.style.background = "rgba(255,255,255,0.15)";
  };
  container.appendChild(refreshBtn);

  const iframe = document.createElement("iframe");
  iframe.src = getIframeSrc();
  iframe.style.cssText = "width: 100%; height: 100%; border: none;";
  container.appendChild(iframe);

  window.addEventListener("message", (e) => {
    if (e.origin !== BASE_URL) return;
    if (e.data && e.data.thyaga_session_id) {
      localStorage.setItem(STORAGE_KEY, e.data.thyaga_session_id);
    }
  });

  btn.onclick = () => {
    const isOpen = container.style.display === "block";
    container.style.display = isOpen ? "none" : "block";
    btn.innerHTML = isOpen ? "🎁" : "✕";
  };

  document.body.appendChild(btn);
  document.body.appendChild(container);
})();
