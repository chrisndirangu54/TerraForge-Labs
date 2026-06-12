import type { ReactNode } from 'react';

type CardProps = {
  title?: string;
  subtitle?: string;
  badge?: ReactNode;
  children: ReactNode;
  className?: string;
  footer?: ReactNode;
  accent?: 'ore' | 'mineral' | 'none';
  interactive?: boolean;
};

const accentTop: Record<NonNullable<CardProps['accent']>, string> = {
  ore: 'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-ore-500/50 before:to-transparent',
  mineral:
    'before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-mineral-500/50 before:to-transparent',
  none: '',
};

export function Card({
  title,
  subtitle,
  badge,
  children,
  className = '',
  footer,
  accent = 'none',
  interactive = true,
}: CardProps) {
  const panelClass = interactive ? 'tf-panel-interactive' : 'tf-panel';

  return (
    <section className={`relative overflow-hidden ${panelClass} ${accentTop[accent]} ${className}`}>
      {(title || subtitle || badge) && (
        <header className="tf-panel-header flex items-start justify-between gap-3">
          <div>
            {title ? (
              <h3 className="text-base font-display font-semibold text-sediment">{title}</h3>
            ) : null}
            {subtitle ? <p className="mt-0.5 text-sm text-sediment-muted">{subtitle}</p> : null}
          </div>
          {badge}
        </header>
      )}
      <div className="p-5">{children}</div>
      {footer ? (
        <footer className="border-t border-forge-600/50 bg-forge-900/20 px-5 py-3.5 text-sm">
          {footer}
        </footer>
      ) : null}
    </section>
  );
}