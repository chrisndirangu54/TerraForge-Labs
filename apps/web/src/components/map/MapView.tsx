import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export type LayerGroup = Record<string, string[]>;

export type MapOverlay = {
  id: string;
  type: string;
  title: string;
  tile_url_template?: string;
  preview_url?: string;
  opacity?: number;
  available?: boolean;
  storage_key?: string;
};

type MapViewProps = {
  layerGroups: LayerGroup;
  mapMode?: string;
  overlays?: MapOverlay[];
  center?: [number, number];
  zoom?: number;
};

const DEFAULT_CENTER: [number, number] = [37.5, -1.15];

export function MapView({
  layerGroups,
  mapMode = '2d_satellite',
  overlays = [],
  center = DEFAULT_CENTER,
  zoom = 11,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [visibleLayers, setVisibleLayers] = useState<Record<string, boolean>>({});
  const [activeOverlays, setActiveOverlays] = useState<Record<string, boolean>>({});
  const [mapError, setMapError] = useState<string | null>(null);
  const [useCanvasFallback, setUseCanvasFallback] = useState(false);

  const allLayers = Object.entries(layerGroups).flatMap(([group, layers]) =>
    layers.map((layer) => ({ group, layer, id: `${group}:${layer}` })),
  );

  useEffect(() => {
    const initial: Record<string, boolean> = {};
    allLayers.forEach(({ id }) => {
      initial[id] = false;
    });
    setVisibleLayers(initial);
  }, [JSON.stringify(layerGroups)]);

  useEffect(() => {
    const initial: Record<string, boolean> = {};
    overlays.forEach((overlay) => {
      initial[overlay.id] = false;
    });
    setActiveOverlays(initial);
  }, [JSON.stringify(overlays)]);

  useEffect(() => {
    if (!containerRef.current || useCanvasFallback) return undefined;

    let map: maplibregl.Map;
    try {
      map = new maplibregl.Map({
        container: containerRef.current,
        style: 'https://demotiles.maplibre.org/style.json',
        center,
        zoom,
      });
      map.addControl(new maplibregl.NavigationControl(), 'top-right');
      mapRef.current = map;
    } catch (err) {
      setMapError(err instanceof Error ? err.message : String(err));
      setUseCanvasFallback(true);
      return undefined;
    }

    map.on('load', () => {
      map.addSource('terraforge-demo', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: { name: 'Exploration grid' },
              geometry: {
                type: 'Point',
                coordinates: center,
              },
            },
          ],
        },
      });
      map.addLayer({
        id: 'terraforge-demo-points',
        type: 'circle',
        source: 'terraforge-demo',
        paint: {
          'circle-radius': 8,
          'circle-color': '#c45c26',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
        },
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [useCanvasFallback, center[0], center[1], zoom]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || useCanvasFallback) return;

    overlays.forEach((overlay) => {
      const sourceId = `overlay-${overlay.id}`;
      const layerId = `overlay-${overlay.id}-raster`;
      const enabled = activeOverlays[overlay.id] && overlay.tile_url_template;

      if (!enabled) {
        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
        return;
      }

      const tileUrl = `${API_BASE_URL}${overlay.tile_url_template}`;

      const attach = () => {
        if (map.getSource(sourceId)) {
          if (map.getLayer(layerId)) map.removeLayer(layerId);
          map.removeSource(sourceId);
        }
        map.addSource(sourceId, {
          type: 'raster',
          tiles: [tileUrl],
          tileSize: 256,
        });
        map.addLayer({
          id: layerId,
          type: 'raster',
          source: sourceId,
          paint: { 'raster-opacity': overlay.opacity ?? 0.65 },
        });
      };

      if (map.isStyleLoaded()) {
        attach();
      } else {
        map.once('load', attach);
      }
    });
  }, [activeOverlays, overlays, useCanvasFallback]);

  function toggleLayer(layerId: string) {
    setVisibleLayers((prev) => ({ ...prev, [layerId]: !prev[layerId] }));
  }

  function toggleOverlay(overlayId: string) {
    setActiveOverlays((prev) => ({ ...prev, [overlayId]: !prev[overlayId] }));
  }

  const activeCount = Object.values(visibleLayers).filter(Boolean).length;
  const activeOverlayCount = Object.values(activeOverlays).filter(Boolean).length;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '1rem' }}>
      <aside
        style={{
          border: '1px solid #ddd',
          borderRadius: 6,
          padding: '0.75rem',
          maxHeight: 480,
          overflowY: 'auto',
        }}
      >
        <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>Layers</h3>
        <p style={{ fontSize: '0.8rem', color: '#666', margin: '0 0 0.75rem' }}>
          Mode: {mapMode} · {activeCount} vector · {activeOverlayCount} overlay
        </p>
        {overlays.length > 0 ? (
          <div style={{ marginBottom: '0.75rem' }}>
            <strong style={{ fontSize: '0.85rem' }}>Overlays</strong>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0.25rem 0 0' }}>
              {overlays.map((overlay) => (
                <li key={overlay.id} style={{ marginBottom: '0.25rem' }}>
                  <label style={{ fontSize: '0.8rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={activeOverlays[overlay.id] ?? false}
                      disabled={!overlay.tile_url_template}
                      onChange={() => toggleOverlay(overlay.id)}
                      style={{ marginRight: '0.35rem' }}
                    />
                    {overlay.title}
                    {!overlay.available ? ' (run kriging first)' : ''}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {Object.entries(layerGroups).map(([group, layers]) => (
          <div key={group} style={{ marginBottom: '0.75rem' }}>
            <strong style={{ fontSize: '0.85rem', textTransform: 'capitalize' }}>
              {group.replace(/_/g, ' ')}
            </strong>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0.25rem 0 0' }}>
              {layers.map((layer) => {
                const id = `${group}:${layer}`;
                return (
                  <li key={id} style={{ marginBottom: '0.25rem' }}>
                    <label style={{ fontSize: '0.8rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={visibleLayers[id] ?? false}
                        onChange={() => toggleLayer(id)}
                        style={{ marginRight: '0.35rem' }}
                      />
                      {layer.replace(/_/g, ' ')}
                    </label>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </aside>

      <div style={{ position: 'relative', minHeight: 480 }}>
        {useCanvasFallback ? (
          <canvas
            ref={(canvas) => {
              if (!canvas) return;
              const ctx = canvas.getContext('2d');
              if (!ctx) return;
              canvas.width = canvas.offsetWidth;
              canvas.height = 480;
              const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
              gradient.addColorStop(0, '#1a3a2a');
              gradient.addColorStop(1, '#2d5a3d');
              ctx.fillStyle = gradient;
              ctx.fillRect(0, 0, canvas.width, canvas.height);
              ctx.fillStyle = '#c45c26';
              ctx.beginPath();
              ctx.arc(canvas.width / 2, canvas.height / 2, 12, 0, Math.PI * 2);
              ctx.fill();
              ctx.fillStyle = '#fff';
              ctx.font = '14px sans-serif';
              ctx.fillText('Canvas map fallback (MapLibre unavailable)', 16, 24);
              ctx.fillText(`${activeCount} layers · ${activeOverlayCount} overlays`, 16, 44);
            }}
            style={{ width: '100%', height: 480, borderRadius: 6, border: '1px solid #ddd' }}
          />
        ) : (
          <div
            ref={containerRef}
            style={{ width: '100%', height: 480, borderRadius: 6, border: '1px solid #ddd' }}
          />
        )}
        {mapError ? (
          <p style={{ fontSize: '0.8rem', color: '#a63', marginTop: '0.5rem' }}>{mapError}</p>
        ) : null}
      </div>
    </div>
  );
}