import cohere
import os
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from kb.rag import load_all_documents, build_index, retrieve
from db.database import init_db, save_message, get_all_sessions, get_session_messages
import uuid
import pickle
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Response

load_dotenv()

api_key = os.getenv("COHERE_API_KEY")
if not api_key:
    raise EnvironmentError("COHERE_API_KEY is not set.")

co = cohere.ClientV2(api_key)

print("Loading knowledge base...")
all_chunks = load_all_documents()
faiss_index, chunk_store = build_index(all_chunks)

slug_image_map = {}
slug_category_map = {}
for _chunk in all_chunks:
    _slug = re.search(r'^Slug: (.+)$', _chunk, re.MULTILINE)
    _img = re.search(r'^Image: (.+)$', _chunk, re.MULTILINE)
    _cat = re.search(r'^Category: (.+)$', _chunk, re.MULTILINE)
    if _slug and _img:
        slug_image_map[_slug.group(1).strip()] = _img.group(1).strip()
    if _slug and _cat:
        slug_category_map[_slug.group(1).strip()] = _cat.group(1).strip()

GENERAL_SLUGS = [s for s, c in slug_category_map.items() if c.strip().lower() == "general"]
GENERAL_IMAGES = [slug_image_map[s] for s in GENERAL_SLUGS if s in slug_image_map]
GENERAL_LINKS = [f"https://thyaga.lk/buy-voucher/General/{s}" for s in GENERAL_SLUGS if s in slug_image_map]

print("Ready!\n")

init_db()

SYSTEM_PROMPT = (
    "You are the Customer Support Assistant of Thyaga.lk. "
    "Answer using ONLY information from the provided context. "
    "Keep all answers short and conversational. "
    "If a question is completely unrelated to Thyaga (e.g. weather, sports, news), say: 'Sorry, I can only help with Thyaga vouchers and information.' "
    "Do NOT use that phrase when the user is asking about vouchers or gift cards — even if that specific voucher does not exist. "
    "If the context doesn't have enough info, say so honestly. "

    "VOUCHER RECOMMENDATIONS — follow this format exactly:\n"
    "ONLY output the voucher list, nothing else. No intro sentence. No explanation.\n"
    "For each voucher output exactly this:\n"
    "🎁 [Voucher Name]\n"
    "👉 https://thyaga.lk/buy-voucher/[category]/[slug]\n"
    "Show 3-6 vouchers max. Nothing else."

    "If the user is vague (e.g. 'show me all birthday vouchers'), respond with:\n"
    "Here are all vouchers in that category: https://thyaga.lk/buy-voucher/[Category]\n"
    "For categories with spaces use %20 e.g. Thank%20You. "
    "If completely unclear, send them to: https://thyaga.lk/buy-voucher\n"

    "For non-voucher questions (FAQs, how-to, general info), answer in plain text only. "
    "Do NOT include any voucher links or recommendations unless the user specifically asked for vouchers."

    "MERCHANT / REDEMPTION QUESTIONS — when the user asks whether they can redeem at a specific merchant or asks about merchant locations: "
    "Answer in plain text only. Confirm yes or no and mention the merchant name. You may list branch names/cities if helpful. "
    "Do NOT generate any https://thyaga.lk links for merchants. Do NOT use the voucher recommendation format for merchants. "
    "At the very end of your response add [MERCHANT] on a new line. Do NOT add [MERCHANT] for any other situation."

    "IMPORTANT: If the user asks for a specific voucher or category that does NOT exist in the knowledge base, "
    "say something like: 'We don't have [X] vouchers at the moment.' Keep it short and friendly. "
    "Then add [NO_VOUCHER] on a new line at the very end of your response. "
    "Do NOT add [NO_VOUCHER] for any other situation."

    "CONTACT US — add [CONTACT] on a new line at the very end of your response (and nowhere else) when the user's request requires human support. "
    "This includes: bulk or large-quantity voucher purchases, corporate gifting orders, "
    "refund or dispute requests, a voucher that was not delivered or is not working, "
    "account or login issues, complaints about a merchant, and any other situation "
    "where you cannot resolve the issue through the knowledge base alone. "
    "When adding [CONTACT], always include a short friendly line telling the user to reach out and include the phone number in bold — "
    "for example: 'For this, it's best to contact our team directly on **+94 750 100 500** or via email.' "
    "Do NOT add [CONTACT] for general FAQs, voucher recommendations, or merchant location queries."
)

app = Flask(__name__, static_folder="ui")
CORS(app, origins=[
    "https://thyaga.lk",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "https://tgcbrwtest-production.up.railway.app",
    "null"    
])

limiter = Limiter(get_remote_address, app=app)

def check_auth(username, password):
    return (
        username == os.getenv("ADMIN_USERNAME") and 
        password == os.getenv("ADMIN_PASSWORD")
    )

def authenticate():
    return Response(
        'Authentication required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("ui", filename)

@app.route("/chat", methods=["POST"])
@limiter.limit("10/minute, 30/hour")

def chat():
    data = request.get_json()
    history = data.get("history", [])
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    relevant_chunks = retrieve(user_message, faiss_index, chunk_store, top_k=8)

    clean_chunks = []
    for chunk in relevant_chunks:
        chunk = re.sub(r"^Image: .+\n", "", chunk, flags=re.MULTILINE)
        clean_chunks.append(chunk)

    context = "\n\n".join(clean_chunks)
    augmented_message = (
        f"Context from Thyaga knowledge base:\n{context}\n\n"
        f"User question: {user_message}"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": augmented_message})

    try:
        response = co.chat(
            model="command-a-03-2025",
            messages=messages,
            temperature=0.25,
            max_tokens=300,
            frequency_penalty=0.4
        )
        reply = response.message.content[0].text

    except Exception as e:
        print(f"Cohere API error: {e}")
        return jsonify({
            "reply": "Sorry, I'm having trouble generating a response right now. Please try again later.",
            "images": [],
            "links": [],
            "page_links": [],
            "session_id": session_id,
            "show_browse": False,
            "show_merchant_btns": False,
            "show_contact_btns": False
        })

    show_browse = False
    if '[NO_VOUCHER]' in reply:
        reply = reply.replace('[NO_VOUCHER]', '').strip()
        show_browse = True

    show_merchant_btns = False
    if '[MERCHANT]' in reply:
        reply = reply.replace('[MERCHANT]', '').strip()
        show_merchant_btns = True

    show_contact_btns = False
    if '[CONTACT]' in reply:
        reply = reply.replace('[CONTACT]', '').strip()
        show_contact_btns = True
        page_links = []

    recommended_slugs = re.findall(r'thyaga\.lk/buy-voucher/[^/\s]+/([\w\-]+)', reply)
    recommended_links = re.findall(r'(https://thyaga\.lk/buy-voucher/[^\s\n]+)', reply)

    images = []
    seen = set()
    for slug in recommended_slugs:
        if slug in slug_image_map and slug not in seen:
            images.append(slug_image_map[slug])
            seen.add(slug)

    if show_browse and not images:
        images = GENERAL_IMAGES[:]
        recommended_links = GENERAL_LINKS[:]

    page_links = []
    for chunk in relevant_chunks:
        if chunk.startswith("title:"):
            title_match = re.search(r'^title: (.+)$', chunk, re.MULTILINE)
            url_match = re.search(r'^url: (.+)$', chunk, re.MULTILINE)
            if title_match and url_match:
                page_links.append({
                    "title": title_match.group(1).strip(),
                    "url": url_match.group(1).strip()
                })

    button_urls = {link["url"] for link in page_links}
    for url in button_urls:
        reply = reply.replace(url, "")
    reply = re.sub(r':\s*\n', '\n', reply)
    reply = re.sub(r'\bvisit:\s*', '', reply, flags=re.IGNORECASE)
    reply = re.sub(r' {2,}', ' ', reply).strip()

    save_message(session_id, "user", user_message)
    save_message(session_id, "assistant", reply)

    return jsonify({"reply": reply, "images": images, "links": recommended_links, "page_links": page_links, "session_id": session_id, "show_browse": show_browse, "show_merchant_btns": show_merchant_btns, "show_contact_btns": show_contact_btns})

@app.route("/admin")
def admin():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    
    sessions = get_all_sessions()
    rows = "".join(
        f"<tr><td>{sid[:16]}...</td><td>{started}</td><td>{count}</td><td><a href='/admin/session/{sid}'>View</a></td></tr>"
        for sid, started, count in sessions
    )
    return f"<h2>Conversation History</h2><table border=1 cellpadding=6><tr><th>Session</th><th>Started</th><th>Messages</th><th></th></tr>{rows}</table>"

@app.route("/admin/session/<session_id>")
def admin_session(session_id):
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    messages = get_session_messages(session_id)
    rows = "".join(f"<tr><td>{role}</td><td>{content}</td><td>{ts}</td></tr>" for role, content, ts in messages)
    return f"<a href='/admin'>← Back</a><br><br><table border=1 cellpadding=6><tr><th>Role</th><th>Message</th><th>Time</th></tr>{rows}</table>"

@app.route("/widget.js")
def widget():
    return send_from_directory(".", "widget.js")

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
            port=int(os.getenv("PORT", 5000))
    )