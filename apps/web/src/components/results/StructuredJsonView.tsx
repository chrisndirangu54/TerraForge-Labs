import { DataTable } from '../capture/DataTable';
import {
  formatJsonLabel,
  formatJsonValue,
  isMapList,
  isScalar,
  unionTableColumns,
} from './jsonFormat';

type StructuredJsonViewProps = {
  data: unknown;
  title?: string;
  depth?: number;
};

export function StructuredJsonView({ data, title, depth = 0 }: StructuredJsonViewProps) {
  if (data === null || data === undefined) {
    return <p className="text-sm text-sediment-dim">No data returned.</p>;
  }
  return <NodeView node={data} title={title} depth={depth} />;
}

function NodeView({
  node,
  title,
  depth,
}: {
  node: unknown;
  title?: string;
  depth: number;
}) {
  if (isScalar(node)) {
    return (
      <div className="flex items-center justify-between gap-4 border-b border-forge-600/20 py-2 text-sm">
        <span className="text-sediment-dim">{title ?? 'value'}</span>
        <span className="font-mono text-sediment">{formatJsonValue(node)}</span>
      </div>
    );
  }

  if (Array.isArray(node)) {
    return <ListView list={node} title={title} depth={depth} />;
  }

  if (typeof node === 'object') {
    return <MapView map={node as Record<string, unknown>} title={title} depth={depth} />;
  }

  return <span className="text-sm">{formatJsonValue(node)}</span>;
}

function MapView({
  map,
  title,
  depth,
}: {
  map: Record<string, unknown>;
  title?: string;
  depth: number;
}) {
  const entries = Object.entries(map).filter(([key]) => key !== 'display');
  const scalars = entries.filter(([, value]) => isScalar(value));
  const complex = entries.filter(([, value]) => !isScalar(value));

  return (
    <div className="space-y-4">
      {title && depth === 0 ? (
        <h4 className="tf-label">{title}</h4>
      ) : null}

      {scalars.length ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {scalars.map(([key, value]) => (
            <div key={key} className="tf-stat-card border-l-2 border-l-forge-500/60">
              <p className="tf-label">{formatJsonLabel(key)}</p>
              <p className="mt-1 font-mono text-sm text-sediment">{formatJsonValue(value)}</p>
            </div>
          ))}
        </div>
      ) : null}

      {complex.map(([key, value]) => (
        <ComplexField key={key} label={key} value={value} depth={depth} />
      ))}
    </div>
  );
}

function ListView({
  list,
  title,
  depth,
}: {
  list: unknown[];
  title?: string;
  depth: number;
}) {
  if (list.length === 0) {
    return <p className="text-sm text-sediment-dim">{title ? `${title}: empty list` : 'Empty list'}</p>;
  }

  if (isMapList(list)) {
    const columns = unionTableColumns(list);
    return (
      <section className="rounded-lg border border-forge-600/50 bg-forge-900/30 p-4">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h4 className="tf-label">{title ? formatJsonLabel(title) : 'Items'}</h4>
          <span className="text-xs text-sediment-dim">
            {list.length} row{list.length === 1 ? '' : 's'}
          </span>
        </div>
        <DataTable columns={columns} rows={list} />
      </section>
    );
  }

  if (list.every((item) => isScalar(item))) {
    return (
      <section className="rounded-lg border border-forge-600/50 bg-forge-900/30 p-4">
        {title ? <h4 className="tf-label mb-3">{formatJsonLabel(title)}</h4> : null}
        <div className="flex flex-wrap gap-2">
          {list.map((item, index) => (
            <span
              key={index}
              className="rounded-full border border-forge-600 px-2 py-0.5 font-mono text-xs text-sediment-muted"
            >
              {formatJsonValue(item)}
            </span>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-3 rounded-lg border border-forge-600/50 bg-forge-900/30 p-4">
      {title ? <h4 className="tf-label">{formatJsonLabel(title)}</h4> : null}
      {list.map((item, index) => (
        <ComplexField key={index} label={`${index + 1}`} value={item} depth={depth + 1} />
      ))}
    </section>
  );
}

function ComplexField({
  label,
  value,
  depth,
}: {
  label: string;
  value: unknown;
  depth: number;
}) {
  const subtitle =
    Array.isArray(value)
      ? `${value.length} items`
      : typeof value === 'object' && value !== null
        ? `${Object.keys(value).length} fields`
        : formatJsonValue(value);

  if (isScalar(value)) {
    return <NodeView node={value} title={formatJsonLabel(label)} depth={depth} />;
  }

  return (
    <details
      className="rounded-lg border border-forge-600/40 bg-forge-950/40 p-3"
      open={depth < 1}
    >
      <summary className="cursor-pointer list-none">
        <div className="flex items-center justify-between gap-3">
          <span className="font-medium text-sediment">{formatJsonLabel(label)}</span>
          <span className="text-xs text-sediment-dim">{subtitle}</span>
        </div>
      </summary>
      <div className="mt-3 border-t border-forge-600/30 pt-3">
        <StructuredJsonView data={value} depth={depth + 1} />
      </div>
    </details>
  );
}