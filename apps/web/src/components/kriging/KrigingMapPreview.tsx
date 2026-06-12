type KrigingMapPreviewProps = {
  previewUrl: string;
  tileTemplate?: string;
  bounds?: number[];
};

export function KrigingMapPreview({
  previewUrl,
  tileTemplate,
  bounds,
}: KrigingMapPreviewProps) {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
  const resolvedPreview = previewUrl.startsWith('http')
    ? previewUrl
    : `${apiBase}${previewUrl}`;

  return (
    <div style={{ display: 'grid', gap: '0.75rem' }}>
      <img
        src={resolvedPreview}
        alt="Kriging COG preview"
        style={{ width: '100%', maxWidth: 520, border: '1px solid #ddd', borderRadius: 6 }}
      />
      {tileTemplate ? (
        <code style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>{tileTemplate}</code>
      ) : null}
      {bounds ? (
        <div style={{ fontSize: '0.85rem', color: '#555' }}>
          Bounds: [{bounds.map((value) => value.toFixed(4)).join(', ')}]
        </div>
      ) : null}
    </div>
  );
}