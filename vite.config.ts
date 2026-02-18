import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(() => {
  return {
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        // Dev convenience: allow the frontend to call the API without CORS/404 issues.
        // In docker, Nginx handles this proxying.
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    plugins: [react()],

    // IMPORTANT SECURITY NOTE:
    // Never embed provider API keys (Gemini/OpenAI/etc.) in the frontend bundle.
    // All AI calls MUST go through the backend.

    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
  };
});
