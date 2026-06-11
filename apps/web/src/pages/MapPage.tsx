import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { MapView, type LayerGroup } from '../components/map/MapView';
import { useProjectStore } from '../stores/projectStore';

type MappingLayersResponse = {
  map_modes: string[];
  layer_groups: LayerGroup;
};

export function MapPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [mapMode, setMapMode] = useState('2d_satellite');
  const [layerGroups, setLayerGroups] = useState<LayerGroup>({});
  const [tileMeta, setTileMeta] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      apiGet<MappingLayersResponse>('/mapping/layers'),
      apiGet<Record<string, unknown>>('/tiles/10/500/400'),
    ])
      .then(([layers, tile]) => {
        setLayerGroups(layers.layer_groups);
        if (layers.map_modes.length > 0) {
          setMapMode(layers.map_modes[0]);
        }
        setTileMeta(tile);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2>Main Map</h2>
      <p>
        MapLibre mission control with layer catalogue from the backend.
        {selectedProject ? ` Project: ${selectedProject.name}` : ' No project selected.'}
      </p>
      {loading ? <p>Loading map catalogue...</p> : null}
      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {!loading && Object.keys(layerGroups).length > 0 ? (
        <>
          <label style={{ display: 'block', marginBottom: '0.75rem' }}>
            Map mode{' '}
            <select value={mapMode} onChange={(e) => setMapMode(e.target.value)}>
              {['2d_street', '2d_satellite', '2d_hybrid', '3d_terrain', '3d_geological'].map(
                (mode) => (
                  <option key={mode} value={mode}>
                    {mode}
                  </option>
                ),
              )}
            </select>
          </label>
          <MapView layerGroups={layerGroups} mapMode={mapMode} />
        </>
      ) : null}
      {tileMeta ? (
        <details style={{ marginTop: '1rem' }}>
          <summary>Vector tile metadata</summary>
          <pre>{JSON.stringify(tileMeta, null, 2)}</pre>
        </details>
      ) : null}
    </div>
  );
}