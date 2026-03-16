# SynapNote-AI-
Trợ lý ghi chép & trích xuất nội dung cuộc họp thông minh

https://chatgpt.com/share/69ae8402-9e20-800b-8299-e16c896c91b8

# Cách thức chạy code 
Mở Terminal 1

cd backend
python -m uvicorn main:app --reload --port 8000 

# Cài đặt thư viện
Mở Terminal 2

npm install

# Chạy môi trường phát triển

npm run dev 

# Gitflow: 
```
main
 │
develop
 ├── feature/
 └── bugfix/*
 └── release/*
```

trong đó: 
- main là nhánh chứa code sạch, code production không được commit trực tiếp. Chỉ nhánh release mới được merge vào main
- develop là nhánh tách ra từ main chứa code chung của team, là nhánh dành cho team phát triển code được update code mới nhất. code chạy ổn định có thể merge vào release.
- feature là nhánh tách ra từ dev để phát triển tính năng, mỗi người làm một feature riêng, code ổn thì merge vào dev.
- release là nhánh tách ra từ dev và là nhánh duy nhất được merge vào main.

# Git Workflow For Team:
Khi phát triển một tính năng(feature):
- Step 1: tạo branch
```
git checkout develop (chuyển về làm việc tại nhánh dev)
git checkout -b feature/tên_tính_năng (tạo và chuyển sang làm việc tại nhánh feature/tên_tính_năng)
```
- Step 2: code tại nhánh feature.
- Step 3: kiểm tra thay đổi
```
git status (kiểm tra thay đổi xem file nào bị sửa, file nào chưa add chưa commit.)
```
- Step 4: xem diff
```
git diff(xem thay đổi code)
```
- Step 5: add từng file
```
git add file1 (thêm file1 vào môi trường staging area, chuẩn bị commit)
git add file2
or
git add file1 file 2
(không được "git add ." vì có thể add cả những file ẩn những rủi ro mình không biết)
```
- Step 6: commit
```
git commit -m "feature: ten tinh nang" (lưu thay đổi thành 1 phiên bản, add là chọn file, commit là lưu lại)
```
- Step 7: pull code mới nhất 
git pull origin develop(kéo code mới nhất từ nhánh dev(remote) về máy(local))
- Step 8: push branch 
git push origin feature/ten_tinh_nang(đấy code từ máy(local) lên github repo(remote))
- Step 9: tạo Pull Request vào develop
- quy định trước khi push phải:
```
git status
git diff
git pull origin tên_nhánh
```
- xử lý conflig:
```
git pull origin develop
Sửa code, sau đó:
git add file
git commit -m "..."
```
# Training Git cấp tốc cho team:
```
git clone <repo>
git status
git add file
git commit -m "message"
git pull origin develop
git push origin feature/abc
```
# bài demo cho team: 
Project: SynapNote-AI
Bối cảnh dự án: SynapNote-AI là một web app giúp ghi chép và phân tích cuộc họp thông minh.

Vấn đề:
- các công ty có quá nhiều cuộc họp
- nội dung họp khó nhớ
- không có tổng kết rõ ràng

Giải pháp:
- Ứng dụng AI để:
  + ghi âm cuộc họp
  + chuyển audio → transcript
  + phân tích nội dung
  + tạo summary(tóm tắt) và action items(hành động)

Quy trình hoạt động của hệ thống:
Workflow hệ thống:
```
User record meeting
        │
        ▼
Upload audio file
        │
        ▼
Speech to Text (STT)
        │
        ▼
Transcript
        │
        ▼
LLM + RAG Analysis
        │
        ▼
Meeting Summary(tóm tắt cuộc họp)
        │
        ▼
Action Items / Insights(mục hành động/thông tin cần thiết)
```
Công nghệ sử dụng:
- Backend
  + Python
  + FastAPI
  + STT (Speech-to-Text)
  + LLM
  + RAG
- Frontend
  + HTML / JS
- Infrastructure
  + GitHub

Thiết lập branch:
main
develop

Workflow:
```
main
 │
develop
 ├── feature/*
 ├── bugfix/*
 └── release/*
 ```
Phân công 5 developer
Team gồm:
Dev Nguyệt
Dev Long
Dev Lan
Dev Tuyết
Dev Tiến

Phân chia module
Dev A
Audio Upload System
feature/audio-upload

Dev B
Speech to Text (STT)
feature/stt-module

Dev C
Transcript Processor
feature/transcript-parser

Dev D
LLM Meeting Analyzer
feature/meeting-analyzer

Dev E
Frontend UI
feature/frontend-ui

Bước 1: Clone project
Tất cả dev chạy:
```
git clone https://github.com/team/SynapNote-AI.git
cd SynapNote-AI
```
Chuyển sang develop:
```
git checkout develop
```
Bước 2: Dev A thực hành
Tạo branch:
```
git checkout -b feature/audio-upload
```
Tạo file:
```
backend/upload.py
```
Ví dụ code:
```
def upload_audio(file):
    return "audio uploaded"
```
Kiểm tra thay đổi:
```
git status
```
Xem diff:
```
git diff
```
Add file:
```
git add backend/upload.py
```
Commit:
```
git commit -m "feature: add audio upload service"
```
Pull code mới:
```
git pull origin develop
```
Push branch:
```
git push origin feature/audio-upload
```
Bước 3: Dev B thực hành
Speech-to-Text module.
Tạo branch:
```
git checkout develop
git checkout -b feature/stt-module
```
Tạo file:
```
ai/stt.py
```
Ví dụ code:
```
def speech_to_text(audio):
    return "transcript text"
```
Commit:
```
git add ai/stt.py
git commit -m "feature: add STT module"
```
Push:
```
git push origin feature/stt-module
```
Bước 4: Dev C thực hành
Transcript parser.
Branch:
feature/transcript-parser
File:
```
ai/parser.py
```
Code:
```
def parse_transcript(text):
    return text.split(".")
```
Commit:
```
git add ai/parser.py
git commit -m "feature: transcript parser"
```
Push.

Bước 5: Dev D thực hành
Meeting analyzer.
Branch:
feature/meeting-analyzer
File:
```
ai/analyzer.py
```
Code:
```
def analyze_meeting(text):
    return "meeting summary"
```
Commit:
```
git commit -am "feature: meeting analyzer using LLM"
```
Push.

Bước 6: Dev E thực hành
Frontend UI.
Branch:
feature/frontend-ui
File:
```
frontend/index.html
```
Ví dụ:
```
<h1>SynapNote AI</h1>
<button>Upload Meeting Audio</button>
```
Commit:
```
git add frontend/index.html
git commit -m "feature: frontend UI"
```
Push.

Bước 7: Pull Request
Mỗi dev tạo Pull Request:
```
feature/audio-upload → develop
feature/stt-module → develop
feature/transcript-parser → develop
feature/meeting-analyzer → develop
feature/frontend-ui → develop
```
Leader review code.

Bước 8: Merge vào develop
Sau khi merge:
```
develop
│
├── frontend
│
├── backend
│
└── ai
```
Bước 9: Team cập nhật code
Mỗi dev chạy:
```
git checkout develop
git pull origin develop
```
Bước 10: Tạo Release
Leader tạo branch:
```
git checkout develop
git checkout -b release/v1.0
```
Update version.
Commit:
```
git commit -am "release: version 1.0"
```
Merge vào main.
```
git checkout main
git merge release/v1.0
```
Tag version:
```
git tag v1.0
```
Push.
