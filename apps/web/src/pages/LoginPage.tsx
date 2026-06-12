import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiPost } from '../api/client';
import { getApiBaseUrl } from '../api/client';
import { Button } from '../components/ui/Button';
import { setSession } from '../auth/token';

type LoginResponse = {
  access_token: string;
  user: { email: string; role: string };
};

const FEATURES = [
  { label: 'LiDAR → DTM/DSM', accent: 'text-mineral-400' },
  { label: 'Kriging & fusion targeting', accent: 'text-ore-400' },
  { label: '3D deposit & JORC reporting', accent: 'text-strata-300' },
];

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('geo@example.com');
  const [password, setPassword] = useState('securepass1');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<LoginResponse>('/auth/login', { email, password });
      setSession(response.access_token, response.user);
      navigate('/');
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen">
      <div
        className="pointer-events-none absolute inset-0 bg-terrain-grid bg-grid opacity-30"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-contour-lines bg-contour opacity-60"
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-0 bg-strata-gradient" aria-hidden />
      <div
        className="tf-orb -left-32 top-1/4 h-96 w-96 bg-ore-500/10 animate-float"
        aria-hidden
      />
      <div
        className="tf-orb -right-24 bottom-1/4 h-80 w-80 bg-mineral-500/10 animate-float"
        style={{ animationDelay: '2s' }}
        aria-hidden
      />

      <div className="relative hidden w-1/2 flex-col justify-between border-r border-forge-600/40 bg-forge-900/40 p-12 backdrop-blur-sm lg:flex">
        <div>
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-ore-500/50 bg-gradient-to-br from-forge-800 to-forge-900 font-display text-2xl font-bold text-ore-400 shadow-glow-ore">
              TF
            </div>
            <div>
              <p className="font-display text-xl font-bold tracking-wider text-sediment">
                TerraForge Labs
              </p>
              <p className="font-mono text-[11px] uppercase tracking-widest text-mineral-500">
                Geological exploration platform
              </p>
            </div>
          </div>

          <h1 className="max-w-md text-4xl font-display font-bold leading-tight tracking-wide text-sediment xl:text-5xl">
            Map the subsurface.{' '}
            <span className="text-gradient-ore">Forge the future.</span>
          </h1>
          <p className="mt-5 max-w-sm text-base leading-relaxed text-sediment-muted">
            End-to-end exploration workflows for the Matuu-Kwale corridor — from LiDAR
            processing to deposit modelling and JORC reporting.
          </p>
        </div>

        <ul className="space-y-3">
          {FEATURES.map((feature) => (
            <li
              key={feature.label}
              className="flex items-center gap-3 rounded-lg border border-forge-600/40 bg-forge-850/40 px-4 py-3 backdrop-blur-sm"
            >
              <span className={`h-1.5 w-1.5 rounded-full bg-current ${feature.accent}`} />
              <span className={`text-sm font-medium ${feature.accent}`}>{feature.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="relative flex flex-1 items-center justify-center p-6 md:p-10">
        <div className="tf-panel w-full max-w-md animate-slide-up shadow-glow-lg">
          <div className="tf-panel-header text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-xl border border-ore-500/50 bg-gradient-to-br from-forge-800 to-forge-900 font-display text-3xl font-bold text-ore-400 shadow-glow-ore lg:hidden">
              TF
            </div>
            <h2 className="text-xl font-display font-bold tracking-wide lg:text-2xl">
              TerraForge Access
            </h2>
            <p className="mt-1.5 text-sm text-sediment-muted">Sign in to mission control</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-5 p-6">
            <div>
              <label className="tf-label mb-2 block" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                className="tf-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div>
              <label className="tf-label mb-2 block" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="tf-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <Button type="submit" variant="primary" className="w-full" disabled={loading}>
              {loading ? 'Authenticating…' : 'Enter Mission Control'}
            </Button>
          </form>

          {error ? <pre className="tf-error mx-6 mb-6">{error}</pre> : null}

          <p className="border-t border-forge-600/50 px-6 py-4 text-center font-mono text-[11px] text-sediment-dim">
            {getApiBaseUrl()}
          </p>
        </div>
      </div>
    </div>
  );
}