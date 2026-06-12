import { FormEvent, useEffect, useState } from 'react';
import { apiGet, apiPost, uploadTrainingData } from '../api/client';
import { CaptureResultView } from '../components/capture/CaptureResultView';
import { StructuredJsonView } from '../components/results/StructuredJsonView';
import { inferDisplay } from '../components/results/inferDisplay';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { useProjectStore } from '../stores/projectStore';

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
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [task, setTask] = useState<DomainTask>('thin_section');
  const [epochs, setEpochs] = useState('6');
  const [cvFolds, setCvFolds] = useState('5');
  const [className, setClassName] = useState('quartz');
  const [classes, setClasses] = useState<string[]>([]);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [cvReport, setCvReport] = useState<CvReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [pulling, setPulling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [uploadResult, setUploadResult] = useState<Record<string, unknown> | null>(null);
  const [pairFile, setPairFile] = useState<File | null>(null);
  const [pplFile, setPplFile] = useState<File | null>(null);
  const [xplFile, setXplFile] = useState<File | null>(null);
  const [spectralFile, setSpectralFile] = useState<File | null>(null);

  async function refreshMeta() {
    try {
      const [manifestRes, cvRes, classRes] = await Promise.all([
        apiGet<Manifest>(`/training/${task}/manifest`),
        apiGet<CvReport>('/training/domain/eval'),
        apiGet<{ classes: string[] }>(`/training/${task}/classes`),
      ]);
      setManifest(manifestRes);
      setCvReport(cvRes);
      setClasses(classRes.classes ?? []);
      if (classRes.classes?.length) {
        setClassName((current) =>
          classRes.classes.includes(current) ? current : classRes.classes[0],
        );
      }
    } catch {
      setManifest(null);
      setCvReport(null);
      setClasses([]);
    }
  }

  useEffect(() => {
    refreshMeta();
  }, [task]);

  async function pullDatasets() {
    setPulling(true);
    setError(null);
    try {
      await apiPost('/training/datasets/pull', { async: false, include_domain: true });
      await refreshMeta();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPulling(false);
    }
  }

  async function uploadDataset(event: FormEvent) {
    event.preventDefault();
    setUploading(true);
    setError(null);
    setUploadResult(null);
    try {
      const result = await uploadTrainingData(task, {
        className,
        projectId: selectedProject?.id,
        pairFile: pairFile ?? undefined,
        pplFile: pplFile ?? undefined,
        xplFile: xplFile ?? undefined,
        spectralFile: spectralFile ?? undefined,
      });
      setUploadResult(result);
      await refreshMeta();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
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
      <PageHeader
        domain="geology"
        title="Domain Model Training"
        description="Upload thin-section PPL/XPL pairs and USGS reflectance spectra, then train stratified CV domain CNNs."
        actions={
          <Button variant="secondary" onClick={pullDatasets} disabled={pulling}>
            {pulling ? 'Pulling...' : 'Pull corpora'}
          </Button>
        }
      />

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card title="Upload training sample">
          <form onSubmit={uploadDataset} className="space-y-4">
            <label className="block text-sm">
              Task
              <select
                value={task}
                onChange={(e) => setTask(e.target.value as DomainTask)}
                className="mt-1 w-full rounded border border-forge-600 bg-forge-900 px-2 py-2"
              >
                {DOMAIN_TASKS.map((entry) => (
                  <option key={entry} value={entry}>
                    {entry}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              Class label
              <select
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                className="mt-1 w-full rounded border border-forge-600 bg-forge-900 px-2 py-2"
              >
                {classes.map((entry) => (
                  <option key={entry} value={entry}>
                    {entry}
                  </option>
                ))}
              </select>
            </label>

            {task === 'spectral' ? (
              <label className="block text-sm">
                Reflectance file (.npy, .csv, .tsv, .json)
                <input
                  type="file"
                  accept=".npy,.csv,.tsv,.json"
                  className="mt-1 block w-full text-sm"
                  onChange={(e) => setSpectralFile(e.target.files?.[0] ?? null)}
                />
              </label>
            ) : (
              <>
                <label className="block text-sm">
                  PPL/XPL pair (.npy shape 2×H×W)
                  <input
                    type="file"
                    accept=".npy"
                    className="mt-1 block w-full text-sm"
                    onChange={(e) => setPairFile(e.target.files?.[0] ?? null)}
                  />
                </label>
                <p className="text-xs text-sediment-dim">Or upload separate images:</p>
                <label className="block text-sm">
                  PPL image
                  <input
                    type="file"
                    accept="image/*"
                    className="mt-1 block w-full text-sm"
                    onChange={(e) => setPplFile(e.target.files?.[0] ?? null)}
                  />
                </label>
                <label className="block text-sm">
                  XPL image
                  <input
                    type="file"
                    accept="image/*"
                    className="mt-1 block w-full text-sm"
                    onChange={(e) => setXplFile(e.target.files?.[0] ?? null)}
                  />
                </label>
              </>
            )}

            <Button type="submit" variant="primary" disabled={uploading}>
              {uploading ? 'Uploading...' : 'Upload to training corpus'}
            </Button>
          </form>
        </Card>

        <Card title="Train model">
          <form onSubmit={runTraining} className="space-y-4">
            <label className="block text-sm">
              Epochs
              <input
                value={epochs}
                onChange={(e) => setEpochs(e.target.value)}
                className="mt-1 w-full rounded border border-forge-600 bg-forge-900 px-2 py-2"
              />
            </label>
            <label className="block text-sm">
              CV folds
              <input
                value={cvFolds}
                onChange={(e) => setCvFolds(e.target.value)}
                className="mt-1 w-full rounded border border-forge-600 bg-forge-900 px-2 py-2"
              />
            </label>
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Training...' : `Train ${task}`}
            </Button>
          </form>

          {manifest ? (
            <p className="mt-4 text-sm text-sediment-muted">
              Source: {manifest.source ?? 'unknown'} — samples:{' '}
              {manifest.sample_count ?? manifest.samples ?? 'n/a'}
              {manifest.n_bands ? ` — bands: ${manifest.n_bands}` : ''}
            </p>
          ) : null}
        </Card>
      </div>

      {cvMetrics?.pooled_metrics ? (
        <Card title="Latest stratified CV" className="mb-6">
          <div className="grid gap-2 text-sm sm:grid-cols-2">
            <div>Accuracy: {pct(cvMetrics.pooled_metrics.accuracy)}</div>
            <div>Macro F1: {pct(cvMetrics.pooled_metrics.macro_f1)}</div>
            <div>Top-3: {pct(cvMetrics.pooled_metrics.top3_accuracy)}</div>
            <div>Samples: {cvMetrics.n_samples ?? 'n/a'}</div>
          </div>
        </Card>
      ) : null}

      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      {uploadResult ? (
        <Card title="Upload response" className="mb-6">
          <CaptureResultView display={inferDisplay(uploadResult)} fallback={uploadResult} />
        </Card>
      ) : null}

      {job ? (
        <Card title="Training job" className="mb-6">
          <StructuredJsonView data={job} />
        </Card>
      ) : null}

      {manifest ? (
        <Card title="Dataset manifest">
          <StructuredJsonView data={manifest} />
        </Card>
      ) : null}
    </div>
  );
}