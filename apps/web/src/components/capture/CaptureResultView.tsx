import { useState } from 'react';
import { StructuredJsonView } from '../results/StructuredJsonView';
import { formatJsonLabel, formatJsonValue, isScalar } from '../results/jsonFormat';
import { CaptureChart } from './CaptureChart';
import { DataTable } from './DataTable';
import { DocumentPreview } from './DocumentPreview';
import { GeoPointMap } from './GeoPointMap';

export type CaptureDisplay = {
  display_type?: string;
  summary?: Record<string, unknown>;
  table?: { columns: string[]; rows: Array<Record<string, unknown>>; source?: string } | null;
  tables?: Array<{ columns: string[]; rows: Array<Record<string, unknown>>; source?: string }>;
  map?: { features: Array<Record<string, unknown>>; bounds?: number[] | null } | null;
  chart?: { series: Array<{ label: string; value: number }> } | null;
  document?: { excerpt?: string; keywords?: string[] } | null;
  timeline?: Array<{ step: string; done: boolean; label?: string; status?: string; detail?: string }>;
};

type CaptureResultViewProps = {
  display?: CaptureDisplay | null;
  fallback?: unknown;
};

export function CaptureResultView({ display, fallback }: CaptureResultViewProps) {
  const [showRaw, setShowRaw] = useState(false);

  if (!display && !fallback) return null;

  const summary = display?.summary ?? {};

  return (
    <div className="space-y-4">
      {display ? (
        <>
          {Object.keys(summary).length ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(summary).map(([key, value]) =>
                isScalar(value) ? (
                  <SummaryCard
                    key={key}
                    label={formatJsonLabel(key)}
                    value={formatJsonValue(value)}
                  />
                ) : null,
              )}
            </div>
          ) : null}

          {display.display_type === 'document' && display.document ? (
            <DocumentPreview
              title={String(summary.title ?? 'Document')}
              excerpt={display.document.excerpt ?? ''}
              keywords={display.document.keywords}
              pages={typeof summary.pages === 'number' ? summary.pages : undefined}
              sizeBytes={typeof summary.size_bytes === 'number' ? summary.size_bytes : undefined}
            />
          ) : null}

          {display.map ? (
            <section>
              <h4 className="tf-label mb-2">Spatial preview</h4>
              <GeoPointMap
                features={
                  display.map.features as Array<{
                    geometry?: { type?: string; coordinates?: number[] };
                    properties?: Record<string, unknown>;
                  }>
                }
                bounds={display.map.bounds}
              />
            </section>
          ) : null}

          {display.chart?.series?.length ? (
            <section>
              <h4 className="tf-label mb-2">Value distribution</h4>
              <CaptureChart series={display.chart.series} />
            </section>
          ) : null}

          {display.table?.rows?.length ? (
            <TableSection
              title={display.table.source ?? String(summary.source ?? 'Data')}
              table={display.table}
            />
          ) : null}

          {display.tables?.map((table, index) =>
            table.rows?.length ? (
              <TableSection
                key={`${table.source ?? 'table'}-${index}`}
                title={table.source ?? `Data ${index + 1}`}
                table={table}
              />
            ) : null,
          )}
        </>
      ) : null}

      {fallback ? (
        <>
          <hr className="border-forge-600/40" />
          <StructuredJsonView data={fallback} title="Complete response" />
          <button
            type="button"
            className="tf-link text-xs"
            onClick={() => setShowRaw(!showRaw)}
          >
            {showRaw ? 'Hide raw JSON' : 'View raw JSON'}
          </button>
          {showRaw ? (
            <pre className="tf-code-block mt-2 max-h-96 overflow-auto">
              {JSON.stringify(fallback, null, 2)}
            </pre>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function TableSection({
  title,
  table,
}: {
  title: string;
  table: { columns: string[]; rows: Array<Record<string, unknown>> };
}) {
  return (
    <section>
      <h4 className="tf-label mb-2">{formatJsonLabel(title)}</h4>
      <DataTable columns={table.columns} rows={table.rows} />
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="tf-stat-card border-l-2 border-l-forge-500/60">
      <p className="tf-label">{label}</p>
      <p className="mt-1 font-mono text-sm text-sediment">{value}</p>
    </div>
  );
}