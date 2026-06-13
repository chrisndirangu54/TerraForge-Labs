import type { DepositBlock } from './DepositCesiumViewer';

type DepositBlockFallbackProps = {
  blocks: DepositBlock[];
  className?: string;
};

function gradeColor(grade: number): string {
  const ratio = Math.min(Math.max((grade - 80) / 120, 0), 1);
  const r = Math.round(80 + ratio * 175);
  const g = Math.round(40 + (1 - ratio) * 80);
  const b = Math.round(30 + (1 - ratio) * 40);
  return `rgb(${r}, ${g}, ${b})`;
}

export function DepositBlockFallback({ blocks, className = '' }: DepositBlockFallbackProps) {
  const geoBlocks = blocks.filter((block) => block.lon != null && block.lat != null);

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-xl border border-forge-600/60 bg-forge-950/80 ${className}`}
    >
      <div className="border-b border-forge-600/40 px-4 py-2 text-xs text-sediment-muted">
        Canvas fallback viewer · {geoBlocks.length} blocks
      </div>
      <div className="relative flex-1 min-h-[320px] p-4">
        {geoBlocks.length === 0 ? (
          <p className="absolute inset-0 flex items-center justify-center text-sm text-sediment-dim">
            Generate deposit model to load blocks
          </p>
        ) : (
          <div className="grid h-full grid-cols-5 gap-2">
            {geoBlocks.map((block, index) => {
              const grade = Number(block.ta_ppm_mean ?? 100);
              const depth = index % 5;
              return (
                <div
                  key={`${block.lon}-${block.lat}-${index}`}
                  className="flex flex-col items-center justify-end"
                  title={`${grade.toFixed(0)} ppm Ta`}
                >
                  <div
                    className="w-full rounded-sm border border-white/20"
                    style={{
                      height: `${28 + depth * 10 + (grade / 220) * 24}px`,
                      backgroundColor: block.color_hex ?? gradeColor(grade),
                    }}
                  />
                  <span className="mt-1 font-mono text-[9px] text-sediment-dim">
                    {grade.toFixed(0)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}