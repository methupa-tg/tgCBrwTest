(function () {
  // Create floating button
  const btn = document.createElement("div");
  btn.id = "thyaga-chat-btn";
  btn.innerHTML = "💬";
  btn.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #6610f2, #9b59b6);
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

  // Create iframe container
  const container = document.createElement("div");
  container.id = "thyaga-chat-container";
  container.style.cssText = `
    position: fixed;
    bottom: 90px;
    right: 24px;
    width: 420px;
    height: 620px;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    display: none;
    z-index: 9998;
    overflow: hidden;
  `;

  // Refresh button
  const refreshBtn = document.createElement("button");
  refreshBtn.innerHTML = "⟳";
  refreshBtn.style.cssText = `
    position: absolute;
    top: 8px;
    right: 8px;
    width: 28px;
    height: 28px;
    background: rgba(255,255,255,0.15);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
  `;
  refreshBtn.title = "Refresh";
  refreshBtn.onclick = () => { iframe.src = iframe.src; };
  container.appendChild(refreshBtn);

  // Load your chatbot inside an iframe
  const iframe = document.createElement("iframe");
  iframe.src = "https://tgcbrwtest-production.up.railway.app";
  iframe.style.cssText = "width: 100%; height: 100%; border: none;";
  container.appendChild(iframe);

  // Toggle open/close
  btn.onclick = () => {
    const isOpen = container.style.display === "block";
    container.style.display = isOpen ? "none" : "block";
    btn.innerHTML = isOpen ? "💬" : "✕";
  };

  document.body.appendChild(btn);
  document.body.appendChild(container);
})();