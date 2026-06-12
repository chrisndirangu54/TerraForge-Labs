import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { DataTable } from '../components/capture/DataTable';
import { StatCard } from '../components/ui/StatCard';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

type DashboardSummary = {
  recent_jobs?: Array<Record<string, unknown>>;
  copilot?: { active?: boolean; provider?: string };
  gpu?: { device_name?: string; cuda_available?: boolean };
  economics_preview?: { npv_usd?: number };
};

export function AdminPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    apiGet<DashboardSummary>('/dashboard/summary')
      .then(setSummary)
      .catch(() => setSummary(null));
  }, []);

  const jobRows = (summary?.recent_jobs ?? []).map((job) => ({
    job_type: String(job.job_type ?? '—'),
    status: String(job.status ?? '—'),
    job_id: String(job.job_id ?? '').slice(0, 8),
  }));

  return (
    <div>
      <PageHeader
        domain="admin"
        title="Administration"
        description="Platform health, telemetry, and recent job activity."
      />

      {summary ? (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Copilot"
              value={summary.copilot?.active ? 'Live' : 'Stub'}
              hint={summary.copilot?.provider}
              accent="mineral"
            />
            <StatCard
              label="GPU"
              value={summary.gpu?.cuda_available ? 'CUDA' : 'CPU'}
              hint={summary.gpu?.device_name}
              accent="moss"
            />
            <StatCard
              label="Recent jobs"
              value={String(summary.recent_jobs?.length ?? 0)}
              accent="ore"
            />
            <StatCard
              label="NPV preview"
              value={
                summary.economics_preview?.npv_usd != null
                  ? `$${Math.round(summary.economics_preview.npv_usd / 1e6)}M`
                  : 'n/a'
              }
              accent="strata"
            />
          </div>

          <Card title="Recent jobs" subtitle="Async pipeline queue">
            {jobRows.length ? (
              <DataTable columns={['job_id', 'job_type', 'status']} rows={jobRows} />
            ) : (
              <p className="text-sm text-sediment-dim">No recent jobs.</p>
            )}
          </Card>
        </>
      ) : (
        <p className="text-sediment-muted">Loading admin summary…</p>
      )}
    </div>
  );
}