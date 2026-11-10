import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev proxy keeps the SPA and API on one origin, so the HTTP-only session cookie just works.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
})
