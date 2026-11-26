import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, any request to /api is forwarded to the backend.
// This means the website never has to worry about CORS or the backend address.
const backend = process.env.VITE_PROXY_TARGET || process.env.VITE_API_BASE_URL || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: backend, changeOrigin: true },
      "/uploads": { target: backend, changeOrigin: true },
      "/media": { target: backend, changeOrigin: true },
      "/officer": { target: backend, changeOrigin: true },
      "/complaints": { target: backend, changeOrigin: true },
      "/stats": { target: backend, changeOrigin: true },
      "/notifications": { target: backend, changeOrigin: true },
    },
  },
});
