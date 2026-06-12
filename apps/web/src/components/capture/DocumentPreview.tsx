type DocumentPreviewProps = {
  title: string;
  excerpt: string;
  keywords?: string[];
  pages?: number;
  sizeBytes?: number;
};

export function DocumentPreview({
  title,
  excerpt,
  keywords = [],
  pages,
  sizeBytes,
}: DocumentPreviewProps) {
  return (
    <div className="rounded-lg border border-forge-600/50 bg-forge-900/40 p-5">
      <div className="mb-4 flex items-start gap-4">
        <div className="flex h-14 w-11 shrink-0 items-center justify-center rounded border border-ore-500/40 bg-forge-800 font-display text-xs font-bold text-ore-400">
          PDF
        </div>
        <div>
          <h4 className="font-display text-base text-sediment">{title}</h4>
          <p className="mt-1 font-mono text-xs text-sediment-dim">
            {pages ? `${pages} pages` : null}
            {pages && sizeBytes ? ' · ' : null}
            {sizeBytes ? `${Math.round(sizeBytes / 1024)} KB` : null}
          </p>
        </div>
      </div>
      {keywords.length ? (
        <div className="mb-3 flex flex-wrap gap-2">
          {keywords.map((keyword) => (
            <span key={keyword} className="tf-badge border-strata-400/40 bg-strata-500/10 text-strata-300">
              {keyword}
            </span>
          ))}
        </div>
      ) : null}
      <p className="text-sm leading-relaxed text-sediment-muted">{excerpt || 'No extractable text preview.'}</p>
    </div>
  );
}