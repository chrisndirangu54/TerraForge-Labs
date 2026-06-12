import type { CaptureDisplay } from '../capture/CaptureResultView';
import { formatJsonValue, isMapList, unionTableColumns } from './jsonFormat';

const LIST_KEYS = [
  'items',
  'records',
  'boreholes',
  'drill_log_preview',
  'blocks_preview',
  'scenes',
  'catalogs',
  'devices',
  'results',
  'layers',
  'settlements',
  'features',
  'packs',
  'categories',
  'timeline',
  'alerts',
  'recent_jobs',
  'jobs',
  'observations',
  'sessions',
  'uploads',
];

const CLASSIFICATION_KEYS = ['label', 'species', 'confidence', 'top3', 'top_k', 'classes'];

export function inferDisplay(value: unknown): CaptureDisplay | null {
  if (!value || typeof value !== 'object') return null;
  const record = value as Record<string, unknown>;

  if (record.display && typeof record.display === 'object') {
    return record.display as CaptureDisplay;
  }

  if (CLASSIFICATION_KEYS.some((key) => key in record)) {
    return classificationDisplay(record);
  }

  const sections: CaptureDisplay[] = [];
  for (const key of LIST_KEYS) {
    const list = record[key];
    if (isMapList(list)) {
      sections.push(tableDisplay(list, key));
    }
  }

  if (record.layer_groups && typeof record.layer_groups === 'object') {
    const rows = Object.entries(record.layer_groups as Record<string, string[]>).map(
      ([group, layers]) => ({ group, layers: layers.join(', ') }),
    );
    sections.push(tableDisplay(rows, 'layer_groups'));
  }

  const scalar = scalarTable(record);
  if (scalar) sections.push(scalar);

  if (sections.length === 0) return null;
  if (sections.length === 1) return sections[0];
  return mergeSections(sections, record);
}

function scalarTable(record: Record<string, unknown>): CaptureDisplay | null {
  const rows = Object.entries(record)
    .filter(([key]) => key !== 'display')
    .map(([field, value]) => ({ field, value: formatJsonValue(value) }));
  if (!rows.length) return null;
  return {
    display_type: 'table',
    summary: { fields: rows.length },
    table: { columns: ['field', 'value'], rows },
  };
}

function mergeSections(
  sections: CaptureDisplay[],
  source: Record<string, unknown>,
): CaptureDisplay {
  const tables = sections
    .map((section) => section.table)
    .filter((table): table is NonNullable<CaptureDisplay['table']> => Boolean(table));

  const mapSection = sections.find((section) => section.map);

  return {
    display_type: 'mixed',
    summary: {
      sections: sections.length,
      count: source.count as number | undefined,
    },
    tables,
    map: mapSection?.map,
  };
}

function tableDisplay(rows: Array<Record<string, unknown>>, source: string): CaptureDisplay {
  const columns = unionTableColumns(rows);
  const hasPoints = rows.some((row) => row.lon != null && row.lat != null);
  const display: CaptureDisplay = {
    display_type: 'table',
    summary: { rows: rows.length, source },
    table: { columns, rows, source },
  };
  if (hasPoints) {
    display.display_type = 'mixed';
    display.map = {
      features: rows
        .filter((row) => row.lon != null && row.lat != null)
        .map((row) => ({
          geometry: { type: 'Point', coordinates: [Number(row.lon), Number(row.lat)] },
          properties: row,
        })),
    };
  }
  return display;
}

function classificationDisplay(record: Record<string, unknown>): CaptureDisplay {
  const label = record.label ?? record.species;
  const confidence = record.confidence ?? record.model_confidence;
  const top = (record.top3 ?? record.top_k ?? record.classes) as unknown;
  const rows = Array.isArray(top)
    ? top.map((entry, index) =>
        typeof entry === 'object' && entry !== null
          ? (entry as Record<string, unknown>)
          : { label: String(entry), confidence: index },
      )
    : [{ label, confidence }];

  const extraSummary = Object.fromEntries(
    Object.entries(record)
      .filter(([key]) => !CLASSIFICATION_KEYS.includes(key) && key !== 'display')
      .map(([key, value]) => [key, formatJsonValue(value)]),
  );

  return {
    display_type: 'chart',
    summary: {
      label: label as string | undefined,
      confidence: confidence as number | undefined,
      accelerator: record.accelerator as string | undefined,
      task: record.task as string | undefined,
      ...extraSummary,
    },
    chart: {
      series: rows.map((row, index) => ({
        label: String(row.label ?? row.species ?? index + 1),
        value: Number(row.confidence ?? row.score ?? confidence ?? 0),
      })),
    },
    table: {
      columns: rows.length ? unionTableColumns(rows) : ['label', 'confidence'],
      rows,
    },
  };
}