import type { ReactNode } from 'react';

type StatCardProps = {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: 'ore' | 'mineral' | 'strata' | 'moss';
  icon?: ReactNode;
};

const accentBorder: Record<NonNullable<StatCardProps['accent']>, string> = {
  ore: 'border-l-ore-500/60',
  mineral: 'border-l-mineral-500/60',
  strata: 'border-l-strata-400/60',
  moss: 'border-l-moss-500/60',
};

export function StatCard({ label, value, hint, accent = 'mineral', icon }: StatCardProps) {
  return (
    <div className={`tf-stat-card border-l-2 ${accentBorder[accent]}`}>
      <div className="flex items-start justify-between gap-3">
        <p className="tf-label">{label}</p>
        {icon ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-forge-600/50 bg-forge-800/80 text-mineral-400">
            {icon}
          </div>
        ) : null}
      </div>
      <p className="mt-2 font-display text-2xl font-bold tracking-wide text-sediment md:text-3xl">
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-sediment-dim">{hint}</p> : null}
    </div>
  );
}