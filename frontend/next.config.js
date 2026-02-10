/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/auth/:path*", destination: "http://127.0.0.1:8000/auth/:path*" },
      { source: "/study/:path*", destination: "http://127.0.0.1:8000/study/:path*" },
      { source: "/user/:path*", destination: "http://127.0.0.1:8000/user/:path*" },
      { source: "/speech/:path*", destination: "http://127.0.0.1:8000/speech/:path*" },
      { source: "/admin/:path*", destination: "http://127.0.0.1:8000/admin/:path*" },
      { source: "/api/teacher/:path*", destination: "http://127.0.0.1:8000/api/teacher/:path*" },
      { source: "/api/notice/:path*", destination: "http://127.0.0.1:8000/api/notice/:path*" },
      { source: "/api/chat/:path*", destination: "http://127.0.0.1:8000/api/chat/:path*" },
    ];
  },
};

module.exports = nextConfig;
