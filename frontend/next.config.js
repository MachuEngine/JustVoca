/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/auth/:path*", destination: "http://127.0.0.1:8000/auth/:path*" },
      { source: "/study/:path*", destination: "http://127.0.0.1:8000/study/:path*" },
      { source: "/user/:path*", destination: "http://127.0.0.1:8000/user/:path*" },
      { source: "/speech/:path*", destination: "http://127.0.0.1:8000/speech/:path*" },
      { source: "/admin/:path*", destination: "http://127.0.0.1:8000/admin/:path*" },

      // 네 백엔드가 실제로 쓰는 api prefix는 여기 두 개뿐
      { source: "/api/teacher/:path*", destination: "http://127.0.0.1:8000/api/teacher/:path*" },
      { source: "/api/notice/:path*", destination: "http://127.0.0.1:8000/api/notice/:path*" },

      // (선택) 프론트에서 /assets 를 직접 때리게 할 거면 추가
      // { source: "/assets/:path*", destination: "http://127.0.0.1:8000/assets/:path*" },
      // { source: "/files/:path*", destination: "http://127.0.0.1:8000/files/:path*" },
    ];
  },
};

module.exports = nextConfig;
