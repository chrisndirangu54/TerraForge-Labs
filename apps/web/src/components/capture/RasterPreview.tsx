type RasterLayer = {
  name: string;
  preview_url?: string;
  tile_url_template?: string;
  storage_key?: string;
  width?: number;
  height?: number;
};

type RasterPreviewProps = {
  layers: RasterLayer[];
  bounds?: number[] | null;
};

export function RasterPreview({ layers, bounds }: RasterPreviewProps) {
  if (!layers.length) return null;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {layers.map((layer) => (
        <a
          key={layer.name}
          href={layer.preview_url ?? '#'}
          target="_blank"
          rel="noreferrer"
          className="group rounded-lg border border-forge-600/50 bg-forge-900/40 p-4 transition-colors hover:border-mineral-500/40"
        >
          <p className="font-display text-sm font-semibold text-ore-300 group-hover:text-ore-200">
            {layer.name}
          </p>
          <p className="mt-1 font-mono text-[11px] text-sediment-dim">
            {layer.width && layer.height ? `${layer.width}×${layer.height}` : 'COG layer'}
          </p>
          {layer.storage_key ? (
            <p className="mt-2 truncate font-mono text-[10px] text-mineral-500">{layer.storage_key}</p>
          ) : null}
          {layer.preview_url ? (
            <img
              src={layer.preview_url}
              alt={`${layer.name} preview`}
              className="mt-3 h-24 w-full rounded border border-forge-600/40 object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          ) : null}
        </a>
      ))}
      {bounds ? (
        <p className="sm:col-span-2 font-mono text-[11px] text-sediment-dim">
          Bounds: [{bounds.map((v) => v.toFixed(4)).join(', ')}]
        </p>
      ) : null}
    </div>
  );
}