import type { ReactNode } from 'react';

type PageHeaderProps = {
  title: string;
  description?: string;
  domain?: string;
  actions?: ReactNode;
};

const domainColors: Record<string, string> = {
  core: 'text-mineral-400 border-mineral-500/40 bg-mineral-600/10',
  geology: 'text-ore-300 border-ore-500/40 bg-ore-600/10',
  hydrogeology: 'text-mineral-300 border-mineral-500/40 bg-mineral-600/10',
  urban: 'text-strata-300 border-strata-400/40 bg-strata-500/10',
  infrastructure: 'text-sediment-muted border-forge-500 bg-forge-700/50',
  satellite: 'text-mineral-300 border-mineral-500/30 bg-forge-800',
  admin: 'text-sediment-dim border-forge-600 bg-forge-800',
};

export function PageHeader({ title, description, domain, actions }: PageHeaderProps) {
  const domainClass = domain ? (domainColors[domain] ?? domainColors.core) : '';

  return (
    <header className="mb-8 animate-fade-in">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          {domain ? (
            <span className={`tf-badge mb-3 ${domainClass}`}>{domain}</span>
          ) : null}
          <h2 className="text-2xl font-display font-bold tracking-wide text-sediment md:text-3xl lg:text-4xl">
            {title}
          </h2>
          {description ? (
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-sediment-muted">
              {description}
            </p>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 gap-2">{actions}</div> : null}
      </div>
      <div className="tf-divider-glow mt-6" />
    </header>
  );
}