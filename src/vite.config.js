import { defineConfig } from "vite";
import { resolve } from "path";

import tailwindcss from "@tailwindcss/vite";

import ViteRails from "vite-plugin-rails";

import vue from "@vitejs/plugin-vue";

process.env.VITE_RUBY_CONFIG_PATH = "vite_django_config.json";

const config = defineConfig({
  plugins: [
    ViteRails({
      fullReload: {
        // Reload Django templates and backend changes without watching generated
        // or dependency HTML files across the entire project tree.
        overridePaths: [
          "./**/*.py",
          "./templates/**/*.html",
          "./components/**/*.html",
        ],
        delay: 300,
      },
      compress: false,
    }),

    tailwindcss(),
    vue(),
  ],
  build: {
    rollupOptions: {
      input: {
        app: resolve(__dirname, "frontend/application/app.js"),
        trumbowyg: resolve(__dirname, "frontend/application/trumbowyg.js"),
      },
    },
  },
  server: {
    port: 3036,
    host: "0.0.0.0",

    // CRITICAL: Tell Vite its own public URL.
    // When Vite injects CSS as <style> tags via JS (HMR style injection), those
    // tags have no URL context. Any url() inside them — including FontAwesome
    // webfonts — becomes root-relative (/@fs/...). The browser then resolves
    // against the document origin (Django at localhost:8000), causing 404s.
    // Setting origin makes Vite emit ABSOLUTE URLs (http://localhost:3036/@fs/...)
    // so fonts always resolve to Vite's server regardless of the page's origin.
    origin: "http://localhost:3036",

    // CORS: Allow requests from both your remote server AND local development
    cors: {
      origin: [
        "https://159.65.234.156", // Your remote dev server (HTTPS)
        "http://localhost:8000", // Your local Django dev server
        "http://127.0.0.1:8000", // Your local Django dev server (alternate)
        "http://localhost:3036", // Your local Vite server
        "http://127.0.0.1:3036", // Your local Vite server (alternate)
      ],
      credentials: true,
    },
  },

  // CRITICAL: Prevent Vite from leaking your local file paths via /@fs/
  fs: {
    strict: true, // Forbid serving files outside the project root
    // If you absolutely MUST allow a specific external folder (not recommended):
    // allow: ['..'],
  },
});

export default config;
