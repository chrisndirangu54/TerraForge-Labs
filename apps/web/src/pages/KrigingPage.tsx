import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { JobStatusPanel } from '../components/capture/JobStatusPanel';
import { KrigingMapPreview } from '../components/kriging/KrigingMapPreview';
import { VariogramChart } from '../components/kriging/VariogramChart';
import { useProjectStore } from '../stores/projectStore';

type KrigingJob = {
  job_id: string;
  status: string;
  result?: Record<string, unknown>;
};

type VariogramAnalyzeResponse = {
  empirical: { lags: number[]; semivariance: number[] };
  fitted: { model: string; curve: Array<{ distance: number; gamma: number }> };
  cross_validation: { rmse: number; mae: number; bias: number; n_folds: number };
  error?: string;
  count?: number;
};

const VARIOGRAM_MODELS = ['spherical', 'exponential', 'gaussian', 'linear'] as const;

export function KrigingPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [element, setElement] = useState('ta_ppm');
  const [variogramModel, setVariogramModel] = useState<(typeof VARIOGRAM_MODELS)[number]>('spherical');
  const [gridResolution, setGridResolution] = useState(50);
  const [asyncMode, setAsyncMode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [cvLoading, setCvLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<KrigingJob | null>(null);
  const [variogram, setVariogram] = useState<VariogramAnalyzeResponse | null>(null);

  async function runCrossValidation() {
    setCvLoading(true);
    setError(null);
    try {
      const analysis = await apiPost<VariogramAnalyzeResponse>(
        '/geodata/variogram/cross-validate',
        {
          element,
          variogram_model: variogramModel,
          project_id: selectedProject?.id,
          dataset: 'matuu_synthetic',
        },
      );
      if (analysis.error) {
        setError(`Variogram CV needs more data (${analysis.count ?? 0} points)`);
        setVariogram(null);
      } else {
        setVariogram(analysis);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCvLoading(false);
    }
  }

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
        dataset: 'matuu_synthetic',
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

  const result = (job?.result ?? null) as Record<string, unknown> | null;

  return (
    <div>
      <h2>Kriging Studio</h2>
      <p>Fit variograms with leave-one-out cross-validation, run PyKrige, and preview COG tiles.</p>

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
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="button" onClick={runCrossValidation} disabled={cvLoading}>
            {cvLoading ? 'Analyzing...' : 'Run variogram CV'}
          </button>
          <button type="submit" disabled={loading}>
            {loading ? 'Running...' : 'Run kriging'}
          </button>
        </div>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}

      {variogram && !variogram.error ? (
        <section style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Variogram cross-validation</h3>
          <VariogramChart analysis={variogram} />
        </section>
      ) : null}

      {result ? (
        <section style={{ marginTop: '1.5rem', display: 'grid', gap: '1rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Kriging output</h3>
          {typeof result.cog_preview_url === 'string' ? (
            <KrigingMapPreview
              previewUrl={result.cog_preview_url}
              tileTemplate={
                typeof result.cog_tile_url_template === 'string'
                  ? result.cog_tile_url_template
                  : undefined
              }
              bounds={Array.isArray(result.stats) ? undefined : (result.stats as { bounds?: number[] })?.bounds}
            />
          ) : null}
          <JobStatusPanel job={job} title="Kriging job" />
        </section>
      ) : null}
    </div>
  );
}