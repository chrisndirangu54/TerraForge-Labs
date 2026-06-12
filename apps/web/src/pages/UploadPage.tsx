import { useEffect, useState } from 'react';
import { apiGet, apiPost, captureUpload } from '../api/client';
import { CaptureResultView, type CaptureDisplay } from '../components/capture/CaptureResultView';
import { DataTable } from '../components/capture/DataTable';
import { FileDropZone } from '../components/capture/FileDropZone';
import { TransportPanel } from '../components/capture/TransportPanel';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { useProjectStore } from '../stores/projectStore';

type FieldCatalog = {
  catalogs: Array<{
    name: string;
    path: string;
    status: string;
    samples?: number;
    classes?: string[];
    size_bytes?: number;
  }>;
  ingest_instructions: Record<string, string>;
};

type CaptureCatalog = {
  instruments: string[];
  transports: Array<{ id: string; label: string }>;
};

type ObservationItem = {
  id: string;
  sample_id?: string;
  instrument_type?: string;
  lon?: number;
  lat?: number;
  source?: string;
  flagged?: boolean;
  data?: Record<string, unknown>;
};

type CaptureResult = {
  display?: CaptureDisplay;
  upload_id?: string;
  row_count?: number;
};

export function UploadPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [tab, setTab] = useState<'files' | 'devices' | 'observations'>('files');
  const [transport, setTransport] = useState('file');
  const [instrumentType, setInstrumentType] = useState('auto');
  const [catalog, setCatalog] = useState<FieldCatalog | null>(null);
  const [captureCatalog, setCaptureCatalog] = useState<CaptureCatalog | null>(null);
  const [observations, setObservations] = useState<ObservationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CaptureResult | null>(null);
  const [registerResult, setRegisterResult] = useState<unknown>(null);

  useEffect(() => {
    apiGet<FieldCatalog>('/ingest/field-catalog').then(setCatalog).catch(() => setCatalog(null));
    apiGet<CaptureCatalog>('/capture/catalog').then(setCaptureCatalog).catch(() => setCaptureCatalog(null));
  }, []);

  useEffect(() => {
    if (!selectedProject?.id) {
      setObservations([]);
      return;
    }
    apiGet<{ items: ObservationItem[] }>('/ingest/observations', {
      project_id: selectedProject.id,
      limit: '50',
    })
      .then((response) => setObservations(response.items))
      .catch(() => setObservations([]));
  }, [selectedProject?.id, result]);

  async function handleFiles(files: FileList) {
    const file = files[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = (await captureUpload(file, {
        instrumentType: instrumentType === 'auto' ? undefined : instrumentType,
        transport,
        projectId: selectedProject?.id,
      })) as CaptureResult;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function registerFieldDataset(name: string) {
    setError(null);
    try {
      const data = await apiPost('/ingest/field-upload/register', {
        dataset: name,
        files: [`data/${name}/manifest.json`],
        project_id: selectedProject?.id,
      });
      setRegisterResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const observationRows = observations.map((item) => ({
    sample_id: item.sample_id ?? item.id.slice(0, 8),
    instrument: item.instrument_type ?? '—',
    lon: item.lon,
    lat: item.lat,
    source: item.source,
    flagged: item.flagged ? 'yes' : 'no',
    primary_value: Object.values(item.data ?? {})[0] ?? '—',
  }));

  return (
    <div>
      <PageHeader
        domain="core"
        title="Data Capture"
        description="Upload CSV, PDF, GeoJSON and survey exports — or sync Bluetooth, Wi-Fi, and radio field devices into structured views."
      />

      {selectedProject ? (
        <p className="mb-6 font-mono text-sm text-sediment-muted">
          Active project: <span className="text-mineral-300">{selectedProject.name}</span>
        </p>
      ) : (
        <p className="mb-6 rounded-lg border border-ore-500/30 bg-ore-600/10 px-4 py-3 text-sm text-ore-300">
          Select a project to attach captures and view stored observations.
        </p>
      )}

      <div className="mb-6 flex flex-wrap gap-2">
        {(['files', 'devices', 'observations'] as const).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`rounded-lg border px-4 py-2 text-sm capitalize transition-colors ${
              tab === key
                ? 'border-ore-500/50 bg-ore-600/15 text-ore-300'
                : 'border-forge-600/50 text-sediment-muted hover:text-sediment'
            }`}
          >
            {key}
          </button>
        ))}
      </div>

      {tab === 'files' ? (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-2">
            <FileDropZone onFiles={handleFiles} disabled={loading} />
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="tf-label mb-2 block">Transport channel</span>
                <select
                  className="tf-input"
                  value={transport}
                  onChange={(e) => setTransport(e.target.value)}
                >
                  {(captureCatalog?.transports ?? [{ id: 'file', label: 'File' }]).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="tf-label mb-2 block">Instrument (auto-detect)</span>
                <select
                  className="tf-input"
                  value={instrumentType}
                  onChange={(e) => setInstrumentType(e.target.value)}
                >
                  <option value="auto">Auto-detect from file</option>
                  {(captureCatalog?.instruments ?? []).map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <Card title="Field datasets" subtitle="Bundled corpora">
            {catalog ? (
              <ul className="space-y-2">
                {catalog.catalogs.map((entry) => (
                  <li
                    key={entry.name}
                    className="flex items-center justify-between rounded border border-forge-600/40 px-3 py-2 text-sm"
                  >
                    <span className="text-sediment">{entry.name}</span>
                    {entry.status === 'ready' ? (
                      <Button variant="ghost" className="text-xs" onClick={() => registerFieldDataset(entry.name)}>
                        Register
                      </Button>
                    ) : (
                      <span className="text-sediment-dim">{entry.status}</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-sediment-dim">Loading catalog…</p>
            )}
            {registerResult ? (
              <pre className="tf-code-block mt-3 max-h-28 text-[10px]">{JSON.stringify(registerResult, null, 2)}</pre>
            ) : null}
          </Card>
        </div>
      ) : null}

      {tab === 'devices' ? (
        <TransportPanel
          projectId={selectedProject?.id}
          transport={transport}
          onTransportChange={setTransport}
        />
      ) : null}

      {tab === 'observations' ? (
        <Card title="Project observations" subtitle="Persisted instrument readings">
          {observationRows.length ? (
            <DataTable
              columns={['sample_id', 'instrument', 'lon', 'lat', 'source', 'flagged', 'primary_value']}
              rows={observationRows}
            />
          ) : (
            <p className="text-sm text-sediment-dim">No observations stored for this project yet.</p>
          )}
        </Card>
      ) : null}

      {result?.display ? (
        <Card title="Capture result" className="mt-6" badge={<span className="tf-badge-live">{result.row_count ?? 0} rows</span>}>
          <CaptureResultView display={result.display} fallback={result} />
        </Card>
      ) : null}

      {error ? <pre className="tf-error mt-6">{error}</pre> : null}
    </div>
  );
}