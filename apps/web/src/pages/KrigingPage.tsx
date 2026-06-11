import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type KrigingJob = {
  job_id: string;
  status: string;
  result?: Record<string, unknown>;
};

const VARIOGRAM_MODELS = ['spherical', 'exponential', 'gaussian', 'linear'] as const;

export function KrigingPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [element, setElement] = useState('ta_ppm');
  const [variogramModel, setVariogramModel] = useState<(typeof VARIOGRAM_MODELS)[number]>('spherical');
  const [gridResolution, setGridResolution] = useState(50);
  const [asyncMode, setAsyncMode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<KrigingJob | null>(null);

  async function runKriging(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setJob(null);
    try {
      const started = await apiPost<KrigingJob>('/fuse-geodata', {
        element,
        variogram_model: variogramModel,
        grid_resolution_m: gridResolution,
        project_id: selectedProject?.id,
        async: asyncMode,
      });
      if (asyncMode && started.job_id) {
        const polled = await apiGet<KrigingJob>(`/jobs/${started.job_id}`);
        setJob(polled);
      } else {
        setJob(started);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Kriging Studio</h2>
      <p>Configure variogram parameters and run the kriging pipeline.</p>

      <form
        onSubmit={runKriging}
        style={{
          display: 'grid',
          gap: '0.75rem',
          maxWidth: 480,
          padding: '1rem',
          border: '1px solid #ddd',
          borderRadius: 6,
        }}
      >
        <label>
          Element field
          <input value={element} onChange={(e) => setElement(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Variogram model
          <select
            value={variogramModel}
            onChange={(e) => setVariogramModel(e.target.value as (typeof VARIOGRAM_MODELS)[number])}
          >
            {VARIOGRAM_MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
        <label>
          Grid resolution (m)
          <input
            type="number"
            min={10}
            max={500}
            value={gridResolution}
            onChange={(e) => setGridResolution(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <input type="checkbox" checked={asyncMode} onChange={(e) => setAsyncMode(e.target.checked)} />
          Run as async job
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Running...' : 'Run kriging'}
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {job ? (
        <section style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Pipeline output</h3>
          <pre>{JSON.stringify(job, null, 2)}</pre>
        </section>
      ) : null}
    </div>
  );
}