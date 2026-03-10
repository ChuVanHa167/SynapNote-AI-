#đầu vào là output từ STT(transcript) -> chunk trans -> AI summarize từng chunk -> merge summaries -> final meeting summary 

# python ai/summary/summary.py

def chunk_text(text, max_words=800):

    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i+max_words])
        chunks.append(chunk)

    return chunks


def prepare_summary_tasks(transcript):

    chunks = chunk_text(transcript)

    tasks = []

    for chunk in chunks:

        prompt = f"""
Tóm tắt nội dung cuộc họp sau bằng tiếng Việt.
Tập trung vào:
- Chủ đề chính
- Quyết định
- Công việc cần làm

Nội dung:
{chunk}
"""

        tasks.append(prompt.strip())

    return tasks