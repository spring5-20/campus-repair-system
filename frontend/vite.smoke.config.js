import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

/**
 * 冒烟测试专用构建配置：
 * 将 scripts/smoke.jsx 以 SSR 方式打包（处理 JSX），
 * jsdom 保持外部依赖，产物由 Node 直接执行。
 */
export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    ssr: 'scripts/smoke.jsx',
    outDir: 'work/smoke-out',
    emptyOutDir: true,
  },
  ssr: {
    external: ['jsdom'],
  },
});
