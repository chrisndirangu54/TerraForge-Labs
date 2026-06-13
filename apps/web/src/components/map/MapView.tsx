import { useEffect, useMemo, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { CircleLayerSpecification } from '@maplibre/maplibre-gl-style-spec';
import type { FeatureCollection, Feature, Geometry } from 'geojson';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  (import.meta.env.DEV ? '' : 'http://localhost:8000');

export type LayerGroup = Record<string, string[]>;

export type MapOverlay = {
  id: string;
  type: string;
  title: string;
  tile_url_template?: string | null;
  preview_url?: string | null;
  opacity?: number;
  available?: boolean;
  storage_key?: string | null;
};

// Use the real GeoJSON types — coordinates depth is handled by the geojson package
export type FeatureLayerCollection = FeatureCollection<Geometry, Record<string, unknown>>;

type MapViewProps = {
  layerGroups: LayerGroup;
  featureLayers?: Record<string, FeatureLayerCollection>;
  mapMode?: string;
  overlays?: MapOverlay[];
  center?: [number, number];
  zoom?: number;
};

const DEFAULT_CENTER: [number, number] = [37.5, -1.15];

const MAP_STYLES: Record<string, string> = {
  '2d_street': 'https://demotiles.maplibre.org/style.json',
  '2d_satellite': 'https://api.maptiler.com/maps/hybrid/style.json?key=get_your_own_key',
  '2d_hybrid': 'https://demotiles.maplibre.org/style.json',
  '3d_terrain': 'https://demotiles.maplibre.org/style.json',
  '3d_geological': 'https://demotiles.maplibre.org/style.json',
};

function satelliteStyle(): maplibregl.StyleSpecification {
  return {
    version: 8,
    sources: {
      esri: {
        type: 'raster',
        tiles: [
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        ],
        tileSize: 256,
        attribution: 'Esri World Imagery',
      },
    },
    layers: [
      {
        id: 'esri-satellite',
        type: 'raster',
        source: 'esri',
      },
    ],
  };
}

function styleForMode(mapMode: string): string | maplibregl.StyleSpecification {
  if (mapMode.includes('satellite') || mapMode === '2d_hybrid') {
    return satelliteStyle();
  }
  return MAP_STYLES[mapMode] ?? MAP_STYLES['2d_satellite'];
}

function layerPaint(layerId: string): CircleLayerSpecification['paint'] {
  if (layerId.includes('borehole')) {
    return {
      'circle-radius': 7,
      'circle-color': '#2f8fd6',
      'circle-stroke-width': 2,
      'circle-stroke-color': '#fff',
    };
  }
  if (layerId.includes('deposit')) {
    return {
      'circle-radius': 9,
      'circle-color': '#c45c26',
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ffe0c2',
    };
  }
  return {
    'circle-radius': 6,
    'circle-color': [
      'interpolate',
      ['linear'],
      ['coalesce', ['get', 'ta_ppm'], ['get', 'ta_ppm_mean'], 100],
      50,
      '#355c3a',
      120,
      '#c45c26',
      220,
      '#ffd27a',
    ],
    'circle-stroke-width': 1,
    'circle-stroke-color': '#ffffff',
  };
}

/**
 * Normalise whatever the backend sends into a valid GeoJSON FeatureCollection.
 * Handles: already-valid collections, single Features, and malformed payloads.
 */
function toFeatureCollection(data: unknown): FeatureCollection {
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;

    if (obj.type === 'FeatureCollection' && Array.isArray(obj.features)) {
      // Filter out any features with null/undefined geometry so MapLibre never
      // receives something it can't validate.
      const clean: Feature[] = (obj.features as unknown[]).filter(
        (f): f is Feature =>
          f !== null &&
          typeof f === 'object' &&
          (f as Record<string, unknown>).type === 'Feature' &&
          (f as Record<string, unknown>).geometry != null,
      );
      return { type: 'FeatureCollection', features: clean };
    }

    if (obj.type === 'Feature' && obj.geometry != null) {
      return { type: 'FeatureCollection', features: [data as Feature] };
    }
  }

  console.warn('[MapView] Invalid GeoJSON payload — using empty FeatureCollection', data);
  return { type: 'FeatureCollection', features: [] };
}

export function MapView({
  layerGroups,
  featureLayers = {},
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
  const [mapReady, setMapReady] = useState(false);

  const allLayers = useMemo(
    () =>
      Object.entries(layerGroups).flatMap(([group, layers]) =>
        layers.map((layer) => ({ group, layer, id: `${group}:${layer}` })),
      ),
    [layerGroups],
  );

  useEffect(() => {
    const initial: Record<string, boolean> = {};
    allLayers.forEach(({ id }) => {
      initial[id] = Boolean(featureLayers[id]);
    });
    setVisibleLayers(initial);
  }, [allLayers, featureLayers]);

  useEffect(() => {
    const initial: Record<string, boolean> = {};
    overlays.forEach((overlay) => {
      initial[overlay.id] = Boolean(overlay.available);
    });
    setActiveOverlays(initial);
  }, [overlays]);

  // ── Map initialisation ──────────────────────────────────────────────────────
  // Re-creates the map instance whenever mapMode or center changes.
  useEffect(() => {
    if (!containerRef.current) return undefined;

    setMapReady(false);
    setMapError(null);

    const style = styleForMode(mapMode);
    const map = new maplibregl.Map({
      container: containerRef.current,
      style,
      center,
      zoom,
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    mapRef.current = map;

    const onLoad = () => setMapReady(true);
    const onError = (event: { error?: Error }) => {
      setMapError(event.error?.message ?? 'Map failed to load');
    };

    map.on('load', onLoad);
    map.on('error', onError);

    return () => {
      map.off('load', onLoad);
      map.off('error', onError);
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, [mapMode, center[0], center[1], zoom]);

  // ── Feature layer installation ──────────────────────────────────────────────
  // `mapReady` guarantees the style is fully loaded before we touch sources,
  // so we no longer need the isStyleLoaded / map.once fallback (which created
  // stale-closure bugs when featureLayers changed before the map finished loading).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    Object.entries(featureLayers).forEach(([layerId, collection]) => {
      const sourceId = `source-${layerId}`;
      const circleLayerId = `layer-${layerId}-points`;

      // Tear down existing source/layer pair before re-adding.
      if (map.getLayer(circleLayerId)) map.removeLayer(circleLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);

      // Normalise and validate — this is what was causing "not a valid GeoJSON object".
      const data = toFeatureCollection(collection);

      map.addSource(sourceId, { type: 'geojson', data });
      map.addLayer({
        id: circleLayerId,
        type: 'circle',
        source: sourceId,
        layout: { visibility: visibleLayers[layerId] ? 'visible' : 'none' },
        paint: layerPaint(layerId),
      });
    });
  }, [featureLayers, mapReady, visibleLayers]);

  // ── Visibility toggling ─────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    Object.keys(featureLayers).forEach((layerId) => {
      const circleLayerId = `layer-${layerId}-points`;
      if (!map.getLayer(circleLayerId)) return;
      map.setLayoutProperty(
        circleLayerId,
        'visibility',
        visibleLayers[layerId] ? 'visible' : 'none',
      );
    });
  }, [visibleLayers, featureLayers, mapReady]);

  // ── Raster overlay management ───────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

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
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);

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
    });
  }, [activeOverlays, overlays, mapReady]);

  function toggleLayer(layerId: string) {
    if (!featureLayers[layerId]) return;
    setVisibleLayers((prev) => ({ ...prev, [layerId]: !prev[layerId] }));
  }

  function toggleOverlay(overlayId: string) {
    setActiveOverlays((prev) => ({ ...prev, [overlayId]: !prev[overlayId] }));
  }

  const activeCount = Object.entries(visibleLayers).filter(
    ([id, on]) => on && featureLayers[id],
  ).length;
  const activeOverlayCount = Object.values(activeOverlays).filter(Boolean).length;

  return (
    <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
      <aside className="max-h-[520px] overflow-y-auto rounded-xl border border-forge-600/50 bg-forge-900/50 p-4">
        <h3 className="font-display text-sm text-sediment">Layers</h3>
        <p className="mt-1 font-mono text-[11px] text-sediment-dim">
          {mapMode.replace(/_/g, ' ')} · {activeCount} vector · {activeOverlayCount} overlay
        </p>

        {overlays.length > 0 ? (
          <div className="mt-4">
            <p className="tf-label">Overlays</p>
            <ul className="mt-2 space-y-1">
              {overlays.map((overlay) => (
                <li key={overlay.id}>
                  <label className="flex cursor-pointer items-center gap-2 text-xs text-sediment-muted">
                    <input
                      type="checkbox"
                      checked={activeOverlays[overlay.id] ?? false}
                      disabled={!overlay.tile_url_template}
                      onChange={() => toggleOverlay(overlay.id)}
                    />
                    {overlay.title}
                    {!overlay.available ? ' (run kriging)' : ''}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {Object.entries(layerGroups).map(([group, layers]) => (
          <div key={group} className="mt-4">
            <p className="tf-label capitalize">{group.replace(/_/g, ' ')}</p>
            <ul className="mt-2 space-y-1">
              {layers.map((layer) => {
                const id = `${group}:${layer}`;
                const hasData = Boolean(featureLayers[id]);
                return (
                  <li key={id}>
                    <label className="flex cursor-pointer items-center gap-2 text-xs text-sediment-muted">
                      <input
                        type="checkbox"
                        checked={visibleLayers[id] ?? false}
                        disabled={!hasData}
                        onChange={() => toggleLayer(id)}
                      />
                      {layer.replace(/_/g, ' ')}
                      {!hasData ? ' (no data)' : ''}
                    </label>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </aside>

      <div>
        <div
          ref={containerRef}
          className="h-[480px] w-full overflow-hidden rounded-xl border border-forge-600/60 shadow-glow"
        />
        {mapError ? <p className="mt-2 text-sm text-red-400">{mapError}</p> : null}
      </div>
    </div>
  );
}