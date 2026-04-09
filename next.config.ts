import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Increase body limit so large audio/video uploads are proxied fully to backend
  experimental: {
    proxyClientMaxBodySize: '300mb',
  },
  rewrites: async () => {
    return [
      {
        source: '/api/meetings',
        destination: 'http://127.0.0.1:8010/meetings/',
      },
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8010/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://127.0.0.1:8010/uploads/:path*',
      },
    ];
  },
};

export default nextConfig;
