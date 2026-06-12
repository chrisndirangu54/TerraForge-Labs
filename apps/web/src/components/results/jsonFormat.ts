export function formatJsonLabel(key: string): string {
  return key.replace(/_/g, ' ').replace(/-/g, ' ');
}

export function formatJsonValue(value: unknown, maxLength = 240): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'number' || typeof value === 'string') {
    const text = String(value);
    return text.length <= maxLength ? text : `${text.slice(0, maxLength)}…`;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    if (value.every((item) => ['string', 'number', 'boolean'].includes(typeof item))) {
      return value.map((item) => formatJsonValue(item, 80)).join(', ');
    }
    return `[${value.length} items]`;
  }
  if (typeof value === 'object') {
    return `{${Object.keys(value as object).length} fields}`;
  }
  return String(value);
}

export function unionTableColumns(rows: Array<Record<string, unknown>>): string[] {
  const columns: string[] = [];
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!columns.includes(key)) columns.push(key);
    }
  }
  return columns;
}

export function isScalar(value: unknown): boolean {
  return (
    value === null ||
    value === undefined ||
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  );
}

export function isMapList(value: unknown): value is Array<Record<string, unknown>> {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every((item) => item !== null && typeof item === 'object' && !Array.isArray(item))
  );
}