Git Workflow For Team
Khi phát triển một tính năng:

Step 1: tạo branch
git checkout develop
git checkout -b feature/ten-tinh-nang

Step 2: code

Step 3: kiểm tra thay đổi
git status

Step 4: xem diff
git diff

Step 5: add từng file
git add file1
git add file2

Step 6: commit
git commit -m "feature: ten tinh nang"

Step 7: pull code mới nhất
git pull origin develop

Step 8: push branch
git push origin feature/ten-tinh-nang

Step 9: tạo Pull Request vào develop
