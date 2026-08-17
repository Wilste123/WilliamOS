import type { NextConfig } from "next";

const backendUrl = process.env.API_PROXY_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Keep /api/tasks/ etc. from 308→strip-slash→FastAPI 307→localhost:8000 (drops auth headers).
  skipTrailingSlashRedirect: true,
  // Allow ngrok / tunnel URLs when testing on phone (Next.js 15+)
  allowedDevOrigins: ["*.ngrok-free.app", "*.ngrok.io", "*.ngrok.app"],
  async rewrites() {
    // Browser calls /api/* → Next.js proxies to FastAPI on the dev machine.
    // Works on iPhone via ngrok without exposing localhost:8000 to the phone.
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
