import { useState } from 'react';

type ApiPanelProps = {
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => Promise<unknown>;
};

export function ApiPanel({ title, description, actionLabel, onAction }: ApiPanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<unknown>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const data = await onAction();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={{ marginBottom: '2rem' }}>
      <h2>{title}</h2>
      <p>{description}</p>
      <button type="button" onClick={run} disabled={loading}>
        {loading ? 'Loading...' : actionLabel}
      </button>
      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {result ? <pre>{JSON.stringify(result, null, 2)}</pre> : null}
    </section>
  );
}