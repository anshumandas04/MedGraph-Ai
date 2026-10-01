import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    allowedHosts: [
      'plc-testament-stephen-magnetic.trycloudflare.com',
      '.trycloudflare.com',
    ],
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
