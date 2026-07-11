/** @type {import('next').NextConfig} */
const API = process.env.MARKETPLACE_API_URL || "http://127.0.0.1:8300";
module.exports = {
  reactStrictMode: false,
  // All /api/* calls proxy to the FastAPI backend. SSO route handlers live
  // under /sso/* so they never collide with the proxy.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};
