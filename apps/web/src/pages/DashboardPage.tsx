import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiGet } from '../api/client';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';

type DashboardSummary = {
  recent_jobs: Array<Record<string, unknown>>;
  copilot: { active?: boolean; provider?: string };
  gpu: { device_name?: string; cuda_available?: boolean };
  domain_cv?: Record<
    string,
    { pooled_metrics?: { accuracy?: number }; n_samples?: number; meets_threshold?: boolean }
  >;
  economics_preview?: { npv_usd?: number; irr?: number | null };
  deposit?: { ore_tonnes_estimate?: number; mean_grade_ta_ppm?: number };
};

const TRAVERSE_LINKS = [
  { to: '/map', title: 'Map', desc: 'Layer catalogue & tiles' },
  { to: '/kriging', title: 'Kriging', desc: 'Variogram & grade' },
  { to: '/deposit', title: 'Deposit 3D', desc: 'Block model viewer' },
  { to: '/platform', title: 'Platform hub', desc: '28+ pipelines', accent: true },
  { to: '/copilot', title: 'Copilot', desc: 'Gemini assistant' },
  { to: '/upload', title: 'Field upload', desc: 'Sync observations' },
];

function fmtUsd(v: number | undefined) {
  if (v === undefined) return 'n/a';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(v);
}

function GpuIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <path d="M9 9h6v6H9zM2 12h2M20 12h2M12 2v2M12 20v2" />
    </svg>
  );
}

function OreIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  );
}

function ModelIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
      <path d="M4 19V5l8-3 8 3v14l-8 3-8-3z" />
    </svg>
  );
}

function JobIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4" aria-hidden>
      <path d="M4 6h16M4 12h16M4 18h10" />
    </svg>
  );
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<DashboardSummary>('/dashboard/summary')
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)));
  }, []);

  const cvCount = summary?.domain_cv ? Object.keys(summary.domain_cv).length : 0;
  const jobCount = summary?.recent_jobs?.length ?? 0;

  return (
    <div>
      <PageHeader
        domain="core"
        title="Mission Control"
        description="Exploration jobs, domain models, economics, and platform telemetry for the Matuu-Kwale corridor."
      />

      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      {summary ? (
        <div className="tf-stagger space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="NPV preview"
              value={fmtUsd(summary.economics_preview?.npv_usd)}
              hint={
                summary.economics_preview?.irr != null
                  ? `IRR ${(summary.economics_preview.irr * 100).toFixed(1)}%`
                  : undefined
              }
              accent="ore"
              icon={<OreIcon />}
            />
            <StatCard
              label="Deposit estimate"
              value={
                summary.deposit?.ore_tonnes_estimate != null
                  ? `${(summary.deposit.ore_tonnes_estimate / 1e6).toFixed(2)}M t`
                  : 'n/a'
              }
              hint={
                summary.deposit?.mean_grade_ta_ppm != null
                  ? `@ ${summary.deposit.mean_grade_ta_ppm} ppm Ta`
                  : undefined
              }
              accent="strata"
              icon={<OreIcon />}
            />
            <StatCard
              label="Domain models"
              value={cvCount > 0 ? `${cvCount} trained` : '—'}
              hint={cvCount > 0 ? 'Stratified CV active' : 'Run model training'}
              accent="mineral"
              icon={<ModelIcon />}
            />
            <StatCard
              label="Accelerator"
              value={summary.gpu.cuda_available ? 'GPU' : 'CPU'}
              hint={
                summary.gpu.cuda_available
                  ? summary.gpu.device_name
                  : 'CUDA unavailable — CPU fallback'
              }
              accent="moss"
              icon={<GpuIcon />}
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card
              title="Economics preview"
              subtitle="Ore financials snapshot"
              badge={<span className="tf-badge-ore">NPV</span>}
              accent="ore"
              footer={
                <Link to="/financial" className="tf-link-ore">
                  Run full financial analysis →
                </Link>
              }
            >
              <p className="font-display text-3xl font-bold text-ore-300">
                {fmtUsd(summary.economics_preview?.npv_usd)}
              </p>
              <p className="mt-3 text-sm text-sediment-muted">
                Deposit ~{summary.deposit?.ore_tonnes_estimate?.toLocaleString()} t @{' '}
                <span className="font-mono text-strata-300">
                  {summary.deposit?.mean_grade_ta_ppm} ppm Ta
                </span>
              </p>
            </Card>

            <Card
              title="Domain models"
              subtitle="Stratified cross-validation"
              badge={<span className="tf-badge-live">CV</span>}
              accent="mineral"
              footer={
                <Link to="/model-training" className="tf-link">
                  Model training →
                </Link>
              }
            >
              {summary.domain_cv ? (
                <ul className="space-y-2">
                  {Object.entries(summary.domain_cv).map(([name, model]) => (
                    <li
                      key={name}
                      className="flex items-center justify-between rounded-lg border border-forge-600/40 bg-forge-900/40 px-3.5 py-2.5 transition-colors hover:border-mineral-500/30 hover:bg-forge-800/50"
                    >
                      <span className="font-mono text-sm text-sediment">{name}</span>
                      <span className="tf-data">
                        {(Number(model.pooled_metrics?.accuracy ?? 0) * 100).toFixed(1)}%
                        {model.meets_threshold ? (
                          <span className="ml-2 text-moss-500">✓</span>
                        ) : null}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-sediment-muted">No CV report — run model training.</p>
              )}
            </Card>

            <Card
              title="Platform telemetry"
              badge={
                summary.copilot.active ? (
                  <span className="tf-badge-live">
                    <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse-glow rounded-full bg-moss-500" />
                    LIVE
                  </span>
                ) : (
                  <span className="tf-badge border-forge-500 text-sediment-dim">STUB</span>
                )
              }
              accent="mineral"
            >
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-forge-600/40 bg-forge-900/40 p-4">
                  <p className="tf-label">Copilot</p>
                  <p className="mt-2 font-mono text-sm text-mineral-300">
                    {summary.copilot.active ? 'Gemini live' : 'stub mode'}
                  </p>
                </div>
                <div className="rounded-lg border border-forge-600/40 bg-forge-900/40 p-4">
                  <p className="tf-label">Accelerator</p>
                  <p className="mt-2 font-mono text-sm text-mineral-300">
                    {summary.gpu.cuda_available ? summary.gpu.device_name : 'CPU fallback'}
                  </p>
                </div>
              </div>
            </Card>

            <Card
              title="Recent jobs"
              subtitle="Async pipeline queue"
              badge={
                <span className="tf-badge border-forge-500/50 bg-forge-800/50 text-sediment-muted">
                  {jobCount} total
                </span>
              }
            >
              <ul className="space-y-2">
                {(summary.recent_jobs ?? []).slice(0, 5).map((job) => (
                  <li
                    key={String(job.job_id)}
                    className="flex items-center justify-between rounded-md border border-forge-600/30 bg-forge-950/30 px-3 py-2 font-mono text-xs"
                  >
                    <span className="text-sediment-muted">{String(job.job_type)}</span>
                    <span
                      className={
                        String(job.status) === 'completed'
                          ? 'text-moss-500'
                          : String(job.status) === 'failed'
                            ? 'text-red-400'
                            : 'text-mineral-400'
                      }
                    >
                      {String(job.status)}
                    </span>
                  </li>
                ))}
                {(summary.recent_jobs ?? []).length === 0 ? (
                  <li className="text-sm text-sediment-dim">No recent jobs.</li>
                ) : null}
              </ul>
            </Card>

            <Card
              title="Quick traverse"
              className="lg:col-span-2"
              accent="mineral"
              footer={
                <p className="text-xs text-sediment-dim">
                  Fusion targeting, variogram kriging, LiDAR/UAV processing, and JORC reporting.
                </p>
              }
            >
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {TRAVERSE_LINKS.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`group tf-traverse-tile ${link.accent ? 'border-ore-500/30 hover:border-ore-500/50' : ''}`}
                  >
                    <span className={link.accent ? 'text-ore-300 group-hover:text-ore-200' : ''}>
                      {link.title}
                    </span>
                    <span>{link.desc}</span>
                  </Link>
                ))}
              </div>
            </Card>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 rounded-xl border border-forge-600/40 bg-forge-850/40 px-5 py-4 text-sediment-muted">
          <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-mineral-500 shadow-glow" />
          Loading dashboard telemetry…
        </div>
      )}
    </div>
  );
}