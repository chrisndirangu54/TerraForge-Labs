import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Cartesian3, Viewer } from 'cesium';
import { apiGet, apiPost } from '../api/client';
import { JobStatusPanel } from '../components/capture/JobStatusPanel';
import { DataTable } from '../components/capture/DataTable';
import { StructuredJsonView } from '../components/results/StructuredJsonView';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
import { useProjectStore } from '../stores/projectStore';

export function DepositPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const cesiumRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [job, setJob] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Record<string, unknown>>('/deposit/summary')
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  useEffect(() => {
    if (!cesiumRef.current || viewerRef.current) return undefined;
    try {
      const viewer = new Viewer(cesiumRef.current, {
        animation: false,
        timeline: false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
      });
      viewer.camera.setView({
        destination: Cartesian3.fromDegrees(37.5, -1.15, 25000),
      });
      viewerRef.current = viewer;
    } catch {
      // Cesium may fail without ion token.
    }
    return () => {
      viewerRef.current?.destroy();
      viewerRef.current = null;
    };
  }, []);

  async function generateModel() {
    setError(null);
    try {
      const started = await apiPost<Record<string, unknown>>('/deposit-model', {
        project_id: selectedProject?.id,
        async: false,
      });
      let job = started;
      if (started.job_id && started.status !== 'complete') {
        job = await apiGet<Record<string, unknown>>(`/jobs/${started.job_id}`);
      }
      setJob(job);
      const refreshed = await apiGet<Record<string, unknown>>('/deposit/summary');
      setSummary(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const summaryRows = summary
    ? Object.entries(summary)
        .filter(([, v]) => typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean')
        .map(([field, value]) => ({ field, value }))
    : [];

  const blockRows = Array.isArray(summary?.blocks_preview)
    ? (summary.blocks_preview as Array<Record<string, unknown>>)
    : [];

  return (
    <div>
      <PageHeader
        domain="geology"
        title="Deposit Model"
        description="Block model summary, Cesium 3D viewer, and link to ore financials."
        actions={
          <Button variant="primary" onClick={generateModel}>
            Generate deposit model
          </Button>
        }
      />

      {selectedProject ? (
        <p className="mb-4 font-mono text-sm text-sediment-muted">
          Project: <span className="text-ore-300">{selectedProject.name}</span>
        </p>
      ) : null}

      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      <div
        ref={cesiumRef}
        className="mb-6 h-[360px] w-full overflow-hidden rounded-lg border border-forge-600 shadow-glow"
      />

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
          <StatCard label="Blocks" value={String(summary.block_count ?? 'n/a')} accent="mineral" />
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
            columns={['x', 'y', 'z', 'ta_ppm_mean', 'unit']}
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