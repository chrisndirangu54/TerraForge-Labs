export type AppRoute = {
  path: string;
  page: string;
  domain: 'core' | 'geology' | 'hydrogeology' | 'urban' | 'infrastructure' | 'satellite' | 'admin';
  keyComponents: string[];
};

export const phase4Routes: AppRoute[] = [
  { path: '/', page: 'Dashboard', domain: 'core', keyComponents: ['Project summary cards', 'MRR metric', 'Recent activity feed'] },
  { path: '/map', page: 'Main Map', domain: 'core', keyComponents: ['MapLibre/Cesium map', 'Layer panel', 'Measurement tools'] },
  { path: '/projects', page: 'Projects', domain: 'core', keyComponents: ['Project list', 'Create', 'Archive'] },
  { path: '/upload', page: 'Data Upload', domain: 'core', keyComponents: ['Drag-drop upload', 'Instrument selector', 'GPS pairing'] },
  { path: '/kriging', page: 'Kriging Studio', domain: 'geology', keyComponents: ['Variogram', 'Run controls', 'Uncertainty view'] },
  { path: '/deposit', page: 'Deposit Model', domain: 'geology', keyComponents: ['Cesium 3D viewer', 'Block table', 'Resource summary'] },
  { path: '/hydrogeology', page: 'Hydrogeology', domain: 'hydrogeology', keyComponents: ['Groundwater model', 'Water table map', 'MODFLOW runner'] },
  { path: '/urban', page: 'Urban Planning', domain: 'urban', keyComponents: ['Settlement map', 'Land use', 'Service gaps'] },
  { path: '/infrastructure', page: 'Infrastructure', domain: 'infrastructure', keyComponents: ['Road network', 'Utilities', 'Pipeline routing'] },
  { path: '/satellite', page: 'Satellite Feeds', domain: 'satellite', keyComponents: ['Scene browser', 'Index calculator', 'Change detection'] },
  { path: '/reports', page: 'Reports', domain: 'core', keyComponents: ['JORC', 'NI 43-101', 'Kenya EL', 'CCS'] },
  { path: '/marketplace', page: 'Marketplace', domain: 'core', keyComponents: ['Catalogue', 'Stripe/M-Pesa', 'Install'] },
  { path: '/digital-twin', page: 'Digital Twin', domain: 'geology', keyComponents: ['4D viewer', 'Time slider', 'Alerts'] },
  { path: '/ar', page: 'AR Preview', domain: 'geology', keyComponents: ['WebXR launcher', 'Model selection'] },
  { path: '/settings', page: 'Settings', domain: 'admin', keyComponents: ['Account', 'Billing', 'API keys', 'Map provider'] },
  { path: '/admin', page: 'Admin', domain: 'admin', keyComponents: ['Users', 'Usage analytics', 'Audit log'] },
];
