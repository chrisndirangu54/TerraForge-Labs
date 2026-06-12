import { useState } from 'react';
import { CaptureResultView, type CaptureDisplay } from './capture/CaptureResultView';
import { DataTable } from './capture/DataTable';
import { Button } from './ui/Button';
import { Card } from './ui/Card';

type ApiPanelProps = {
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => Promise<unknown>;
};

function inferDisplay(value: unknown): CaptureDisplay | null {
  if (!value || typeof value !== 'object') return null;
  const record = value as Record<string, unknown>;
  if (record.display && typeof record.display === 'object') {
    return record.display as CaptureDisplay;
  }

  if (Array.isArray(value) && value.length) {
    const rows = value as Array<Record<string, unknown>>;
    const columns = Object.keys(rows[0]).slice(0, 8);
    return {
      display_type: 'table',
      table: { columns, rows },
    };
  }

  const listKeys = ['items', 'records', 'boreholes', 'scenes', 'catalogs', 'devices'];
  for (const key of listKeys) {
    const list = record[key];
    if (Array.isArray(list) && list.length && typeof list[0] === 'object') {
      const rows = list as Array<Record<string, unknown>>;
      const columns = Object.keys(rows[0]).slice(0, 8);
      return {
        display_type: 'table',
        summary: { rows: rows.length, source: key },
        table: { columns, rows },
      };
    }
  }

  const scalarEntries = Object.entries(record).filter(
    ([, v]) => typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean',
  );
  if (scalarEntries.length >= 2) {
    return {
      display_type: 'table',
      table: {
        columns: ['field', 'value'],
        rows: scalarEntries.map(([field, value]) => ({ field, value })),
      },
    };
  }

  return null;
}

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