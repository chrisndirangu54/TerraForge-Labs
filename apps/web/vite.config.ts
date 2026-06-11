import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://localhost:8000',
      '/version': 'http://localhost:8000',
      '/instruments': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/fuse-geodata': 'http://localhost:8000',
      '/fuse-spectral': 'http://localhost:8000',
      '/fuse-seismic': 'http://localhost:8000',
      '/classify-thin-section': 'http://localhost:8000',
      '/marketplace': 'http://localhost:8000',
      '/mapping': 'http://localhost:8000',
      '/tiles': 'http://localhost:8000',
      '/hydro': 'http://localhost:8000',
      '/urban': 'http://localhost:8000',
      '/infra': 'http://localhost:8000',
      '/satellite': 'http://localhost:8000',
      '/geobotany': 'http://localhost:8000',
    },
  },
});