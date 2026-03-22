import os
import json
import re
import numpy as np
import torch

from fastapi import FastAPI
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from transformers import AutoTokenizer, AutoModelForCausalLM


# =========================================================
# ⚙️ CONFIG - nơi cấu hình toàn bộ đường dẫn và tham số
# =========================================================

# File do STT sinh ra
TRANSCRIPT_FILE = "data/output/transcript.txt"

# File do summary sinh ra
SUMMARY_FILE = "data/output/summary.json"

# File chứa các đoạn nhỏ (chunk) để search nhanh
CHUNKS_FILE = "data/output/chunks.json"

# File lưu lịch sử chat (memory)
MEMORY_FILE = "data/output/memory.json"

# Số câu trong mỗi chunk
CHUNK_SIZE = 2


# =========================================================
# 📂 TẠO THƯ MỤC
# =========================================================

def ensure_dirs():
    """
    Đảm bảo thư mục data/output tồn tại
    Nếu chưa có thì tạo mới
    """
    os.makedirs("data/output", exist_ok=True)


# =========================================================
# 📖 LOAD DỮ LIỆU
# =========================================================

def load_transcript():
    """
    Đọc file transcript (text thuần từ STT)
    """
    if not os.path.exists(TRANSCRIPT_FILE):
        return None

    return open(TRANSCRIPT_FILE, encoding="utf-8").read().strip()


def load_summary():
    """
    Đọc file summary (JSON)
    """
    if not os.path.exists(SUMMARY_FILE):
        return None

    return json.load(open(SUMMARY_FILE, encoding="utf-8"))


# =========================================================
# 🧠 MEMORY SYSTEM (giữ lịch sử chat)
# =========================================================

def load_memory():
    """
    Load memory từ file JSON

    ⚠️ Fix lỗi:
    - Nếu file rỗng → tránh crash JSONDecodeError
    """
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_memory(memory):
    """
    Ghi memory xuống file
    """
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_memory(user, bot):
    """
    Thêm 1 lượt chat vào memory
    """

    memory = load_memory()

    memory.append({
        "user": user,
        "bot": bot
    })

    # chỉ giữ 10 lượt gần nhất (tránh file quá to)
    memory = memory[-10:]

    save_memory(memory)


# =========================================================
# ✂️ CHIA CÂU + CHUNKING (RAG)
# =========================================================

def split_sentences(text):
    """
    Tách text thành từng câu
    """
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def split_into_chunks(text):
    """
    Gom nhiều câu thành 1 chunk

    👉 Mục tiêu:
    - mỗi chunk = 1 đoạn ngữ cảnh nhỏ
    - giúp RAG tìm chính xác hơn
    """

    sentences = split_sentences(text)

    chunks = []
    temp = []

    for s in sentences:
        temp.append(s)

        if len(temp) >= CHUNK_SIZE:
            chunks.append(". ".join(temp))
            temp = []

    if temp:
        chunks.append(". ".join(temp))

    return chunks


def build_chunks():
    """
    Tạo file chunks.json từ transcript
    """

    text = load_transcript()
    if not text:
        return None

    chunks = split_into_chunks(text)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    return chunks


# =========================================================
# 🧠 EMBEDDING (RAG SEARCH)
# =========================================================

def load_embedding():
    """
    Load model embedding

    👉 Model này biến text → vector số
    """
    print("🔄 Loading embedding model...")
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def precompute_embeddings(chunks, model):
    """
    🔥 TỐI ƯU QUAN TRỌNG:
    - encode chunks 1 lần duy nhất
    - không encode lại mỗi lần query
    """
    print("⚡ Precomputing embeddings...")
    return model.encode(chunks)


def search_context(query, chunks, chunk_embeddings, model, top_k=3):
    """
    Tìm các đoạn liên quan nhất tới câu hỏi

    Cách hoạt động:
    1. encode câu hỏi → vector
    2. so sánh cosine similarity với từng chunk
    3. lấy top_k đoạn giống nhất
    """

    query_embedding = model.encode([query])

    scores = cosine_similarity(query_embedding, chunk_embeddings)[0]

    top_indices = np.argsort(scores)[-top_k:][::-1]

    return [chunks[i] for i in top_indices]


# =========================================================
# 🤖 LOAD LOCAL LLM
# =========================================================

def load_llm():
    """
    Load model ngôn ngữ (LLM)

    ⚡ tối ưu:
    - float16 → giảm RAM
    - low_cpu_mem_usage → load nhanh hơn
    """

    print("⚡ Loading LLM...")

    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )

    model = model.to("cpu")  # chạy CPU

    return tokenizer, model


# =========================================================
# 🧠 PROMPT ENGINEERING
# =========================================================

def build_prompt(query, contexts, summary, memory):
    """
    Đây là phần QUAN TRỌNG NHẤT

    👉 quyết định bot có thông minh hay không
    """

    context_text = "\n".join(contexts)

    summary_text = summary["summary"] if summary else ""

    # lấy 5 đoạn hội thoại gần nhất
    memory_text = ""
    for m in memory[-5:]:
        memory_text += f"User: {m['user']}\nBot: {m['bot']}\n"

    return f"""
Bạn là AI trợ lý cuộc họp.

Luật:
- KHÔNG được bịa
- Chỉ trả lời dựa trên dữ liệu
- Trả lời tự nhiên như con người

===== MEMORY =====
{memory_text}

===== SUMMARY =====
{summary_text}

===== CONTEXT =====
{context_text}

===== QUESTION =====
{query}

===== ANSWER =====
"""


# =========================================================
# 🤖 GENERATE ANSWER
# =========================================================

def generate(prompt, tokenizer, model):
    """
    Sinh câu trả lời từ LLM
    """

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # cắt phần answer
    return result.split("===== ANSWER =====")[-1].strip()


# =========================================================
# 🚀 FASTAPI SERVER
# =========================================================

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


# =========================================================
# 🔄 INIT SYSTEM (CHẠY 1 LẦN DUY NHẤT)
# =========================================================

ensure_dirs()

# 1. chunks
if not os.path.exists(CHUNKS_FILE):
    print("⚠️ Building chunks...")
    chunks = build_chunks()
else:
    chunks = json.load(open(CHUNKS_FILE, encoding="utf-8"))

# 2. summary + memory
summary = load_summary()
memory = load_memory()

# 3. load model
embed_model = load_embedding()
chunk_embeddings = precompute_embeddings(chunks, embed_model)

tokenizer, llm_model = load_llm()


# =========================================================
# 💬 API CHAT
# =========================================================

@app.post("/chat")
def chat_api(req: ChatRequest):
    """
    API chính để chat

    Flow:
    user → search context → build prompt → LLM → trả lời → lưu memory
    """

    global memory

    query = req.message

    # 🔍 RAG search
    contexts = search_context(
        query,
        chunks,
        chunk_embeddings,
        embed_model
    )

    # 🧠 build prompt
    prompt = build_prompt(query, contexts, summary, memory)

    # 🤖 generate
    answer = generate(prompt, tokenizer, llm_model)

    # 💾 lưu memory
    add_memory(query, answer)

    return {
        "answer": answer,
        "contexts": contexts
    }


# =========================================================
# 🧪 RUN LOCAL
# =========================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "chatbot_api:app",
        host="127.0.0.1",
        port=8002,
        reload=False
    )