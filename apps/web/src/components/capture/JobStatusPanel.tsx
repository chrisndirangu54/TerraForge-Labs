import type { CaptureDisplay } from './CaptureResultView';
import { CaptureResultView } from './CaptureResultView';

type JobStatusPanelProps = {
  job: Record<string, unknown> | null;
  title?: string;
};

export function JobStatusPanel({ job, title = 'Job status' }: JobStatusPanelProps) {
  if (!job) return null;

  const display = (job.display as CaptureDisplay | undefined) ?? null;
  const status = String(job.status ?? 'unknown');
  const statusColor =
    status === 'complete' ? 'text-moss-500' : status === 'failed' ? 'text-red-400' : 'text-mineral-400';

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h4 className="font-display text-sm text-sediment">{title}</h4>
        <span className={`tf-badge border-forge-500/50 font-mono ${statusColor}`}>{status}</span>
      </div>
      {display?.timeline ? (
        <ol className="flex flex-wrap gap-2">
          {display.timeline.map((step) => (
            <li
              key={step.step}
              className={`rounded-full border px-3 py-1 font-mono text-[11px] ${
                step.done
                  ? 'border-mineral-500/40 bg-mineral-600/15 text-mineral-300'
                  : 'border-forge-600/50 text-sediment-dim'
              }`}
            >
              {step.step}
            </li>
          ))}
        </ol>
      ) : null}
      <CaptureResultView display={display} fallback={job} />
    </div>
  );
}