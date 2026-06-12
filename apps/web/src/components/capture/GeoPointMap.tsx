type GeoFeature = {
  geometry?: { type?: string; coordinates?: number[] };
  properties?: Record<string, unknown>;
};

type GeoPointMapProps = {
  features: GeoFeature[];
  bounds?: number[] | null;
};

export function GeoPointMap({ features, bounds }: GeoPointMapProps) {
  const points = features
    .filter((f) => f.geometry?.type === 'Point' && (f.geometry.coordinates?.length ?? 0) >= 2)
    .map((f) => ({
      lon: f.geometry!.coordinates![0],
      lat: f.geometry!.coordinates![1],
      label: String(f.properties?.sample_id ?? f.properties?.point_id ?? ''),
      flagged: Boolean(f.properties?.flagged),
    }));

  if (!points.length) {
    return <p className="text-sm text-sediment-dim">No georeferenced points in this capture.</p>;
  }

  const west = bounds?.[0] ?? Math.min(...points.map((p) => p.lon)) - 0.01;
  const south = bounds?.[1] ?? Math.min(...points.map((p) => p.lat)) - 0.01;
  const east = bounds?.[2] ?? Math.max(...points.map((p) => p.lon)) + 0.01;
  const north = bounds?.[3] ?? Math.max(...points.map((p) => p.lat)) + 0.01;

  const width = 480;
  const height = 280;
  const pad = 24;

  function project(lon: number, lat: number) {
    const x = pad + ((lon - west) / Math.max(east - west, 0.0001)) * (width - pad * 2);
    const y = height - pad - ((lat - south) / Math.max(north - south, 0.0001)) * (height - pad * 2);
    return { x, y };
  }

  return (
    <div className="rounded-lg border border-forge-600/50 bg-forge-950/60 p-3">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="Capture point map">
        <defs>
          <pattern id="capture-grid" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M 24 0 L 0 0 0 24" fill="none" stroke="rgba(74,155,155,0.08)" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width={width} height={height} fill="url(#capture-grid)" />
        {points.map((point, index) => {
          const { x, y } = project(point.lon, point.lat);
          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r={5}
                fill={point.flagged ? '#c4784a' : '#4a9b9b'}
                stroke="#e6e2d8"
                strokeWidth="1"
              />
              {point.label ? (
                <text x={x + 8} y={y + 4} fill="#9a9488" fontSize="10" fontFamily="monospace">
                  {point.label}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
      <p className="mt-2 font-mono text-[11px] text-sediment-dim">
        {points.length} points · bounds [{west.toFixed(3)}, {south.toFixed(3)}, {east.toFixed(3)}, {north.toFixed(3)}]
      </p>
    </div>
  );
}