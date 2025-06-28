import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      // Enable reactivity transform for better performance
      reactivityTransform: true,
    }),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  
  // Development server configuration
  server: {
    port: 5173,
    host: true, // Allow external access
    open: true, // Open browser automatically
    cors: true, // Enable CORS for API calls
    proxy: {
      // Proxy API calls to backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  
  // Build configuration
  build: {
    target: 'esnext', // Modern browsers
    minify: 'terser',
    sourcemap: false, // Disable sourcemaps in production
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor libraries
          vendor: ['vue'],
          axios: ['axios']
        }
      }
    },
    // Optimize dependencies
    optimizeDeps: {
      include: ['vue', 'axios']
    }
  },
  
  // Preview configuration
  preview: {
    port: 4173,
    host: true
  },
  
  // Environment variables
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false
  }
})
