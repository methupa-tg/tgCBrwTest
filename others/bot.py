import cohere
import os
from dotenv import load_dotenv
from kb.rag import load_all_documents, build_index, retrieve

load_dotenv()
co = cohere.ClientV2(os.getenv("COHERE_API_KEY"))
print("Loading knowledge base...")
all_chunks = load_all_documents()
faiss_index, chunk_store = build_index(all_chunks)
print("Ready!\n")

system_prompt = (
    "You are the Customer Support Assistant of Thyaga.lk. "
    
    "Answer questions about Thyaga.lk using ONLY the information explicitly stated in the provided context. "
    "Do NOT add any details, features, or descriptions that are not directly written in the context. "
    "Keep answers short and simple. "
    "Only answer questions related to Thyaga vouchers or basic Thyaga information. "
    "If a question is unrelated, say: 'Sorry, I can only answer questions related to Thyaga vouchers and basic information.' "
    "If the context does not contain enough information, say so honestly. "
    
    "Voucher Recommendation Rules: "
    "Always mention the exact Voucher Name from the context when recommending. "
    "If the user is very specific (brand, category, or need), recommend the most relevant exact voucher. "
    "If the user is somewhat specific, suggest 2-10 relevant vouchers. "
    "If the user is general or unclear, suggest a category and include all available vouchers under that category from the context. "
    "If no vouchers match the user’s request, clearly say that no relevant vouchers are available in the provided context."
)

chat_history = [{"role": "system", "content": system_prompt}]

print("Thyaga Assistant (type 'quit' to exit)\n")

while True:
    message = input("You: ").strip()
    if message.lower() == "quit":
        break
    if not message:
        continue

    relevant_chunks = retrieve(message, faiss_index, chunk_store, top_k=8)
    context = "\n\n".join(relevant_chunks)

    augmented_message = (
        f"Context from Thyaga knowledge base:\n{context}\n\n"
        f"User question: {message}"
    )

    chat_history.append({"role": "user", "content": augmented_message})

    response = co.chat_stream(
        model="command-a-03-2025",
        messages=chat_history,
        temperature=0.25,
        max_tokens=300,
        frequency_penalty=0.4
    )

    print("Assistant: ", end="", flush=True)
    full_response = ""
    for event in response:
        if event.type == "content-delta":
            text = event.delta.message.content.text
            print(text, end="", flush=True)
            full_response += text
    print()

    chat_history[-1] = {"role": "user", "content": message}
    chat_history.append({"role": "assistant", "content": full_response})