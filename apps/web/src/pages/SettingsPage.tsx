import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { DataTable } from '../components/capture/DataTable';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

export function SettingsPage() {
  const [providerPlan, setProviderPlan] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    apiGet<Record<string, unknown>>('/mapping/provider-plan')
      .then(setProviderPlan)
      .catch(() => setProviderPlan(null));
  }, []);

  const rows = providerPlan
    ? Object.entries(providerPlan)
        .filter(([, v]) => typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')
        .map(([field, value]) => ({ field, value }))
    : [];

  return (
    <div>
      <PageHeader
        domain="admin"
        title="Settings"
        description="Account, billing, API keys, and map provider configuration."
      />

      <Card title="Map provider plan" subtitle="Tile and COG routing">
        {rows.length ? (
          <DataTable columns={['field', 'value']} rows={rows} />
        ) : (
          <p className="text-sm text-sediment-dim">Loading provider plan…</p>
        )}
      </Card>
    </div>
  );
}