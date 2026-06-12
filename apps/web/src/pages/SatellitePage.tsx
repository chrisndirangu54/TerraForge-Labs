import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { DataTable } from '../components/capture/DataTable';
import { StructuredJsonView } from '../components/results/StructuredJsonView';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

type SatelliteScene = {
  scene_id?: string;
  source?: string;
  date?: string;
  cloud_cover_pct?: number;
  ndvi_mean?: number;
  lst_mean_c?: number;
  coherence?: number;
};

type ScenesResponse = {
  scenes: SatelliteScene[];
  indices_available?: string[];
};

type LatestResponse = {
  index: string;
  statistics?: { min: number; mean: number; max: number };
  raster_url?: string;
};

type InsarResponse = {
  job_id?: string;
  alert_threshold_mm?: number;
  displacement_raster_url?: string;
};

export function SatellitePage() {
  const [loading, setLoading] = useState(true);
  const [insarLoading, setInsarLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogue, setCatalogue] = useState<ScenesResponse | null>(null);
  const [scenes, setScenes] = useState<SatelliteScene[]>([]);
  const [indices, setIndices] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState('ndvi');
  const [latest, setLatest] = useState<LatestResponse | null>(null);
  const [insar, setInsar] = useState<InsarResponse | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiGet<ScenesResponse>('/satellite/scenes')
      .then((response) => {
        setCatalogue(response);
        setScenes(response.scenes ?? []);
        const available = response.indices_available ?? [];
        setIndices(available);
        if (available.length > 0) setSelectedIndex(available[0]);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  async function loadLatest() {
    setError(null);
    try {
      const response = await apiGet<LatestResponse>('/satellite/latest', {
        index: selectedIndex,
      });
      setLatest(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function runInsar() {
    setInsarLoading(true);
    setError(null);
    try {
      const response = await apiPost<InsarResponse>('/satellite/insar', {
        bbox: '37.45,-1.2,37.55,-1.1',
        date_range: ['2026-01-01', '2026-06-30'],
      });
      setInsar(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setInsarLoading(false);
    }
  }

  const sceneRows = scenes.map((scene) => ({
    scene_id: scene.scene_id ?? scene.date ?? 'n/a',
    source: scene.source ?? 'unknown',
    date: scene.date ?? '',
    cloud_cover_pct: scene.cloud_cover_pct ?? '',
    ndvi_mean: scene.ndvi_mean ?? '',
    lst_mean_c: scene.lst_mean_c ?? '',
    coherence: scene.coherence ?? '',
  }));

  return (
    <div>
      <PageHeader
        domain="environmental"
        title="Satellite Feeds"
        description="Scene browser, spectral indices, and InSAR change detection for the Matuu AOI."
        actions={
          <Button variant="secondary" onClick={() => window.location.reload()}>
            Refresh
          </Button>
        }
      />

      {loading ? <p>Loading satellite catalogue...</p> : null}
      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card title="Spectral index" subtitle="Latest composite for the AOI">
          <label className="mb-3 block text-sm text-sediment-muted">
            Index{' '}
            <select
              value={selectedIndex}
              onChange={(e) => setSelectedIndex(e.target.value)}
              className="ml-2 rounded border border-forge-600 bg-forge-900 px-2 py-1"
            >
              {indices.map((index) => (
                <option key={index} value={index}>
                  {index}
                </option>
              ))}
            </select>
          </label>
          <Button variant="primary" onClick={loadLatest}>
            Load latest {selectedIndex}
          </Button>
          {latest?.statistics ? (
            <div className="mt-4 flex flex-wrap gap-2 text-sm">
              <span className="rounded bg-forge-800 px-2 py-1">min: {latest.statistics.min}</span>
              <span className="rounded bg-forge-800 px-2 py-1">mean: {latest.statistics.mean}</span>
              <span className="rounded bg-forge-800 px-2 py-1">max: {latest.statistics.max}</span>
            </div>
          ) : null}
          {latest?.raster_url ? (
            <p className="mt-3 font-mono text-xs text-sediment-dim">{latest.raster_url}</p>
          ) : null}
        </Card>

        <Card title="InSAR displacement" subtitle="Subsidence and slope movement alerts">
          <Button variant="primary" onClick={runInsar} disabled={insarLoading}>
            {insarLoading ? 'Running...' : 'Run InSAR'}
          </Button>
          {insar ? (
            <dl className="mt-4 space-y-2 text-sm">
              <div>
                <dt className="text-sediment-dim">Job</dt>
                <dd className="font-mono">{insar.job_id ?? 'n/a'}</dd>
              </div>
              <div>
                <dt className="text-sediment-dim">Alert threshold</dt>
                <dd>{insar.alert_threshold_mm ?? 'n/a'} mm</dd>
              </div>
              {insar.displacement_raster_url ? (
                <div>
                  <dt className="text-sediment-dim">Raster</dt>
                  <dd className="font-mono text-xs">{insar.displacement_raster_url}</dd>
                </div>
              ) : null}
            </dl>
          ) : null}
        </Card>
      </div>

      <Card title="Scene catalogue" badge={<span>{scenes.length} scenes</span>}>
        {indices.length > 0 ? (
          <div className="mb-4 flex flex-wrap gap-2">
            {indices.map((index) => (
              <span
                key={index}
                className="rounded-full border border-forge-600 px-2 py-0.5 text-xs text-sediment-muted"
              >
                {index}
              </span>
            ))}
          </div>
        ) : null}
        <DataTable
          columns={[
            'scene_id',
            'source',
            'date',
            'cloud_cover_pct',
            'ndvi_mean',
            'lst_mean_c',
            'coherence',
          ]}
          rows={sceneRows}
        />
      </Card>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {latest ? (
          <Card title="Latest index response">
            <StructuredJsonView data={latest} />
          </Card>
        ) : null}
        {insar ? (
          <Card title="InSAR response">
            <StructuredJsonView data={insar} />
          </Card>
        ) : null}
      </div>

      {catalogue ? (
        <Card title="Complete catalogue response" className="mt-6">
          <StructuredJsonView data={catalogue} />
        </Card>
      ) : null}
    </div>
  );
}