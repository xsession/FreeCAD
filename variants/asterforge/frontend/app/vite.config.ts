import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 550,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/three")) {
            return "three";
          }

          if (id.includes("node_modules/react")) {
            return "react-vendor";
          }
        }
      }
    }
  },
  server: {
    port: 4173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:4180",
        changeOrigin: true
      }
    }
  }
});
