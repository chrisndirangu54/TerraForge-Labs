import { FormEvent, ReactNode, useState } from 'react';
import { Button } from './ui/Button';
import { PageHeader } from './ui/PageHeader';

type WorkflowPageProps = {
  title: string;
  description: string;
  domain?: string;
  children?: ReactNode;
  actionLabel?: string;
  onAction?: () => Promise<unknown>;
};

export function WorkflowPage({
  title,
  description,
  domain,
  children,
  actionLabel,
  onAction,
}: WorkflowPageProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<unknown>(null);

  async function run(event: FormEvent) {
    event.preventDefault();
    if (!onAction) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await onAction());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader title={title} description={description} domain={domain} />

      {children ? <div className="mb-6">{children}</div> : null}

      {onAction ? (
        <form onSubmit={run} className="mb-6">
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? 'Processing…' : actionLabel ?? 'Run pipeline'}
          </Button>
        </form>
      ) : null}

      {error ? <pre className="tf-error mb-6">{error}</pre> : null}
      {result ? (
        <pre className="tf-code-block">{JSON.stringify(result, null, 2)}</pre>
      ) : null}
    </div>
  );
}