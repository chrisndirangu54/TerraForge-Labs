import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { DataTable } from '../components/capture/DataTable';
import {
  MapView,
  type FeatureLayerCollection,
  type LayerGroup,
  type MapOverlay,
} from '../components/map/MapView';
import { inferDisplay } from '../components/results/inferDisplay';
import { PageHeader } from '../components/ui/PageHeader';
import { useProjectStore } from '../stores/projectStore';

type MappingLayersResponse = {
  map_modes: string[];
  layer_groups: LayerGroup;
  feature_layers?: Record<string, FeatureLayerCollection>;
  overlays?: MapOverlay[];
  center?: { lon: number; lat: number; elevation_m?: number };
  bounds?: [number, number, number, number];
};

export function MapPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [mapMode, setMapMode] = useState('2d_satellite');
  const [mapModes, setMapModes] = useState<string[]>([]);
  const [layerGroups, setLayerGroups] = useState<LayerGroup>({});
  const [featureLayers, setFeatureLayers] = useState<Record<string, FeatureLayerCollection>>({});
  const [overlays, setOverlays] = useState<MapOverlay[]>([]);
  const [center, setCenter] = useState<[number, number]>([37.5, -1.15]);
  const [tileMeta, setTileMeta] = useState<Record<string, unknown> | null>(null);
  const [stacCount, setStacCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const layerParams = selectedProject?.id ? { project_id: selectedProject.id } : undefined;

    const layerPromise = apiGet<MappingLayersResponse>('/mapping/layers', layerParams);
    const tilePromise = apiGet<Record<string, unknown>>('/tiles/10/500/400').catch(() => null);
    const stacPromise = apiGet<{ count: number }>('/mapping/stac/items', layerParams).catch(
      () => null,
    );

    Promise.all([layerPromise, tilePromise, stacPromise])
      .then(([layers, tile, stac]) => {
        setLayerGroups(layers.layer_groups);
        setFeatureLayers(layers.feature_layers ?? {});
        setOverlays(layers.overlays ?? []);
        setMapModes(layers.map_modes);
        if (layers.map_modes.length > 0) {
          setMapMode(
            layers.map_modes.includes('2d_satellite') ? '2d_satellite' : layers.map_modes[0],
          );
        }
        if (layers.center?.lon != null && layers.center?.lat != null) {
          setCenter([layers.center.lon, layers.center.lat]);
        }
        setTileMeta(tile);
        setStacCount(stac?.count ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [selectedProject?.id]);

  return (
    <div>
      <PageHeader
        domain="core"
        title="Main Map"
        description="MapLibre mission control with Matuu sample points, deposit blocks, boreholes, and kriging overlays."
      />

      {selectedProject ? (
        <p className="mb-4 font-mono text-sm text-sediment-muted">
          Project: <span className="text-mineral-300">{selectedProject.name}</span>
        </p>
      ) : null}

      {loading ? (
        <p className="text-sediment-muted">Loading map catalogue…</p>
      ) : null}
      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      {!loading && Object.keys(layerGroups).length > 0 ? (
        <>
          <label className="mb-4 flex max-w-xs flex-col gap-1 text-sm text-sediment-muted">
            Map mode
            <select
              className="rounded-lg border border-forge-600 bg-forge-900 px-3 py-2 text-sediment"
              value={mapMode}
              onChange={(e) => setMapMode(e.target.value)}
            >
              {mapModes.map((mode) => (
                  <option key={mode} value={mode}>
                    {mode.replace(/_/g, ' ')}
                  </option>
              ))}
            </select>
          </label>

          <MapView
            layerGroups={layerGroups}
            featureLayers={featureLayers}
            mapMode={mapMode}
            overlays={overlays}
            center={center}
          />
        </>
      ) : null}

      {stacCount != null ? (
        <p className="mt-4 text-sm text-sediment-muted">
          STAC catalog: {stacCount} raster item{stacCount === 1 ? '' : 's'}
          {selectedProject ? ` for ${selectedProject.name}` : ''}.
        </p>
      ) : null}

      {tileMeta ? (
        <details className="mt-4 rounded-lg border border-forge-600/40 bg-forge-900/30 p-4">
          <summary className="cursor-pointer text-sm text-sediment">Vector tile metadata</summary>
          {(() => {
            const display = inferDisplay(tileMeta);
            return display?.table ? (
              <DataTable columns={display.table.columns} rows={display.table.rows} />
            ) : (
              <p className="mt-2 text-sm text-sediment-muted">Tile redirect loaded successfully.</p>
            );
          })()}
        </details>
      ) : null}
    </div>
  );
}