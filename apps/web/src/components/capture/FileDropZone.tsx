import { DragEvent, useRef, useState } from 'react';

const ACCEPTED = '.csv,.tsv,.xml,.json,.geojson,.pdf,.txt,.nmea,.las,.laz';

type FileDropZoneProps = {
  onFiles: (files: FileList) => void;
  disabled?: boolean;
};

export function FileDropZone({ onFiles, disabled }: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    if (disabled || !event.dataTransfer.files.length) return;
    onFiles(event.dataTransfer.files);
  }

  return (
    <div
      className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
        dragging
          ? 'border-mineral-500/60 bg-mineral-600/10'
          : 'border-forge-600/60 bg-forge-900/30 hover:border-mineral-500/40'
      } ${disabled ? 'opacity-50' : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <p className="font-display text-lg text-sediment">Drop transferable files here</p>
      <p className="mt-2 text-sm text-sediment-muted">
        CSV, TSV, XML, GeoJSON, PDF, NMEA, LAS/LAZ
      </p>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {['CSV', 'PDF', 'GeoJSON', 'XML', 'LAZ'].map((fmt) => (
          <span key={fmt} className="tf-badge border-forge-500/50 text-sediment-dim">
            {fmt}
          </span>
        ))}
      </div>
      <button
        type="button"
        className="mt-5 rounded-lg border border-forge-600 bg-forge-800 px-4 py-2 text-sm text-sediment hover:border-mineral-500/40"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
      >
        Browse files
      </button>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept={ACCEPTED}
        multiple
        disabled={disabled}
        onChange={(e) => e.target.files && onFiles(e.target.files)}
      />
    </div>
  );
}