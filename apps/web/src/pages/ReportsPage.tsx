import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { JobStatusPanel } from '../components/capture/JobStatusPanel';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { useProjectStore } from '../stores/projectStore';

type JobResponse = {
  job_id: string;
  status: string;
  result?: Record<string, unknown>;
  display?: Record<string, unknown>;
};

export function ReportsPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [projectName, setProjectName] = useState('TerraForge Demo');
  const [commodity, setCommodity] = useState('Ta');
  const [reportType, setReportType] = useState<'jorc' | 'ni43101'>('jorc');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);

  async function generateReport(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setJob(null);
    try {
      const started = await apiPost<JobResponse>('/reports/jorc', {
        project_name: projectName,
        commodity,
        report_type: reportType,
        project_id: selectedProject?.id,
        async: false,
      });
      setJob(started);
      if (started.job_id && started.status !== 'complete') {
        const polled = await apiGet<JobResponse>(`/jobs/${started.job_id}`);
        setJob(polled);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const reportUrl =
    job?.result && typeof job.result.report_url === 'string'
      ? job.result.report_url
      : job?.result && typeof job.result.pdf_url === 'string'
        ? job.result.pdf_url
        : null;

  return (
    <div>
      <PageHeader
        domain="core"
        title="Reports"
        description="JORC and NI 43-101 report workflow with structured job output."
      />

      <Card title="Generate report" className="max-w-lg">
        <form onSubmit={generateReport} className="space-y-4">
          <label className="block">
            <span className="tf-label mb-2 block">Report type</span>
            <select
              className="tf-input"
              value={reportType}
              onChange={(e) => setReportType(e.target.value as 'jorc' | 'ni43101')}
            >
              <option value="jorc">JORC</option>
              <option value="ni43101">NI 43-101</option>
            </select>
          </label>
          <label className="block">
            <span className="tf-label mb-2 block">Project name</span>
            <input className="tf-input" value={projectName} onChange={(e) => setProjectName(e.target.value)} />
          </label>
          <label className="block">
            <span className="tf-label mb-2 block">Commodity</span>
            <input className="tf-input" value={commodity} onChange={(e) => setCommodity(e.target.value)} />
          </label>
          {selectedProject ? (
            <p className="font-mono text-xs text-sediment-muted">
              Linked project: {selectedProject.name}
            </p>
          ) : null}
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? 'Generating…' : 'Generate report'}
          </Button>
        </form>
      </Card>

      {error ? <pre className="tf-error mt-6">{error}</pre> : null}
      {job ? (
        <Card title="Report job" className="mt-6">
          {reportUrl ? (
            <p className="mb-4">
              <a href={reportUrl} className="tf-link-ore" target="_blank" rel="noreferrer">
                Download report PDF →
              </a>
            </p>
          ) : null}
          <JobStatusPanel job={job as Record<string, unknown>} />
        </Card>
      ) : null}
    </div>
  );
}