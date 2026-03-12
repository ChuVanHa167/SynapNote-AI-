import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Khai báo các route thuộc phần Authentication (không cần đăng nhập)
const authRoutes = ['/login', '/register', '/forgot-password'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // 1. Kiểm tra xem user đang ở trang auth hay không
  const isAuthRoute = authRoutes.includes(pathname);

  // 2. Lấy token (trong thực tế sẽ lấy từ cookies hoặc header)
  // Ở đây giả lập trạng thái đăng nhập bằng cách check một cookie tạm 'synap_session'
  const hasSession = request.cookies.has('synap_session');

  // 3. Logic điều hướng
  if (!hasSession && !isAuthRoute) {
    // Chưa đăng nhập mà vào các trang bảo vệ (/, /meetings, /settings...) -> Đá về login
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Cho phép vào trang auth kể cả khi đã có session (để có thể "đăng xuất" hoặc chuyển tài khoản)
  // Bỏ chặn hasSession && isAuthRoute

  // Cho phép đi tiếp nếu thỏa mãn điều kiện
  return NextResponse.next();

  // Cho phép đi tiếp nếu thỏa mãn điều kiện
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Bỏ qua các đường dẫn liên quan đến Next.js internals và static files:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, sitemap.xml, robots.txt (tệp meta)
     * - *.png, *.jpg, *.jpeg, *.svg, *.webp (hình ảnh trực tiếp)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
