import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { JobStatusPanel } from '../components/capture/JobStatusPanel';
import { DataTable } from '../components/capture/DataTable';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';

const TASKS = [
  'mineral',
  'geobotany',
  'thin_section',
  'spectral',
  'grain_segmentation',
] as const;

type GpuTask = (typeof TASKS)[number];

export function CloudGpuPage() {
  const [task, setTask] = useState<GpuTask>('mineral');
  const [capabilities, setCapabilities] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiGet<Record<string, unknown>>('/classification/gpu/capabilities')
      .then(setCapabilities)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  async function run(sync: boolean) {
    setLoading(true);
    setError(null);
    try {
      const path = sync ? '/classification/gpu/sync' : '/classification/gpu';
      const response = await apiPost<Record<string, unknown>>(path, {
        task,
        project_id: 'web-demo',
        async: !sync,
      });
      if (!sync && response.job_id) {
        const polled = await apiGet<Record<string, unknown>>(`/jobs/${response.job_id}`);
        setResult(polled);
      } else {
        setResult(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const capRows = capabilities
    ? Object.entries(capabilities)
        .filter(([, v]) => typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')
        .map(([field, value]) => ({ field, value }))
    : [];

  return (
    <div>
      <PageHeader
        domain="geology"
        title="Cloud GPU"
        description="CUDA classification for mineral, geobotany, thin-section, and spectral CNNs."
      />

      {capabilities ? (
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Accelerator"
            value={capabilities.cuda_available ? 'GPU' : 'CPU'}
            hint={String(capabilities.device_name ?? '')}
            accent="mineral"
          />
          <StatCard label="Tasks" value={String(TASKS.length)} accent="ore" />
          <StatCard label="Batch" value={capabilities.batch_supported ? 'Yes' : 'No'} accent="moss" />
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="GPU capabilities">
          {capRows.length ? (
            <DataTable columns={['field', 'value']} rows={capRows} />
          ) : (
            <p className="text-sm text-sediment-dim">Loading…</p>
          )}
        </Card>

        <Card title="Run classification">
          <label className="tf-label mb-2 block">Task</label>
          <select className="tf-input mb-4" value={task} onChange={(e) => setTask(e.target.value as GpuTask)}>
            {TASKS.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <Button variant="primary" onClick={() => run(true)} disabled={loading}>
              {loading ? 'Running…' : 'Sync classify'}
            </Button>
            <Button variant="secondary" onClick={() => run(false)} disabled={loading}>
              Async job
            </Button>
          </div>
        </Card>
      </div>

      {error ? <pre className="tf-error mt-6">{error}</pre> : null}
      {result ? (
        <Card title="Classification result" className="mt-6">
          <JobStatusPanel job={result} />
        </Card>
      ) : null}
    </div>
  );
}