import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import '../../cesium/init';
import {
  Cartesian2,
  Cartesian3,
  Color,
  HeadingPitchRange,
  Ion,
  Math as CesiumMath,
  UrlTemplateImageryProvider,
  Viewer,
  type Primitive,
} from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { loadDepositMeshPrimitive } from './depositMeshLoader';
import { DepositBlockFallback } from './DepositBlockFallback';

export type DepositBlock = {
  lon?: number;
  lat?: number;
  elevation_m?: number;
  depth_m?: number;
  ta_ppm_mean?: number;
  color_hex?: string;
  unit?: string;
};

type DepositCesiumViewerProps = {
  blocks: DepositBlock[];
  centre?: { lon: number; lat: number; elevation_m?: number };
  meshUrl?: string;
  className?: string;
};

const BLOCK_SIZE_M = 50;

Ion.defaultAccessToken = '';

function hexToCesiumColor(hex: string | undefined, grade: number | undefined): Color {
  if (hex && /^#[0-9a-fA-F]{6}$/.test(hex)) {
    return Color.fromCssColorString(hex).withAlpha(0.92);
  }
  const ratio = Math.min(Math.max(((grade ?? 100) - 80) / 120, 0), 1);
  return Color.fromHsl(0.08 - ratio * 0.06, 0.75, 0.45 + ratio * 0.15, 0.92);
}

function blocksKey(blocks: DepositBlock[]): string {
  return blocks
    .map(
      (block) =>
        `${block.lon ?? ''}:${block.lat ?? ''}:${block.elevation_m ?? ''}:${block.ta_ppm_mean ?? ''}`,
    )
    .join('|');
}

export function DepositCesiumViewer({
  blocks,
  centre,
  meshUrl,
  className = 'h-[420px] w-full',
}: DepositCesiumViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const meshPrimitiveRef = useRef<Primitive | null>(null);
  const [viewerReady, setViewerReady] = useState(false);
  const [viewerError, setViewerError] = useState<string | null>(null);
  const blockSignature = useMemo(() => blocksKey(blocks), [blocks]);

  const renderBlocks = useCallback(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    const lon = centre?.lon ?? 37.5;
    const lat = centre?.lat ?? -1.15;
    const surfaceElevation = centre?.elevation_m ?? 1180;

    viewer.entities.removeAll();

    const geoBlocks = blocks.filter(
      (block) => block.lon != null && block.lat != null,
    );

    if (geoBlocks.length === 0) {
      viewer.entities.add({
        position: Cartesian3.fromDegrees(lon, lat, surfaceElevation),
        point: {
          pixelSize: 14,
          color: Color.ORANGE,
          outlineColor: Color.WHITE,
          outlineWidth: 2,
        },
        label: {
          text: 'Generate deposit model to load blocks',
          font: '14px sans-serif',
          fillColor: Color.WHITE,
          outlineColor: Color.BLACK,
          outlineWidth: 2,
          pixelOffset: new Cartesian2(0, -24),
        },
      });
      viewer.camera.setView({
        destination: Cartesian3.fromDegrees(lon, lat - 0.015, surfaceElevation + 1200),
        orientation: {
          heading: CesiumMath.toRadians(20),
          pitch: CesiumMath.toRadians(-40),
          roll: 0,
        },
      });
      viewer.scene.requestRender();
      return;
    }

    geoBlocks.forEach((block) => {
      const blockLon = Number(block.lon);
      const blockLat = Number(block.lat);
      const blockElevation = Number(block.elevation_m ?? surfaceElevation);
      const grade = Number(block.ta_ppm_mean ?? 100);
      const centerElevation = blockElevation;

      viewer.entities.add({
        name: `${block.unit ?? 'block'} @ ${grade.toFixed(0)} ppm Ta`,
        position: Cartesian3.fromDegrees(blockLon, blockLat, centerElevation),
        box: {
          dimensions: new Cartesian3(BLOCK_SIZE_M, BLOCK_SIZE_M, BLOCK_SIZE_M),
          material: hexToCesiumColor(block.color_hex, grade),
          outline: true,
          outlineColor: Color.WHITE.withAlpha(0.45),
        },
        description: `Grade ${grade.toFixed(1)} ppm Ta · ${block.unit ?? 'unknown unit'} · depth ${block.depth_m ?? 'n/a'} m`,
      });
    });

    viewer.zoomTo(viewer.entities, new HeadingPitchRange(0, -0.55, 200)).catch(() => {
      viewer.camera.setView({
        destination: Cartesian3.fromDegrees(lon, lat - 0.012, surfaceElevation + 900),
        orientation: {
          heading: CesiumMath.toRadians(25),
          pitch: CesiumMath.toRadians(-50),
          roll: 0,
        },
      });
    });
    viewer.scene.requestRender();
  }, [blocks, centre?.elevation_m, centre?.lat, centre?.lon]);

  const loadMesh = useCallback(async () => {
    const viewer = viewerRef.current;
    if (!viewer || !meshUrl) return;

    if (meshPrimitiveRef.current) {
      viewer.scene.primitives.remove(meshPrimitiveRef.current);
      meshPrimitiveRef.current = null;
    }

    try {
      const primitive = await loadDepositMeshPrimitive(viewer, meshUrl, {
        lon: centre?.lon ?? 37.5,
        lat: centre?.lat ?? -1.15,
        elevation_m: centre?.elevation_m ?? 1180,
      });
      meshPrimitiveRef.current = primitive;
      viewer.scene.requestRender();
    } catch (err) {
      console.warn('Deposit mesh could not be loaded; showing block primitives only.', err);
    }
  }, [centre?.elevation_m, centre?.lat, centre?.lon, meshUrl]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    setViewerError(null);
    setViewerReady(false);

    let viewer: Viewer | null = null;
    try {
      viewer = new Viewer(container, {
        animation: false,
        timeline: false,
        baseLayer: false,
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        fullscreenButton: false,
        infoBox: true,
        selectionIndicator: true,
        terrain: undefined,
        skyBox: false,

        msaaSamples: 2,
        requestRenderMode: true,
        maximumRenderTimeChange: Infinity,
      });
      viewer.imageryLayers.addImageryProvider(
        new UrlTemplateImageryProvider({
          url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          maximumLevel: 19,
          credit: 'OpenStreetMap contributors',
        }),
      );
      viewer.scene.globe.depthTestAgainstTerrain = false;
      viewer.scene.screenSpaceCameraController.enableCollisionDetection = false;
      viewerRef.current = viewer;
      setViewerReady(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setViewerError(message);
      console.error('Cesium viewer failed to initialize', err);
      return undefined;
    }

    return () => {
      if (meshPrimitiveRef.current && viewer) {
        viewer.scene.primitives.remove(meshPrimitiveRef.current);
        meshPrimitiveRef.current = null;
      }
      viewer?.destroy();
      viewerRef.current = null;
      setViewerReady(false);
    };
  }, []);

  useEffect(() => {
    if (!viewerReady) return;
    renderBlocks();
    void loadMesh();
  }, [viewerReady, blockSignature, meshUrl, renderBlocks, loadMesh]);

  if (viewerError) {
    return <DepositBlockFallback blocks={blocks} className={className} />;
  }

  return (
    <div className={`deposit-cesium-viewer relative overflow-hidden rounded-xl border border-forge-600/60 shadow-glow ${className}`}>
      <div ref={containerRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute bottom-2 left-3 rounded bg-forge-950/70 px-2 py-1 text-[10px] text-sediment-dim">
        {blocks.filter((b) => b.lon != null && b.lat != null).length} blocks
        {meshUrl ? ' · mesh loaded' : ''}
      </div>
    </div>
  );
}