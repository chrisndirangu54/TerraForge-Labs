import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type JobResponse = {
  job_id: string;
  status: string;
  result?: Record<string, unknown>;
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

  return (
    <div>
      <h2>Reports</h2>
      <p>JORC and NI 43-101 report workflow with async job polling.</p>

      <form
        onSubmit={generateReport}
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
          Report type
          <select value={reportType} onChange={(e) => setReportType(e.target.value as 'jorc' | 'ni43101')}>
            <option value="jorc">JORC</option>
            <option value="ni43101">NI 43-101</option>
          </select>
        </label>
        <label>
          Project name
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            style={{ width: '100%' }}
          />
        </label>
        <label>
          Commodity
          <input value={commodity} onChange={(e) => setCommodity(e.target.value)} style={{ width: '100%' }} />
        </label>
        {selectedProject ? (
          <p style={{ fontSize: '0.85rem', margin: 0 }}>
            Linked project: {selectedProject.name} ({selectedProject.slug})
          </p>
        ) : null}
        <button type="submit" disabled={loading}>
          {loading ? 'Generating...' : 'Generate report'}
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {job ? (
        <section style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Job status</h3>
          <pre>{JSON.stringify(job, null, 2)}</pre>
        </section>
      ) : null}
    </div>
  );
}