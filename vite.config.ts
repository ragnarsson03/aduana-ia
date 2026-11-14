import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const stripExternalErrorUrls = () => ({
  name: 'strip-external-error-urls',
  renderChunk(code: string) {
    return code.replace(/https?:\/\/reactjs\.org\/docs\/error-decoder\.html\?invariant=/g, 'react-invariant:')
  },
})

// Air-Gapped build configuration
export default defineConfig({
  plugins: [react(), stripExternalErrorUrls()],
  base: './',
  build: {
    outDir: 'static',
    emptyOutDir: false,
    assetsDir: 'assets',
    sourcemap: false,
  },
  server: {
    port: 3000,
    open: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  }
})
