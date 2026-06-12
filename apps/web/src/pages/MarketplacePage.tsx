import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { DataTable } from '../components/capture/DataTable';
import { StructuredJsonView } from '../components/results/StructuredJsonView';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

type MarketplaceItem = {
  id: string;
  name: string;
  description?: string;
  price_usd?: number;
  category?: string;
  formats?: string[];
  holes?: number;
  total_metres?: number;
};

type CatalogueResponse = {
  items: MarketplaceItem[];
  categories?: string[];
  drill_log_preview?: Array<Record<string, unknown>>;
};

const TABS = [
  { id: 'all', label: 'All' },
  { id: 'drill_log', label: 'Drill logs' },
  { id: 'report', label: 'Reports' },
  { id: 'plugin', label: 'Plugins' },
] as const;

export function MarketplacePage() {
  const [tab, setTab] = useState<(typeof TABS)[number]['id']>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [catalogue, setCatalogue] = useState<CatalogueResponse | null>(null);
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [drillPreview, setDrillPreview] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const query = tab === 'all' ? undefined : { category: tab };
    apiGet<CatalogueResponse>('/marketplace/catalogue', query)
      .then((response) => {
        setCatalogue(response);
        setItems(response.items ?? []);
        setDrillPreview(response.drill_log_preview ?? []);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [tab]);

  async function installItem(item: MarketplaceItem) {
    setMessage(null);
    setError(null);
    try {
      const result = await apiPost<{ installed?: boolean; status?: string }>(
        '/marketplace/install',
        { plugin_id: item.id },
      );
      setMessage(`Installed ${item.name}: ${result.status ?? result.installed}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function purchaseItem(item: MarketplaceItem) {
    setMessage(null);
    setError(null);
    try {
      const result = await apiPost<{ status?: string; receipt_id?: string }>(
        '/marketplace/checkout',
        {
          item_id: item.id,
          amount_usd: item.price_usd ?? 0,
          provider: 'stripe',
        },
      );
      setMessage(`Checkout ${item.name}: ${result.status} (${result.receipt_id})`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div>
      <PageHeader
        domain="platform"
        title="Marketplace"
        description="Drill logs, JORC report templates, and capture pipeline plugins."
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map((entry) => (
          <Button
            key={entry.id}
            variant={tab === entry.id ? 'primary' : 'secondary'}
            onClick={() => setTab(entry.id)}
          >
            {entry.label}
          </Button>
        ))}
      </div>

      {loading ? <p>Loading catalogue...</p> : null}
      {error ? <pre className="tf-error mb-6">{error}</pre> : null}
      {message ? <p className="mb-4 text-sm text-mineral-300">{message}</p> : null}

      {(tab === 'all' || tab === 'drill_log') && drillPreview.length > 0 ? (
        <Card title="Drill hole preview" className="mb-6">
          <DataTable
            columns={[
              'hole_id',
              'depth_m',
              'mean_ta_ppm',
              'lithology',
              'dip',
              'azimuth',
            ]}
            rows={drillPreview}
          />
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => {
          const isFree = (item.price_usd ?? 0) <= 0;
          const isPlugin = item.category === 'plugin';
          return (
            <Card
              key={item.id}
              title={item.name}
              subtitle={item.description}
              badge={
                <span className="text-xs text-ore-300">
                  {isFree ? 'Free' : `$${item.price_usd}`}
                </span>
              }
              footer={
                <div className="flex gap-2">
                  {isPlugin ? (
                    <Button variant="primary" onClick={() => installItem(item)}>
                      Install
                    </Button>
                  ) : isFree ? (
                    <Button variant="secondary" onClick={() => installItem(item)}>
                      Get
                    </Button>
                  ) : (
                    <Button variant="primary" onClick={() => purchaseItem(item)}>
                      Buy
                    </Button>
                  )}
                </div>
              }
            >
              <dl className="space-y-1 text-sm text-sediment-muted">
                <div>
                  <dt className="inline text-sediment-dim">Category: </dt>
                  <dd className="inline">{item.category ?? 'other'}</dd>
                </div>
                {item.formats?.length ? (
                  <div>
                    <dt className="inline text-sediment-dim">Formats: </dt>
                    <dd className="inline">{item.formats.join(', ')}</dd>
                  </div>
                ) : null}
                {item.holes != null ? (
                  <div>
                    <dt className="inline text-sediment-dim">Program: </dt>
                    <dd className="inline">
                      {item.holes} holes · {item.total_metres ?? '?'} m
                    </dd>
                  </div>
                ) : null}
              </dl>
            </Card>
          );
        })}
      </div>

      {catalogue ? (
        <Card title="Complete catalogue response" className="mt-6">
          <StructuredJsonView data={catalogue} />
        </Card>
      ) : null}
    </div>
  );
}