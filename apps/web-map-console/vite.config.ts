import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // base "/" wajib untuk SPA di Cloud Run + nginx. base "./" memakai relative
  // path yang memecah asset URL saat operator buka deep-link / refresh route.
  base: "/",
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("maplibre-gl")) {
            return "maplibre";
          }
          if (id.includes("node_modules/react") || id.includes("node_modules/zustand")) {
            return "react";
          }
          return undefined;
        }
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      "/v1": "http://localhost:8000"
    }
  }
});
