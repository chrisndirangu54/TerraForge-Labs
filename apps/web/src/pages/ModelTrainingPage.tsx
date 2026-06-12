import { FormEvent, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';

type JobResponse = {
  job_id: string;
  status: string;
  result?: Record<string, unknown>;
};

type Manifest = {
  source?: string;
  samples?: number;
  sample_count?: number;
  classes?: string[] | number;
  n_bands?: number;
};

type CvReport = {
  models?: Record<
    string,
    {
      pooled_metrics?: { accuracy?: number; macro_f1?: number; top3_accuracy?: number };
      n_samples?: number;
      meets_threshold?: boolean;
    }
  >;
  error?: string;
};

const DOMAIN_TASKS = ['thin_section', 'spectral'] as const;
type DomainTask = (typeof DOMAIN_TASKS)[number];

function pct(value: number | undefined) {
  if (value === undefined) return 'n/a';
  return `${(value * 100).toFixed(1)}%`;
}

export function ModelTrainingPage() {
  const [task, setTask] = useState<DomainTask>('thin_section');
  const [epochs, setEpochs] = useState('6');
  const [cvFolds, setCvFolds] = useState('5');
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [cvReport, setCvReport] = useState<CvReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [pulling, setPulling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);

  async function refreshMeta() {
    try {
      const [manifestRes, cvRes] = await Promise.all([
        apiGet<Manifest>(`/training/${task}/manifest`),
        apiGet<CvReport>('/training/domain/eval'),
      ]);
      setManifest(manifestRes);
      setCvReport(cvRes);
    } catch {
      setManifest(null);
      setCvReport(null);
    }
  }

  useEffect(() => {
    refreshMeta();
  }, [task]);

  async function pullDatasets() {
    setPulling(true);
    setError(null);
    try {
      await apiPost('/training/datasets/pull', { async: false });
      await refreshMeta();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPulling(false);
    }
  }

  async function runTraining(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setJob(null);
    try {
      const started = await apiPost<JobResponse>(`/training/${task}/run`, {
        data_source: 'corpus',
        epochs: Number(epochs),
        cv_folds: Number(cvFolds),
        cv_epochs: Number(epochs),
        async: false,
      });
      setJob(started);
      if (started.job_id && started.status !== 'complete') {
        const polled = await apiGet<JobResponse>(`/jobs/${started.job_id}`);
        setJob(polled);
      }
      await refreshMeta();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const cvKey = task === 'thin_section' ? 'thin_section_cnn' : 'spectral_1d_cnn';
  const cvMetrics = cvReport?.models?.[cvKey];

  return (
    <div>
      <h2>Domain Model Training</h2>
      <p>
        Train thin-section (PPL/XPL) and spectral (USGS reflectance) CNNs with stratified
        cross-validation on thousands of labeled samples.
      </p>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <button type="button" onClick={pullDatasets} disabled={pulling}>
          {pulling ? 'Pulling corpora...' : 'Pull datasets (GBIF + thin-section + spectral)'}
        </button>
      </div>

      <form
        onSubmit={runTraining}
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
          Task
          <select value={task} onChange={(e) => setTask(e.target.value as DomainTask)}>
            {DOMAIN_TASKS.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </select>
        </label>
        <label>
          Epochs
          <input value={epochs} onChange={(e) => setEpochs(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          CV folds
          <input value={cvFolds} onChange={(e) => setCvFolds(e.target.value)} style={{ width: '100%' }} />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Training...' : 'Train + stratified CV'}
        </button>
      </form>

      {manifest ? (
        <section style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Dataset manifest</h3>
          <p style={{ margin: 0 }}>
            Source: {manifest.source ?? 'unknown'} — samples:{' '}
            {manifest.sample_count ?? manifest.samples ?? 'n/a'}
            {manifest.n_bands ? ` — bands: ${manifest.n_bands}` : ''}
          </p>
        </section>
      ) : null}

      {cvMetrics?.pooled_metrics ? (
        <section style={{ marginTop: '1rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Latest stratified CV</h3>
          <table style={{ borderCollapse: 'collapse' }}>
            <tbody>
              <tr>
                <td style={{ paddingRight: '1rem' }}>Accuracy</td>
                <td>{pct(cvMetrics.pooled_metrics.accuracy)}</td>
              </tr>
              <tr>
                <td style={{ paddingRight: '1rem' }}>Macro F1</td>
                <td>{pct(cvMetrics.pooled_metrics.macro_f1)}</td>
              </tr>
              <tr>
                <td style={{ paddingRight: '1rem' }}>Top-3</td>
                <td>{pct(cvMetrics.pooled_metrics.top3_accuracy)}</td>
              </tr>
              <tr>
                <td style={{ paddingRight: '1rem' }}>Samples</td>
                <td>{cvMetrics.n_samples ?? 'n/a'}</td>
              </tr>
            </tbody>
          </table>
        </section>
      ) : cvReport?.error ? (
        <p style={{ fontSize: '0.85rem' }}>No CV report yet — run training to generate one.</p>
      ) : null}

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {job ? (
        <details style={{ marginTop: '1rem' }}>
          <summary>Training job</summary>
          <pre style={{ fontSize: '0.8rem' }}>{JSON.stringify(job, null, 2)}</pre>
        </details>
      ) : null}
    </div>
  );
}