import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteStaticCopy } from 'vite-plugin-static-copy';

const rootDir = path.dirname(fileURLToPath(import.meta.url));

const API_TARGET = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000';
const cesiumSource = 'node_modules/cesium/Build/Cesium';
const cesiumBaseUrl = 'cesiumStatic';

/** SPA paths that must not be forwarded to the FastAPI backend on hard refresh. */
const SPA_ROUTE_PATHS = new Set([
  '/',
  '/login',
  '/map',
  '/projects',
  '/upload',
  '/labeling',
  '/copilot',
  '/targeting',
  '/kriging',
  '/deposit',
  '/hydrogeology',
  '/urban',
  '/infrastructure',
  '/satellite',
  '/reports',
  '/financial',
  '/marketplace',
  '/digital-twin',
  '/ar',
  '/cloud-gpu',
  '/model-training',
  '/settings',
  '/admin',
  '/platform',
]);

function spaAwareProxy(context: string) {
  return {
    target: API_TARGET,
    changeOrigin: true,
    bypass(req: { url?: string }) {
      const pathname = (req.url || '').split('?')[0];
      if (SPA_ROUTE_PATHS.has(pathname)) {
        return '/index.html';
      }
      // `/hydro` must not swallow the `/hydrogeology` page route.
      if (context === '/hydro' && pathname.startsWith('/hydrogeology')) {
        return '/index.html';
      }
      return undefined;
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        { src: `${cesiumSource}/ThirdParty`, dest: cesiumBaseUrl },
        { src: `${cesiumSource}/Workers`, dest: cesiumBaseUrl },
        { src: `${cesiumSource}/Assets`, dest: cesiumBaseUrl },
        { src: `${cesiumSource}/Widgets`, dest: cesiumBaseUrl },
      ],
    }),
  ],
  define: {
    CESIUM_BASE_URL: JSON.stringify(`/${cesiumBaseUrl}`),
  },
  resolve: {
    alias: [
      {
        find: /^mersenne-twister$/,
        replacement: path.resolve(rootDir, 'src/shims/mersenne-twister.ts'),
      },
      // Redirect the bare ESM import of urijs to its CJS build so Vite's
      // esbuild pre-bundler can wrap it as a proper ESM default export.
      {
        find: /^urijs$/i,
        replacement: 'urijs/src/URI.js',
      },
    ],
  },
  optimizeDeps: {
    // Do NOT exclude cesium — exclusion prevents esbuild from resolving its
    // CJS transitive deps (urijs, mersenne-twister) and causes the
    // "does not provide an export named 'default'" crash at runtime.
    include: [
      'cesium',
      'urijs',
    ],
    needsInterop: [
      'mersenne-twister',
      'urijs',
    ],
  },
  server: {
    port: 5173,
    proxy: {
      '/health': API_TARGET,
      '/version': API_TARGET,
      '/auth': API_TARGET,
      '/projects': spaAwareProxy('/projects'),
      '/platform': spaAwareProxy('/platform'),
      '/dashboard': API_TARGET,
      '/deposit': spaAwareProxy('/deposit'),
      '/deposit-model': API_TARGET,
      '/financial': spaAwareProxy('/financial'),
      '/training': API_TARGET,
      '/copilot': spaAwareProxy('/copilot'),
      '/capture': API_TARGET,
      '/ingest': API_TARGET,
      '/instruments': API_TARGET,
      '/jobs': API_TARGET,
      '/reports': spaAwareProxy('/reports'),
      '/fuse-geodata': API_TARGET,
      '/fuse-spectral': API_TARGET,
      '/fuse-seismic': API_TARGET,
      '/classify-thin-section': API_TARGET,
      '/marketplace': spaAwareProxy('/marketplace'),
      '/mapping': API_TARGET,
      '/tiles': API_TARGET,
      '/hydro': spaAwareProxy('/hydro'),
      '/urban': spaAwareProxy('/urban'),
      '/infra': API_TARGET,
      '/satellite': spaAwareProxy('/satellite'),
      '/geobotany': API_TARGET,
      '/classification': API_TARGET,
    },
  },
});