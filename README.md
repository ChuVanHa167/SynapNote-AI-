# SynapNote AI

Dự án Next.js cung cấp giao diện quản trị và công cụ AI hỗ trợ ghi chú, phân tích cuộc họp.

## 🚀 Hướng Dẫn Cài Đặt và Chạy Dự Án

Làm theo các bước dưới đây để cài đặt và chạy dự án không gặp lỗi:

### 1. Yêu cầu hệ thống
- **Node.js**: Phiên bản 20.x trở lên (khuyến nghị).
- **Trình quản lý gói**: npm (hoặc yarn, pnpm).

### 2. Cài đặt thư viện
Mở terminal tại thư mục gốc của dự án (`SynapNote-AI-`) và chạy lệnh sau để cài đặt tất cả các dependencies:

```bash
npm install
```
*(Lưu ý: Nếu bạn sử dụng yarn hoặc pnpm, hãy dùng lệnh tương ứng `yarn install` hoặc `pnpm install`)*

### 3. Chạy môi trường phát triển (Development)
Sau khi cài đặt xong, khởi chạy server development bằng lệnh:

```bash
npm run dev
```

### 4. Truy cập giao diện
Mở trình duyệt và truy cập vào đường dẫn:
[http://localhost:3000](http://localhost:3000)

---

## 🛠️ Các Lệnh Khác

- **Build cho Production**:
  ```bash
  npm run build
  ```
- **Chạy Production Server (sau khi đã build)**:
  ```bash
  npm start
  ```
- **Chạy Linter**:
  ```bash
  npm run lint
  ```

## 📦 Stack Công Nghệ Chính
- **Framework**: Next.js 16.1 (App Router)
- **UI & Styling**: Tailwind CSS, Lucide React
- **Ngôn ngữ**: TypeScript
