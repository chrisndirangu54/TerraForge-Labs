import { FormEvent, useState } from 'react';
import { apiPost } from '../api/client';
import { CaptureResultView } from '../components/capture/CaptureResultView';
import { StructuredJsonView } from '../components/results/StructuredJsonView';
import { inferDisplay } from '../components/results/inferDisplay';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { useProjectStore } from '../stores/projectStore';

type TwinResponse = {
  npv_band_usd?: { p10?: number; p50?: number; p90?: number };
  commodity?: string;
  grade_ta_ppm?: number;
  alerts?: string[];
  price_feed?: string;
};

export function DigitalTwinPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [commodity, setCommodity] = useState('ta');
  const [oreTonnes, setOreTonnes] = useState('3000000');
  const [priceShock, setPriceShock] = useState(-8);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TwinResponse | null>(null);

  async function runTwin(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<TwinResponse>('/platform/digital-twin/live-npv', {
        commodity,
        ore_tonnes: Number(oreTonnes),
        price_shock_pct: priceShock,
        project_id: selectedProject?.id,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader
        domain="geology"
        title="Digital Twin"
        description="Live NPV twin with commodity price shock bands and deposit alerts."
      />

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card title="NPV twin controls">
          <form onSubmit={runTwin} className="space-y-4">
            <label className="block text-sm">
              Commodity
              <input
                value={commodity}
                onChange={(e) => setCommodity(e.target.value)}
                className="mt-1 w-full rounded border border-forge-600 bg-forge-900 px-2 py-2"
              />
            </label>
            <label className="block text-sm">
              Ore tonnes
              <input
                value={oreTonnes}
                onChange={(e) => setOreTonnes(e.target.value)}
                className="mt-1 w-full rounded border border-forge-600 bg-forge-900 px-2 py-2"
              />
            </label>
            <label className="block text-sm">
              Price shock ({priceShock}%)
              <input
                type="range"
                min={-30}
                max={30}
                value={priceShock}
                onChange={(e) => setPriceShock(Number(e.target.value))}
                className="mt-2 w-full"
              />
            </label>
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Running...' : 'Run live NPV twin'}
            </Button>
          </form>
        </Card>

        {result?.npv_band_usd ? (
          <Card title="NPV band (USD)">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="tf-stat-card">
                <p className="tf-label">P10</p>
                <p className="mt-1 font-mono text-lg">${result.npv_band_usd.p10}</p>
              </div>
              <div className="tf-stat-card border-l-ore-500/60">
                <p className="tf-label">P50</p>
                <p className="mt-1 font-mono text-lg text-ore-300">${result.npv_band_usd.p50}</p>
              </div>
              <div className="tf-stat-card">
                <p className="tf-label">P90</p>
                <p className="mt-1 font-mono text-lg">${result.npv_band_usd.p90}</p>
              </div>
            </div>
            {result.alerts?.length ? (
              <ul className="mt-4 space-y-2 text-sm text-sediment-muted">
                {result.alerts.map((alert) => (
                  <li key={alert}>• {alert}</li>
                ))}
              </ul>
            ) : null}
          </Card>
        ) : null}
      </div>

      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      {result ? (
        <Card title="Twin response" className="mb-6">
          <CaptureResultView display={inferDisplay(result)} fallback={result} />
          <div className="mt-4">
            <StructuredJsonView data={result} />
          </div>
        </Card>
      ) : null}
    </div>
  );
}