import os
import csv
import re
import numpy as np
import faiss
from dotenv import load_dotenv
import pickle
from google import genai

load_dotenv()
_google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def _strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "").strip()

def load_voucher_catalog(filepath):
    chunks = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("published", "1") == "0":
                continue
            chunk = (
                f"Voucher Name: {row['title']}\n"
                f"Slug: {row['slug']}\n"
                f"Category: {row['category']}\n"
                f"Occasion: {row.get('occasion', '')}\n"
                f"Best for: {row.get('recipient', '')}\n"
                f"Tone: {row.get('tone', '')}\n"
                f"Image: {row.get('image_front', '')}\n"
                f"Description: {_strip_html(row['description'])}\n"
                f"Keywords: {row.get('keywords', '')}\n"
                f"Featured: {row.get('featured', '')}"
            )
            chunks.append(chunk)
    return chunks

def load_faq(filepath):
    chunks = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk = (
                f"Q: {row['Question'].strip()}\n"
                f"A: {row['Answer'].strip()}\n"
                f"Category: {row.get('Category', '').strip()}"
            )
            chunks.append(chunk)
    return chunks

def load_how_to(filepath):
    chunks = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk = (
                f"How to {row['How'].strip()}:\n"
                f"{row['Steps'].strip()}"
            )
            chunks.append(chunk)
    return chunks

def load_links(filepath):
    chunks = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk = (
                f"title: {row['title'].strip()}\n"
                f"url: {row['url'].strip()}\n"
                f"description: {row.get('description', '').strip()}"
            )
            chunks.append(chunk)
    return chunks

def load_merchants_loc(filepath):
    chunks = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk = (
                f"Merchant: {row['merchant_name'].strip()}\n"
                f"City: {row['City'].strip()}\n"
                f"Location: {row['Location'].strip()}\n"
                f"Status: {row.get('Status', '').strip()}\n"
                f"Category: {row.get('Category', '').strip()}\n"
                f"Type: {row.get('type', '').strip()}"
            )
            chunks.append(chunk)
    return chunks

def _split_large_chunk(chunk, max_chars=700):
    """Split a chunk that's too large by grouping its numbered/bulleted lines."""
    if len(chunk) <= max_chars:
        return [chunk]
    lines = chunk.split("\n")
    header = lines[0]
    result = []
    batch = [header]
    for line in lines[1:]:
        if re.match(r'^\d+\.', line.strip()) and len("\n".join(batch)) > 400:
            result.append("\n".join(batch))
            batch = [header, line]
        else:
            batch.append(line)
    if batch:
        result.append("\n".join(batch))
    return result

def load_thyaga_info(filepath):
    chunks = []
    current = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("*") and current:
                chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
    if current:
        chunks.append("\n".join(current))
    result = []
    for chunk in chunks:
        result.extend(_split_large_chunk(chunk))
    return result

def load_corporate_info(filepath):
    chunks = []
    current = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("*") and current:
                chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks

def load_for_merchants(filepath):
    chunks = []
    current = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("*") and current:
                chunks.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks

def load_special_redemptions(filepath):
    chunks = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunk = (
                f"Special Redemption Instructions for: {row['Merchant'].strip()}\n"
                f"Type: {row['type'].strip()}\n"
                f"How to redeem at {row['Merchant'].strip()}:\n"
                f"{row['redeem instructions'].strip()}"
            )
            chunks.append(chunk)
    return chunks

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_all_documents():
    chunks = []
    chunks += load_voucher_catalog(os.path.join(BASE_DIR, "catog.csv"))
    chunks += load_faq(os.path.join(BASE_DIR, "faq.csv"))
    chunks += load_how_to(os.path.join(BASE_DIR, "how_to.csv"))
    chunks += load_special_redemptions(os.path.join(BASE_DIR, "special_redemptions.csv"))
    chunks += load_links(os.path.join(BASE_DIR, "links - Sheet1.csv"))
    chunks += load_merchants_loc(os.path.join(BASE_DIR, "Merchants426.csv"))
    chunks += load_thyaga_info(os.path.join(BASE_DIR, "thyagaInfo.txt"))
    chunks += load_corporate_info(os.path.join(BASE_DIR, "corporates.txt"))
    chunks += load_for_merchants(os.path.join(BASE_DIR, "forMer.txt"))
    return chunks

CACHE_DIR = os.path.join(BASE_DIR, "cache")
INDEX_FILE = os.path.join(CACHE_DIR, "faiss_index.bin")
CHUNKS_FILE = os.path.join(CACHE_DIR, "chunks.pkl")

def save_cache(index, chunks):
    os.makedirs(CACHE_DIR, exist_ok=True)
    faiss.write_index(index, INDEX_FILE)
    with open(CHUNKS_FILE, "wb") as f:
        pickle.dump(chunks, f)
    print("Cache saved.")

def load_cache():
    if os.path.exists(INDEX_FILE) and os.path.exists(CHUNKS_FILE):
        print("Loading index from cache...")
        index = faiss.read_index(INDEX_FILE)
        with open(CHUNKS_FILE, "rb") as f:
            chunks = pickle.load(f)
        print(f"Loaded {index.ntotal} vectors from cache.")
        return index, chunks
    return None, None

def build_index(chunks):
    cached_index, cached_chunks = load_cache()
    if cached_index is not None:
        return cached_index, cached_chunks

    print(f"Embedding {len(chunks)} chunks... (first time only)")

    all_embeddings = []
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        response = _google_client.models.embed_content(
            model="text-embedding-004",
            contents=batch,
        )
        all_embeddings.extend([e.values for e in response.embeddings])

    embeddings = np.array(all_embeddings, dtype="float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    save_cache(index, chunks)
    print(f"Index built with {index.ntotal} vectors.")
    return index, chunks

def retrieve(query, index, chunks, top_k=8):
    response = _google_client.models.embed_content(
        model="text-embedding-004",
        contents=[query],
    )

    query_vec = np.array([response.embeddings[0].values], dtype="float32")
    faiss.normalize_L2(query_vec)

    distances, indices = index.search(query_vec, top_k)

    results = []
    for idx in indices[0]:
        if idx != -1:
            results.append(chunks[idx])
    return results