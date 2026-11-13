import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" lets the built dist/ folder work on GitHub Pages or any static host
export default defineConfig({
  plugins: [react()],
  base: "./",
});
