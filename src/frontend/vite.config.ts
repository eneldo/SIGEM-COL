import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src/frontend'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: false,
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    restoreMocks: true,
    unstubGlobals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      exclude: [
        'dist/**',
        'coverage/**',
        '**/node_modules/**',
        '**/*.d.ts',
        'src/**/*.test.ts',
        'src/**/*.test.tsx',
        'src/test/**',
        'src/vite-env.d.ts',
        'src/main.tsx',
        'src/lib/types.ts',
        '**/*.config.js',
        '**/*.config.ts',
        'postcss.config.js',
        'tailwind.config.js',
      ],
      thresholds: {
        lines: 17,
        statements: 17,
        functions: 85,
        branches: 90,
        'src/components/EvidencePreview.tsx': { lines: 80 },
        'src/components/EvidenciasModal.tsx': { lines: 80 },
        'src/components/ui/*.tsx': { lines: 80 },
        'src/lib/api.ts': { lines: 80 },
        'src/stores/authStore.ts': { lines: 80 },
        'src/pages/auth/LoginPage.tsx': { lines: 80 },
        'src/pages/auth/ChangePasswordPage.tsx': { lines: 80 },
      },
    },
  },
})
