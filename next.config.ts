import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Increase body limit so large audio/video uploads are proxied fully to backend
  experimental: {
    proxyClientMaxBodySize: '300mb',
  },
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://localhost:8001/uploads/:path*',
      },
    ];
  },
};

export default nextConfig;
