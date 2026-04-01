import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/chat': 'http://localhost:8002',
      '/notes': 'http://localhost:8002',
      '/subsidy': 'http://localhost:8002',
      '/doctor-questions': 'http://localhost:8002',
      '/cycle-info': 'http://localhost:8002',
    },
  },
});
