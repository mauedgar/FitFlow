import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;
          if (/[\\/]node_modules[\\/]@chakra-ui[\\/]/.test(id)) return 'chakra-ui';
          if (/[\\/]node_modules[\\/]@emotion[\\/]/.test(id)) return 'emotion';
          if (/[\\/]node_modules[\\/]framer-motion[\\/]/.test(id)) return 'motion';
          if (/[\\/]node_modules[\\/]react-icons[\\/]/.test(id)) return 'icons';
          if (/[\\/]node_modules[\\/]@tanstack[\\/]/.test(id)) return 'query';
        },
      },
    },
  },
})
