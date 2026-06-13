import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type TornadoRow = {
  variable: string;
  factor: number;
  npv_usd: number;
  delta_npv_usd: number;
};

type SensitivityChartProps = {
  rows: TornadoRow[];
  baseNpvUsd: number;
};

function formatUsd(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

export function SensitivityChart({ rows, baseNpvUsd }: SensitivityChartProps) {
  const byVariable = new Map<string, TornadoRow>();
  rows.forEach((row) => {
    const existing = byVariable.get(row.variable);
    if (!existing || Math.abs(row.delta_npv_usd) > Math.abs(existing.delta_npv_usd)) {
      byVariable.set(row.variable, row);
    }
  });

  const chartData = Array.from(byVariable.values())
    .sort((a, b) => Math.abs(b.delta_npv_usd) - Math.abs(a.delta_npv_usd))
    .slice(0, 6)
    .map((row) => ({
      name: row.variable.replace(/_/g, ' '),
      delta: row.delta_npv_usd,
      npv: row.npv_usd,
    }));

  if (!chartData.length) return null;

  return (
    <div className="h-56 rounded-xl border border-forge-600/50 bg-forge-950/40 p-3">
      <p className="mb-2 text-xs text-sediment-dim">
        Tornado sensitivity · base NPV {formatUsd(baseNpvUsd)}
      </p>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(74,155,155,0.12)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: '#9a9488', fontSize: 10 }}
            tickFormatter={(v) => formatUsd(Number(v))}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={100}
            tick={{ fill: '#9a9488', fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{
              background: '#141d18',
              border: '1px solid #2f3d34',
              borderRadius: 8,
              color: '#e6e2d8',
            }}
            formatter={(value: number) => [formatUsd(value), 'ΔNPV']}
          />
          <Bar dataKey="delta" radius={[0, 4, 4, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.delta >= 0 ? '#5a7a52' : '#c45c26'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}