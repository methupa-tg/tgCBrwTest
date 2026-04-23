const API_URL = "https://tgcbrwtest-production.up.railway.app/chat";

const chatMessages = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

let history = [];
let sessionId = null;

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  document.getElementById("suggestions").style.display = "none";

  appendMessage("user", text);
  history.push({ role: "user", content: text });
  userInput.value = "";
  setLoading(true);

  const typingEl = appendTyping();

  fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, history: history.slice(0, -1), session_id: sessionId }),
  })
    .then((res) => res.json())
    .then((data) => {
      typingEl.remove();
      if (data.session_id) sessionId = data.session_id;
      const reply = data.reply || "Sorry, something went wrong.";
      appendMessage("bot", reply, data.images || [], data.links || [], data.page_links || [], data.show_browse || false, data.show_merchant_btns || false, data.show_contact_btns || false, data.cta_button || null);
      history.push({ role: "assistant", content: reply });
    })
    .catch(() => {
      typingEl.remove();
      appendMessage("bot", "Could not reach the server. Please try again.");
    })
    .finally(() => setLoading(false));
}

function appendMessage(role, text, images = [], voucherLinks = [], pageLinks = [], showBrowse = false, showMerchantBtns = false, showContactBtns = false, ctaButton = null) {
  const msg = document.createElement("div");
  msg.classList.add("message", role);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  if (images.length === 0) {
    bubble.innerHTML = formatMessage(text);
  }

  if (role === "bot" && images.length > 0) {
    msg.classList.add("has-vouchers");

    if (showBrowse) {
      const textEl = document.createElement("div");
      textEl.innerHTML = formatMessage(text);
      bubble.appendChild(textEl);

      const suggLabel = document.createElement("div");
      suggLabel.classList.add("general-voucher-label");
      suggLabel.textContent = "Here are some popular vouchers you might like:";
      bubble.appendChild(suggLabel);
    }

    const cardRow = document.createElement("div");
    cardRow.classList.add("voucher-cards");
    images.slice(0, 5).forEach((url, index) => {
      const card = document.createElement("a");
      card.classList.add("voucher-card");
      card.href = voucherLinks[index] || "#";
      card.target = "_blank";
      card.rel = "noopener noreferrer";
      card.innerHTML = `<img src="${url}" alt="voucher" class="voucher-img" onerror="this.parentElement.style.display='none'"/>`;
      cardRow.appendChild(card);
    });
    bubble.appendChild(cardRow);
  }

  if (role === "bot" && showBrowse) {
    const browseRow = document.createElement("div");
    browseRow.classList.add("page-link-buttons");
    const browseBtn = document.createElement("a");
    browseBtn.classList.add("page-link-btn");
    browseBtn.href = "https://thyaga.lk/buy-voucher";
    browseBtn.target = "_blank";
    browseBtn.rel = "noopener noreferrer";
    browseBtn.textContent = "Browse Vouchers";
    browseRow.appendChild(browseBtn);
    bubble.appendChild(browseRow);
  }

  if (role === "bot" && showMerchantBtns) {
    const merchantRow = document.createElement("div");
    merchantRow.classList.add("page-link-buttons");
    [{ label: "Buy Vouchers", url: "https://thyaga.lk/buy-voucher" },
     { label: "Merchants", url: "https://thyaga.lk/merchants" }].forEach(({ label, url }) => {
      const btn = document.createElement("a");
      btn.classList.add("page-link-btn");
      btn.href = url;
      btn.target = "_blank";
      btn.rel = "noopener noreferrer";
      btn.textContent = label;
      merchantRow.appendChild(btn);
    });
    bubble.appendChild(merchantRow);
  }

  if (role === "bot" && showContactBtns) {
    const contactRow = document.createElement("div");
    contactRow.classList.add("page-link-buttons");
    [{ label: "📞 Call Us", url: "tel:+94750100500" },
     { label: "✉️ Email Us", url: "mailto:info@thyaga.lk" }].forEach(({ label, url }) => {
      const btn = document.createElement("a");
      btn.classList.add("page-link-btn");
      btn.href = url;
      btn.textContent = label;
      contactRow.appendChild(btn);
    });
    bubble.appendChild(contactRow);
  }

  if (role === "bot" && ctaButton) {
    const ctaRow = document.createElement("div");
    ctaRow.classList.add("page-link-buttons");
    const btn = document.createElement("a");
    btn.classList.add("page-link-btn");
    btn.href = ctaButton.url;
    btn.target = "_blank";
    btn.rel = "noopener noreferrer";
    btn.textContent = ctaButton.label;
    ctaRow.appendChild(btn);
    bubble.appendChild(ctaRow);
  }

  if (role === "bot" && pageLinks.length > 0) {
    const linkRow = document.createElement("div");
    linkRow.classList.add("page-link-buttons");
    pageLinks.forEach(({ title, url }) => {
      const btn = document.createElement("a");
      btn.classList.add("page-link-btn");
      btn.href = url;
      btn.target = "_blank";
      btn.rel = "noopener noreferrer";
      btn.textContent = title;
      linkRow.appendChild(btn);
    });
    bubble.appendChild(linkRow);
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
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\n/g, "<br>");
}

function sendSuggestion(btn) {
  const text = btn.textContent.trim();
  document.getElementById("suggestions").style.display = "none";
  userInput.value = text;
  sendMessage();
}