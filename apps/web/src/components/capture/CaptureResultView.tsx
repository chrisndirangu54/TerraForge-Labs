import { useState } from 'react';
import { CaptureChart } from './CaptureChart';
import { DataTable } from './DataTable';
import { DocumentPreview } from './DocumentPreview';
import { GeoPointMap } from './GeoPointMap';

export type CaptureDisplay = {
  display_type?: string;
  summary?: Record<string, unknown>;
  table?: { columns: string[]; rows: Array<Record<string, unknown>> } | null;
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

  if (!display) {
    return fallback ? <FallbackJson value={fallback} showRaw={showRaw} setShowRaw={setShowRaw} /> : null;
  }

  const summary = display.summary ?? {};

  return (
    <div className="space-y-4">
      {Object.keys(summary).length ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {summary.rows != null ? <SummaryCard label="Rows" value={String(summary.rows)} /> : null}
          {summary.flagged != null ? <SummaryCard label="Flagged" value={String(summary.flagged)} accent="ore" /> : null}
          {summary.instrument_type ? <SummaryCard label="Instrument" value={String(summary.instrument_type)} /> : null}
          {summary.transport ? <SummaryCard label="Transport" value={String(summary.transport)} accent="mineral" /> : null}
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
            features={display.map.features as Array<{ geometry?: { type?: string; coordinates?: number[] }; properties?: Record<string, unknown> }>}
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
        <section>
          <h4 className="tf-label mb-2">Captured readings</h4>
          <DataTable columns={display.table.columns} rows={display.table.rows} />
        </section>
      ) : null}

      {fallback ? <FallbackJson value={fallback} showRaw={showRaw} setShowRaw={setShowRaw} /> : null}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: 'ore' | 'mineral';
}) {
  const border =
    accent === 'ore'
      ? 'border-l-ore-500/60'
      : accent === 'mineral'
        ? 'border-l-mineral-500/60'
        : 'border-l-forge-500/60';
  return (
    <div className={`tf-stat-card border-l-2 ${border}`}>
      <p className="tf-label">{label}</p>
      <p className="mt-1 font-display text-lg font-semibold text-sediment">{value}</p>
    </div>
  );
}

function FallbackJson({
  value,
  showRaw,
  setShowRaw,
}: {
  value: unknown;
  showRaw: boolean;
  setShowRaw: (v: boolean) => void;
}) {
  return (
    <div>
      <button
        type="button"
        className="tf-link text-xs"
        onClick={() => setShowRaw(!showRaw)}
      >
        {showRaw ? 'Hide raw JSON' : 'Show raw JSON'}
      </button>
      {showRaw ? <pre className="tf-code-block mt-2 max-h-64">{JSON.stringify(value, null, 2)}</pre> : null}
    </div>
  );
}