import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  children: ReactNode;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-ore-500 text-forge-950 hover:bg-ore-400 hover:shadow-glow-ore active:scale-[0.98] shadow-glow-ore border border-ore-400/50 font-semibold',
  secondary:
    'bg-forge-700/80 text-sediment hover:bg-forge-600 hover:border-mineral-500/40 active:scale-[0.98] border border-forge-600',
  ghost:
    'bg-transparent text-sediment-muted hover:text-sediment hover:bg-forge-800/80 border border-transparent hover:border-forge-600/50',
  danger:
    'bg-red-950/60 text-red-300 hover:bg-red-900/50 border border-red-800/50 active:scale-[0.98]',
};

export function Button({
  variant = 'primary',
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm transition-all duration-200 ease-smooth disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100 ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}