import os
import json
import re
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# =========================
# 📂 PATH
# =========================
INPUT_TRANSCRIPT = "data/output/transcript.txt"
OUTPUT_SUMMARY = "data/output/summary.json"
SUMMARY_MODEL_NAME = os.getenv(
    "SUMMARY_MODEL_NAME",
    "VietAI/vit5-base-vietnews-summarization"
)

EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

SUMMARY_CHUNK_WORDS = int(os.getenv("SUMMARY_CHUNK_WORDS", "180"))
RETRIEVE_TOP_K = int(os.getenv("SUMMARY_RETRIEVE_TOP_K", "4"))
SUMMARY_MAX_NEW_TOKENS = int(os.getenv("SUMMARY_MAX_NEW_TOKENS", "96"))

CHUNKS_FILE = "data/output/chunks.json"
EMBEDDINGS_FILE = "data/output/chunk_embeddings.npy"
FAISS_INDEX_FILE = "data/output/chunks.faiss"
_EMBED_MODEL = None
_SUMMARY_TOKENIZER = None
_SUMMARY_MODEL = None
# =========================
# 📂 CHUNK TRANSCRIPT
# =========================
def chunk_transcript(text, max_words=SUMMARY_CHUNK_WORDS):

    sentences = split_sentences(text)
    chunks = []
    current = []
    current_words = 0

    for s in sentences:
        n = len(s.split())

        if current and current_words + n > max_words:
            chunks.append(" ".join(current).strip())
            current = []
            current_words = 0

        current.append(s)
        current_words += n

    if current:
        chunks.append(" ".join(current).strip())

    return chunks if chunks else [text.strip()]

def detect_speaker(text):
    speakers = []

    lines = text.split("\n")

    for line in lines:
        if ":" in line:
            spk = line.split(":")[0].strip()
            if len(spk) < 20:
                speakers.append(spk)

    return list(set(speakers))

def normalize_transcript(text: str):
    # bỏ timestamp [00:00 - 00:05]
    text = re.sub(r"\[\d{2}:\d{2}.*?\]", "", text)

    # bỏ speaker label [AI], [User]
    text = re.sub(r"\[.*?\]:", "", text)

    # xóa khoảng trắng dư
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def split_sentences(text: str):
    sentences = re.split(r"[.!?\n]+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def score_sentence(sentence: str):
    score = 0

    keywords = [
        "quyết định", "thống nhất", "kết luận",
        "deadline", "hạn", "cần làm",
        "phải", "nhiệm vụ", "phân công",
        "báo cáo", "triển khai"
    ]

    for k in keywords:
        if k in sentence.lower():
            score += 2

    # câu dài thường nhiều thông tin hơn
    score += len(sentence.split()) * 0.1

    return score

def extract_decisions(sentences):
    decisions = []

    for s in sentences:
        if any(k in s.lower() for k in ["quyết định", "thống nhất", "kết luận"]):
            decisions.append(s)

    return decisions

def extract_action_items(sentences):
    actions = []

    for s in sentences:
        if any(k in s.lower() for k in ["cần", "phải", "nhiệm vụ", "triển khai"]):
            actions.append(s)

    return actions


# =========================
# 📂 LLM
# =========================

def rewrite_sentence(sentence):
    s = sentence.strip()

    # viết lại đơn giản kiểu AI
    s = s.replace("phải", "cần")
    s = s.replace("nhiệm vụ", "công việc")

    if len(s) > 120:
        s = s[:120] + "..."

    return s

def deduplicate_sentences(sentences):
    seen = set()
    result = []

    for s in sentences:
        key = s.lower()

        if key not in seen:
            seen.add(key)
            result.append(s)

    return result

def extract_questions(sentences):
    questions = []

    for s in sentences:
        if "?" in s or any(k in s.lower() for k in ["không biết", "cần làm gì", "làm sao"]):
            questions.append(s)

    return questions



def load_embedding_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        print("🔄 Loading embedding model...")
        _EMBED_MODEL = SentenceTransformer(EMBED_MODEL_NAME)
    return _EMBED_MODEL


def load_summary_model():
    global _SUMMARY_TOKENIZER, _SUMMARY_MODEL
    if _SUMMARY_TOKENIZER is None or _SUMMARY_MODEL is None:
        print("🔄 Loading local summary model...")
        _SUMMARY_TOKENIZER = AutoTokenizer.from_pretrained(SUMMARY_MODEL_NAME)
        _SUMMARY_MODEL = AutoModelForSeq2SeqLM.from_pretrained(SUMMARY_MODEL_NAME)
        _SUMMARY_MODEL.to("cpu")
        _SUMMARY_MODEL.eval()
    return _SUMMARY_TOKENIZER, _SUMMARY_MODEL

def load_bridge_artifacts():
    if not os.path.exists(CHUNKS_FILE):
        return None, None, None

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    embeddings = np.load(EMBEDDINGS_FILE)
    index = faiss.read_index(FAISS_INDEX_FILE)

    model = load_embedding_model()

    return chunks, embeddings, index, model

def save_bridge_artifacts(chunks, embeddings, index):
    os.makedirs("data/output", exist_ok=True)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    np.save(EMBEDDINGS_FILE, embeddings)
    faiss.write_index(index, FAISS_INDEX_FILE)


def summarize_chunk_with_model(text):
    tokenizer, model = load_summary_model()

    text = text.strip()
    if not text:
        return ""

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256
    )

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=SUMMARY_MAX_NEW_TOKENS,
            num_beams=4,
            do_sample=False,
            early_stopping=True,
            length_penalty=1.0
        )

    return tokenizer.decode(
        output_ids[0],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True
    ).strip()


def unique_keep_order(items):
    seen = set()
    result = []

    for item in items:
        item = item.strip()
        if not item:
            continue

        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)

    return result

def build_vector_index(chunks):
    model = load_embedding_model()
    embeddings = model.encode(chunks, convert_to_numpy=True)

    # cosine similarity => normalize vectors + inner product
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return model, index, embeddings

def retrieve_relevant_chunks(query, chunks, model, index, top_k=5):
    query_emb = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_emb)

    scores, ids = index.search(query_emb, top_k)

    results = []
    for idx in ids[0]:
        if idx != -1:
            results.append(chunks[idx])

    return results

# =========================
# 🧠 SIMPLE SUMMARY ENGINE (FREE)
# =========================
def summarize(text: str):

    text = normalize_transcript(text)

    chunks = chunk_transcript(text)

    if not chunks:
        return {
            "summary": "",
            "highlights": [],
            "decisions": [],
            "action_items": [],
            "open_questions": [],
            "topics": [],
            "speakers": [],
            "retrieved_chunks": []
        }

    # ===== VECTOR BRIDGE =====
    embed_model, embeddings, index = build_vector_index(chunks)
    save_bridge_artifacts(chunks, embeddings, index)

    focus_queries = [
        "nội dung chính cuộc họp là gì",
        "các quyết định đã được thống nhất",
        "ai làm gì deadline khi nào",
        "vấn đề chưa giải quyết"
    ]

    retrieved_chunks = []
    for q in focus_queries:
        retrieved_chunks.extend(
            retrieve_relevant_chunks(q, chunks, embed_model, index, top_k=RETRIEVE_TOP_K)
        )

    retrieved_chunks = unique_keep_order(retrieved_chunks)
    if not retrieved_chunks:
        retrieved_chunks = chunks

    # ===== LOCAL LLM SUMMARY =====
    local_summaries = []
    for chunk in retrieved_chunks:
        s = summarize_chunk_with_model(chunk)
        if s:
            local_summaries.append(s)

    local_summaries = unique_keep_order(local_summaries)

    merged_context = " ".join(local_summaries[:4]) if local_summaries else " ".join(retrieved_chunks[:4])
    final_summary = summarize_chunk_with_model("Tóm tắt cuộc họp, nêu rõ quyết định, công việc và vấn đề chính:\n" + merged_context)

    # ===== RULE-BASED EXTRACTION =====
    source_sentences = []
    for chunk in retrieved_chunks:
        source_sentences.extend(split_sentences(chunk))

    source_sentences = deduplicate_sentences(source_sentences)

    decisions = extract_decisions(source_sentences)
    actions = extract_action_items(source_sentences)
    questions = extract_questions(source_sentences)
    speakers = detect_speaker(text)
    topics = extract_keywords(text)

    return {
        "summary": final_summary or " ".join(local_summaries[:3]),
        "highlights": local_summaries,
        "decisions": decisions,
        "action_items": actions,
        "open_questions": questions,
        "topics": topics,
        "speakers": speakers,
        "retrieved_chunks": retrieved_chunks,
        "chunk_count": len(chunks)
    }

# =========================
# 🔍 KEYWORD EXTRACT
# =========================
def extract_keywords(text: str):
    words = text.lower().split()

    stopwords = [
        "là","và","của","có","được","trong","những","các",
        "với","cho","khi","đó","này","thì","một","như"
    ]

    freq = {}

    for w in words:
        if w not in stopwords and len(w) > 3:
            freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq, key=freq.get, reverse=True)

    return sorted_words[:8]


# =========================
# 🧠 PIPELINE
# =========================
def run_summary():
    if not os.path.exists(INPUT_TRANSCRIPT):
        print("❌ Chưa có transcript → chạy STT trước")
        return

    with open(INPUT_TRANSCRIPT, "r", encoding="utf-8") as f:
        text = f.read()

    result = summarize(text)

    os.makedirs("data/output", exist_ok=True)

    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n===== SUMMARY =====\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print(f"\n💾 Saved → {OUTPUT_SUMMARY}")


# =========================
# 🧪 TEST
# =========================
if __name__ == "__main__":
    run_summary()