import type { CaptureDisplay } from './CaptureResultView';

export function inferDisplay(value: unknown): CaptureDisplay | null {
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

  const listKeys = ['items', 'records', 'boreholes', 'scenes', 'catalogs', 'devices', 'ranked_targets'];
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