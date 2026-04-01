import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Increase body limit so large audio/video uploads are proxied fully to backend
  experimental: {
    middlewareClientMaxBodySize: '300mb',
  },
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://localhost:8000/uploads/:path*',
      },
    ];
  },
};

export default nextConfig;
