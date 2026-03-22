import os
import json

# =========================
# 📂 PATH
# =========================
INPUT_TRANSCRIPT = "data/output/transcript.txt"
OUTPUT_SUMMARY = "data/output/summary.json"


# =========================
# 🧠 SIMPLE SUMMARY ENGINE (FREE)
# =========================
def summarize(text: str):
    """
    Summary rule-based (FREE)

    Sau này có thể thay bằng LLM
    """

    sentences = text.split(".")

    # lọc câu dài (thường quan trọng hơn)
    important = [s.strip() for s in sentences if len(s.split()) > 5]

    summary = important[:3]  # lấy 3 câu đầu

    return {
        "summary": " ".join(summary),
        "key_points": summary,
        "action_items": [],
        "keywords": extract_keywords(text)
    }


# =========================
# 🔍 KEYWORD EXTRACT
# =========================
def extract_keywords(text: str):
    words = text.lower().split()

    stopwords = ["là", "và", "của", "có", "được", "trong"]

    freq = {}
    for w in words:
        if w not in stopwords and len(w) > 3:
            freq[w] = freq.get(w, 0) + 1

    # top 5 keyword
    sorted_words = sorted(freq, key=freq.get, reverse=True)

    return sorted_words[:5]


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