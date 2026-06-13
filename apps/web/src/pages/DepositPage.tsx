import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiGet, apiPost } from '../api/client';
import { DepositCesiumViewer, type DepositBlock } from '../components/geology/DepositCesiumViewer';
import { JobStatusPanel } from '../components/capture/JobStatusPanel';
import { DataTable } from '../components/capture/DataTable';
import { StructuredJsonView } from '../components/results/StructuredJsonView';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { useProjectStore } from '../stores/projectStore';

type DepositSummary = {
  ore_tonnes_estimate?: number;
  mean_grade_ta_ppm?: number;
  block_count?: number;
  blocks_preview?: DepositBlock[];
  centre?: { lon: number; lat: number; elevation_m?: number };
  mesh_url?: string;
  source?: string;
  [key: string]: unknown;
};

function extractBlocks(job: Record<string, unknown> | null): DepositBlock[] | null {
  if (!job) return null;
  const result = job.result;
  if (result && typeof result === 'object' && Array.isArray((result as DepositSummary).blocks_preview)) {
    return (result as DepositSummary).blocks_preview as DepositBlock[];
  }
  if (Array.isArray(job.blocks_preview)) {
    return job.blocks_preview as DepositBlock[];
  }
  return null;
}

async function pollJob(jobId: string, attempts = 20): Promise<Record<string, unknown>> {
  for (let i = 0; i < attempts; i += 1) {
    const job = await apiGet<Record<string, unknown>>(`/jobs/${jobId}`);
    const status = String(job.status ?? '');
    if (status === 'complete' || status === 'failed') {
      return job;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return apiGet<Record<string, unknown>>(`/jobs/${jobId}`);
}

export function DepositPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [summary, setSummary] = useState<DepositSummary | null>(null);
  const [job, setJob] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  async function refreshSummary() {
    const params = selectedProject?.id ? { project_id: selectedProject.id } : undefined;
    const refreshed = await apiGet<DepositSummary>('/deposit/summary', params);
    setSummary(refreshed);
    return refreshed;
  }

  useEffect(() => {
    setLoading(true);
    refreshSummary()
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [selectedProject?.id]);

  async function generateModel() {
    setGenerating(true);
    setError(null);
    try {
      const started = await apiPost<Record<string, unknown>>('/deposit-model', {
        project_id: selectedProject?.id,
        async: false,
      });

      let nextJob = started;
      if (started.job_id && started.status !== 'complete') {
        nextJob = await pollJob(String(started.job_id));
      }
      setJob(nextJob);

      const jobBlocks = extractBlocks(nextJob);
      const refreshed = await refreshSummary();
      const result = nextJob.result;
      const resultSummary =
        result && typeof result === 'object'
          ? (result as { summary?: DepositSummary }).summary
          : undefined;

      const jobResult =
        result && typeof result === 'object' ? (result as DepositSummary) : undefined;

      setSummary({
        ...refreshed,
        ...(resultSummary ?? {}),
        blocks_preview: jobBlocks?.length ? jobBlocks : refreshed.blocks_preview,
        mesh_url: jobResult?.mesh_url ?? refreshed.mesh_url,
        centre: resultSummary?.centre ?? refreshed.centre,
        block_count:
          resultSummary?.block_count ??
          jobBlocks?.length ??
          refreshed.block_count,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setGenerating(false);
    }
  }

  const summaryRows = summary
    ? Object.entries(summary)
        .filter(([, value]) => ['string', 'number', 'boolean'].includes(typeof value))
        .map(([field, value]) => ({ field, value }))
    : [];

  const blockRows = summary?.blocks_preview ?? extractBlocks(job) ?? [];

  return (
    <div>
      <PageHeader
        domain="geology"
        title="Deposit Model"
        description="3D block model viewer, resource summary, and link to ore financials."
        actions={
          <Button variant="primary" onClick={generateModel} disabled={generating}>
            {generating ? 'Generating…' : 'Generate deposit model'}
          </Button>
        }
      />

      {selectedProject ? (
        <p className="mb-4 font-mono text-sm text-sediment-muted">
          Project: <span className="text-ore-300">{selectedProject.name}</span>
        </p>
      ) : null}

      {error ? <pre className="tf-error mb-2">{error}</pre> : null}
      {error && (error.includes('401') || error.includes('Authentication')) ? (
        <p className="tf-error mb-6 text-sm">
          Sign in at <Link to="/login" className="tf-link">/login</Link> to generate models.
        </p>
      ) : null}
      {loading ? <p className="mb-4 text-sediment-muted">Loading deposit summary…</p> : null}

      {!loading || blockRows.length > 0 ? (
        <DepositCesiumViewer
          blocks={blockRows}
          centre={summary?.centre}
          meshUrl={summary?.mesh_url}
          className="mb-6 h-[420px] w-full"
        />
      ) : null}

      {summary ? (
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Ore tonnes"
            value={String(summary.ore_tonnes_estimate ?? 'n/a')}
            accent="ore"
          />
          <StatCard
            label="Mean grade"
            value={
              summary.mean_grade_ta_ppm != null
                ? `${summary.mean_grade_ta_ppm} ppm Ta`
                : 'n/a'
            }
            accent="strata"
          />
          <StatCard
            label="Blocks"
            value={String(summary.block_count ?? blockRows.length)}
            accent="mineral"
          />
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        {summary ? (
          <Card title="Resource summary">
            <DataTable columns={['field', 'value']} rows={summaryRows} />
          </Card>
        ) : null}
        {job ? (
          <Card title="Latest job">
            <JobStatusPanel job={job} />
          </Card>
        ) : null}
      </div>

      {blockRows.length ? (
        <Card title="Block model preview" className="mt-6">
          <DataTable
            columns={['lon', 'lat', 'elevation_m', 'ta_ppm_mean', 'unit']}
            rows={blockRows}
          />
        </Card>
      ) : null}

      {summary ? (
        <Card title="Complete deposit summary" className="mt-6">
          <StructuredJsonView data={summary} />
        </Card>
      ) : null}

      <p className="mt-6 text-sm text-sediment-muted">
        <Link to="/financial" className="tf-link-ore">
          Open ore financials →
        </Link>{' '}
        to run NPV using deposit tonnes and grade.
      </p>
    </div>
  );
}