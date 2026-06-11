import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';

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
  const [result, setResult] = useState<unknown>(null);
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

  return (
    <div>
      <h2>Cloud GPU Classification</h2>
      <p>
        CUDA-accelerated ResNet18 inference with mixed precision. Falls back to CPU when no GPU
        worker is attached.
      </p>
      {capabilities ? <pre>{JSON.stringify(capabilities, null, 2)}</pre> : null}
      <label>
        Task{' '}
        <select value={task} onChange={(event) => setTask(event.target.value as GpuTask)}>
          {TASKS.map((entry) => (
            <option key={entry} value={entry}>
              {entry}
            </option>
          ))}
        </select>
      </label>
      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.75rem' }}>
        <button type="button" onClick={() => run(true)} disabled={loading}>
          {loading ? 'Running...' : 'Sync classify'}
        </button>
        <button type="button" onClick={() => run(false)} disabled={loading}>
          Async job
        </button>
      </div>
      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {result ? <pre>{JSON.stringify(result, null, 2)}</pre> : null}
    </div>
  );
}