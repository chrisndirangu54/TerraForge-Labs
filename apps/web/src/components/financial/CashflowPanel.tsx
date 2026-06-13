import { useMemo } from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export type CashFlowRow = {
  year: number;
  amount_usd: number;
};

type CashflowPanelProps = {
  cashFlows: CashFlowRow[];
  paybackYears?: number | null;
  npvUsd?: number;
};

function formatUsd(value: number, compact = false) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 0,
  }).format(value);
}

const tooltipStyle = {
  background: '#141d18',
  border: '1px solid #2f3d34',
  borderRadius: 8,
  color: '#e6e2d8',
};

export function CashflowPanel({ cashFlows, paybackYears, npvUsd }: CashflowPanelProps) {
  const { chartData, totalUndiscounted, peakOutflow, peakInflow } = useMemo(() => {
    let cumulative = 0;
    let peakOutflow = 0;
    let peakInflow = 0;

    const chartData = cashFlows.map((row) => {
      cumulative += row.amount_usd;
      peakOutflow = Math.min(peakOutflow, row.amount_usd);
      peakInflow = Math.max(peakInflow, row.amount_usd);
      return {
        label: row.year === 0 ? 'Y0' : `Y${row.year}`,
        year: row.year,
        amount: row.amount_usd,
        cumulative,
        positive: row.amount_usd >= 0,
      };
    });

    const totalUndiscounted = cashFlows.reduce((sum, row) => sum + row.amount_usd, 0);

    return {
      chartData,
      totalUndiscounted,
      peakOutflow,
      peakInflow,
    };
  }, [cashFlows]);

  if (!cashFlows.length) {
    return (
      <p className="text-sm text-sediment-muted">No cash flow data — run an analysis first.</p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-forge-600/40 bg-forge-900/50 px-4 py-3">
          <p className="tf-label">Undiscounted total</p>
          <p className="font-display text-xl font-bold text-sediment">
            {formatUsd(totalUndiscounted)}
          </p>
        </div>
        <div className="rounded-lg border border-forge-600/40 bg-forge-900/50 px-4 py-3">
          <p className="tf-label">Peak annual inflow</p>
          <p className="font-display text-xl font-bold text-moss-400">
            {formatUsd(peakInflow)}
          </p>
        </div>
        <div className="rounded-lg border border-forge-600/40 bg-forge-900/50 px-4 py-3">
          <p className="tf-label">Initial CAPEX (Y0)</p>
          <p className="font-display text-xl font-bold text-ore-400">
            {formatUsd(cashFlows[0]?.amount_usd ?? 0)}
          </p>
        </div>
      </div>

      <div className="h-72 rounded-xl border border-forge-600/50 bg-forge-950/40 p-3">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(74,155,155,0.12)" />
            <XAxis
              dataKey="label"
              tick={{ fill: '#9a9488', fontSize: 11 }}
              axisLine={{ stroke: '#2f3d34' }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: '#9a9488', fontSize: 10 }}
              tickFormatter={(v) => formatUsd(Number(v), true)}
              axisLine={{ stroke: '#2f3d34' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: '#9a9488', fontSize: 10 }}
              tickFormatter={(v) => formatUsd(Number(v), true)}
              axisLine={{ stroke: '#2f3d34' }}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value: number, name: string) => [
                formatUsd(value),
                name === 'amount' ? 'Annual cash flow' : 'Cumulative',
              ]}
              labelFormatter={(label) => `Year ${label}`}
            />
            <Legend
              wrapperStyle={{ fontSize: 11, color: '#9a9488' }}
              formatter={(value) =>
                value === 'amount' ? 'Annual cash flow' : 'Cumulative position'
              }
            />
            <ReferenceLine yAxisId="left" y={0} stroke="#4a9b9b" strokeDasharray="4 4" />
            {paybackYears != null ? (
              <ReferenceLine
                yAxisId="left"
                x={`Y${Math.ceil(paybackYears)}`}
                stroke="#c45c26"
                strokeDasharray="3 3"
                label={{
                  value: `Payback ~${paybackYears.toFixed(1)}y`,
                  fill: '#c45c26',
                  fontSize: 10,
                  position: 'insideTopRight',
                }}
              />
            ) : null}
            <Bar
              yAxisId="left"
              dataKey="amount"
              name="amount"
              radius={[4, 4, 0, 0]}
              fill="#4a9b9b"
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              shape={(props: any) => {
                const { x, y, width, height, payload } = props;
                const fill = payload.positive ? '#5a7a52' : '#c45c26';
                const h = Math.abs(height);
                const yPos = height < 0 ? y + height : y;
                return (
                  <rect x={x} y={yPos} width={width} height={h} fill={fill} rx={4} ry={4} />
                );
              }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cumulative"
              name="cumulative"
              stroke="#d4a574"
              strokeWidth={2}
              dot={{ r: 3, fill: '#d4a574', strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {npvUsd != null ? (
        <p className="text-xs text-sediment-dim">
          NPV (discounted): <span className="font-mono text-ore-300">{formatUsd(npvUsd)}</span>
          {' · '}
          Cumulative line shows undiscounted project cash position by year.
        </p>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-forge-600/40">
        <table className="w-full min-w-[420px] text-left text-sm">
          <thead className="border-b border-forge-600/40 bg-forge-900/60 text-xs uppercase tracking-wide text-sediment-dim">
            <tr>
              <th className="px-4 py-2 font-medium">Year</th>
              <th className="px-4 py-2 font-medium">Annual cash flow</th>
              <th className="px-4 py-2 font-medium">Cumulative</th>
              <th className="px-4 py-2 font-medium">Phase</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((row) => (
              <tr
                key={row.year}
                className="border-b border-forge-600/20 last:border-0 hover:bg-forge-800/30"
              >
                <td className="px-4 py-2 font-mono text-sediment-muted">
                  {row.year === 0 ? 'Y0 (CAPEX)' : `Year ${row.year}`}
                </td>
                <td
                  className={`px-4 py-2 font-mono ${
                    row.amount < 0 ? 'text-ore-400' : 'text-moss-400'
                  }`}
                >
                  {formatUsd(row.amount)}
                </td>
                <td
                  className={`px-4 py-2 font-mono ${
                    row.cumulative < 0 ? 'text-strata-300' : 'text-mineral-300'
                  }`}
                >
                  {formatUsd(row.cumulative)}
                </td>
                <td className="px-4 py-2 text-sediment-dim">
                  {row.year === 0 ? 'Investment' : row.cumulative < 0 ? 'Payback period' : 'Free cash'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}