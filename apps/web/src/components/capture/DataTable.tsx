type DataTableProps = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
};

export function DataTable({ columns, rows }: DataTableProps) {
  if (!rows.length) {
    return <p className="text-sm text-sediment-dim">No tabular rows to display.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-forge-600/50">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-forge-900/80">
          <tr>
            {columns.map((column) => (
              <th
                key={column}
                className="tf-label whitespace-nowrap px-3 py-2.5 font-mono normal-case tracking-normal"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={index}
              className="border-t border-forge-600/30 hover:bg-forge-800/40"
            >
              {columns.map((column) => (
                <td key={column} className="whitespace-nowrap px-3 py-2 font-mono text-xs text-sediment-muted">
                  {formatCell(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}