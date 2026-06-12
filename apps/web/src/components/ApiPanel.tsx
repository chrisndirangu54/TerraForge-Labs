import { useState } from 'react';
import { CaptureResultView } from './capture/CaptureResultView';
import { DataTable } from './capture/DataTable';
import { inferDisplay } from './results/inferDisplay';
import { Button } from './ui/Button';
import { Card } from './ui/Card';

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

  const display = result ? inferDisplay(result) : null;

  return (
    <Card
      title={title}
      subtitle={description}
      className="mb-6"
      footer={
        <Button variant="secondary" onClick={run} disabled={loading}>
          {loading ? 'Loading…' : actionLabel}
        </Button>
      }
    >
      {error ? <pre className="tf-error">{error}</pre> : null}
      {result ? (
        <CaptureResultView display={display} fallback={result} />
      ) : (
        <p className="text-sm text-sediment-dim">Run the action to fetch API response.</p>
      )}
      {display?.table && display.display_type === 'table' && !display.map && !display.chart ? (
        <div className="mt-4">
          <DataTable columns={display.table.columns} rows={display.table.rows} />
        </div>
      ) : null}
    </Card>
  );
}