import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  root: process.cwd(),
  server: {
    port: 5173,
    host: true
  },
  build: {
    rollupOptions: {
      input: resolve(__dirname, 'index.html')
    }
  }
})