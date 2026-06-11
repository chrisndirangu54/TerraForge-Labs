import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';

export function DashboardPage() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Record<string, unknown>>('/health')
      .then(setHealth)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Connected React web shell for the TerraForge FastAPI backend.</p>
      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {health ? <pre>{JSON.stringify(health, null, 2)}</pre> : <p>Checking backend health...</p>}
    </div>
  );
}