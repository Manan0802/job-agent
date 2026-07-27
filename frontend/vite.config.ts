import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  build: {
    // FastAPI serves this, so a single `uvicorn` command runs the whole app.
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    // In dev the API stays on the backend port; paths are same-origin either way.
    proxy: { "/api": "http://localhost:8000" },
  },
});
