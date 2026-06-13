declare global {
  interface Window {
    CESIUM_BASE_URL?: string;
  }
}

const base = import.meta.env.BASE_URL || '/';
const normalizedBase = base.endsWith('/') ? base : `${base}/`;

if (typeof window !== 'undefined' && !window.CESIUM_BASE_URL) {
  window.CESIUM_BASE_URL = `${normalizedBase}cesiumStatic`;
}

export {};