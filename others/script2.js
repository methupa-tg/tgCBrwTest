const API_URL = "http://127.0.0.1:5000/chat";

const chatMessages = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// Chat history sent to backend (excludes system prompt — handled server-side)
let history = [];

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  history.push({ role: "user", content: text });
  userInput.value = "";
  setLoading(true);

  const typingEl = appendTyping();

  fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
  })
    .then((res) => res.json())
    .then((data) => {
      typingEl.remove();
      const reply = data.reply || "Sorry, something went wrong.";
      appendMessage("bot", reply, data.images || [], data.links || []);
      history.push({ role: "assistant", content: reply });
    })
    .catch(() => {
      typingEl.remove();
      appendMessage("bot", "Could not reach the server. Please try again.");
    })
    .finally(() => setLoading(false));
}

function appendMessage(role, text, images = [], voucherLinks = []) {
  const msg = document.createElement("div");
  msg.classList.add("message", role);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  // Render newlines as line breaks
  bubble.innerHTML = formatMessage(text);

  if (role === "bot" && vouchers.length > 0) {
    const cardRow = document.createElement("div");
    cardRow.classList.add("voucher-cards");
    vouchers.slice(0, 4).forEach(({ image, url }) => {
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.classList.add("voucher-card");
      link.innerHTML = `<img src="${image}" alt="voucher" class="voucher-img" onerror="this.parentElement.style.display='none'"/>`;
      cardRow.appendChild(link);
    });
    bubble.appendChild(cardRow);
  }

  msg.appendChild(bubble);
  chatMessages.appendChild(msg);
  scrollToBottom();
  return msg;
}

function appendTyping() {
  const msg = document.createElement("div");
  msg.classList.add("message", "bot", "typing");

  msg.innerHTML = `<div class="bubble">
    <span class="dot"></span>
    <span class="dot"></span>
    <span class="dot"></span>
  </div>`;

  chatMessages.appendChild(msg);
  scrollToBottom();
  return msg;
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setLoading(state) {
  sendBtn.disabled = state;
  userInput.disabled = state;
}

function formatMessage(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")  // bold
    .replace(/\*(.*?)\*/g, "<em>$1</em>")              // italic
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')  // clickable links
    .replace(/\n/g, "<br>");                            // newlines
}