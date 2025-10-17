import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        // 在Docker环境中使用服务名，在本地开发中使用localhost
        target: process.env.DOCKER_ENV ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  build: {
    // 启用代码分割
    rollupOptions: {
      output: {
        // 手动分块策略
        manualChunks: {
          // 将React相关库分离到单独的chunk
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // 将UI库分离到单独的chunk
          'ui-vendor': ['antd', '@ant-design/icons', '@heroui/react'],
          // 将工具库分离到单独的chunk
          'utils-vendor': ['axios', 'date-fns', 'zustand'],
          // 将图表和可视化库分离到单独的chunk
          'viz-vendor': ['recharts', 'cytoscape', 'cytoscape-cola', 'cytoscape-cose-bilkent', 'cytoscape-dagre'],
          // 将查询库分离到单独的chunk
          'query-vendor': ['@tanstack/react-query'],
        },
      },
    },
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    // 启用源码映射（仅在开发环境）
    sourcemap: process.env.NODE_ENV === 'development',
    // 压缩配置
    minify: 'terser',
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      '@ant-design/icons',
      'axios',
      'zustand',
    ],
    exclude: [
      // 排除一些大型库，让它们按需加载
      'cytoscape',
      'cytoscape-cola',
      'cytoscape-cose-bilkent',
      'cytoscape-dagre',
    ],
  },

})