type NavIconName =
  | 'dashboard'
  | 'map'
  | 'kriging'
  | 'deposit'
  | 'platform'
  | 'copilot'
  | 'upload'
  | 'financial'
  | 'reports'
  | 'training'
  | 'settings'
  | 'admin'
  | 'hydro'
  | 'urban'
  | 'infra'
  | 'satellite'
  | 'default';

type NavIconProps = {
  name: NavIconName;
  className?: string;
};

const paths: Record<NavIconName, string> = {
  dashboard:
    'M3 3h8v8H3V3zm10 0h8v5h-8V3zM3 13h5v8H3v-8zm7 3h11v5H10v-5z',
  map: 'M1 6l7-3 8 3 7-3v15l-7 3-8-3-7 3V6z',
  kriging:
    'M4 18V6l8 4 8-4v12M4 14l8 4 8-4',
  deposit: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  platform: 'M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z',
  copilot: 'M12 2a7 7 0 0 1 7 7c0 2.5-1.3 4.7-3.2 6L12 22l-3.8-7A7 7 0 0 1 12 2z',
  upload: 'M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2',
  financial: 'M12 2v20M17 7H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H7',
  reports: 'M6 4h9l3 3v13H6V4zm3 8h6m-6 4h6',
  training: 'M4 19V5l8-3 8 3v14l-8 3-8-3z',
  settings:
    'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm8-3a8 8 0 0 1-.2 1.8l2 1.5-2 3.5-2.4-1a8 8 0 0 1-1.5 1l-.4 2.6H9.5l-.4-2.6a8 8 0 0 1-1.5-1l-2.4 1-2-3.5 2-1.5A8 8 0 0 1 4 12a8 8 0 0 1 .2-1.8L2.2 8.7l2-3.5 2.4 1a8 8 0 0 1 1.5-1L8.5 2h7l.4 2.6a8 8 0 0 1 1.5 1l2.4-1 2 3.5-2 1.5c.1.6.2 1.2.2 1.8z',
  admin: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 9v-1a6 6 0 0 1 12 0v1H4z',
  hydro: 'M12 2.7c3.5 4.5 6 7.5 6 11a6 6 0 1 1-12 0c0-3.5 2.5-6.5 6-11z',
  urban: 'M3 21V9l9-4 9 4v12H3zm6-3h6v-6H9v6z',
  infra: 'M2 20h20M6 20V10l6-6 6 6v10',
  satellite: 'M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7L12 2z',
  default: 'M4 4h16v16H4V4z',
};

const pageToIcon: Record<string, NavIconName> = {
  Dashboard: 'dashboard',
  'Main Map': 'map',
  'Kriging Studio': 'kriging',
  'Deposit Model': 'deposit',
  'Platform Hub': 'platform',
  Copilot: 'copilot',
  'Field Upload': 'upload',
  'Financial Analysis': 'financial',
  Reports: 'reports',
  'Model Training': 'training',
  Settings: 'settings',
  Admin: 'admin',
  Hydrogeology: 'hydro',
  'Urban Planning': 'urban',
  Infrastructure: 'infra',
  'Satellite Feeds': 'satellite',
};

export function iconForPage(page: string): NavIconName {
  return pageToIcon[page] ?? 'default';
}

export function NavIcon({ name, className = '' }: NavIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`h-4 w-4 ${className}`}
      aria-hidden
    >
      <path d={paths[name]} />
    </svg>
  );
}