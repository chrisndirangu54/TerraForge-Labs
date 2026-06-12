import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type CaptureChartProps = {
  series: Array<{ label: string; value: number }>;
};

export function CaptureChart({ series }: CaptureChartProps) {
  if (!series.length) return null;

  return (
    <div className="h-56 rounded-lg border border-forge-600/50 bg-forge-950/40 p-2">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={series}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(74,155,155,0.15)" />
          <XAxis dataKey="label" tick={{ fill: '#9a9488', fontSize: 10 }} />
          <YAxis tick={{ fill: '#9a9488', fontSize: 10 }} />
          <Tooltip
            contentStyle={{
              background: '#141d18',
              border: '1px solid #2f3d34',
              borderRadius: 8,
              color: '#e6e2d8',
            }}
          />
          <Bar dataKey="value" fill="#4a9b9b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}