import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

type VariogramAnalyzeResponse = {
  empirical: {
    lags: number[];
    semivariance: number[];
  };
  fitted: {
    model: string;
    curve: Array<{ distance: number; gamma: number }>;
  };
  cross_validation: {
    rmse: number;
    mae: number;
    bias: number;
    n_folds: number;
  };
};

export function VariogramChart({ analysis }: { analysis: VariogramAnalyzeResponse }) {
  const empirical = analysis.empirical.lags.map((lag, index) => ({
    distance: lag,
    empiricalGamma: analysis.empirical.semivariance[index] ?? 0,
  }));
  const fitted = analysis.fitted.curve.map((point) => ({
    distance: point.distance,
    fittedGamma: point.gamma,
  }));
  const chartData = [...empirical, ...fitted];

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="distance" type="number" name="distance" unit=" m" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Scatter name="Empirical" data={empirical} dataKey="empiricalGamma" fill="#2563eb" />
            <Line
              type="monotone"
              data={fitted}
              dataKey="fittedGamma"
              stroke="#dc2626"
              dot={false}
              name={`Fitted ${analysis.fitted.model}`}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
          gap: '0.75rem',
        }}
      >
        <Metric label="CV RMSE" value={analysis.cross_validation.rmse.toFixed(3)} />
        <Metric label="CV MAE" value={analysis.cross_validation.mae.toFixed(3)} />
        <Metric label="CV bias" value={analysis.cross_validation.bias.toFixed(3)} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: '1px solid #ddd', borderRadius: 6, padding: '0.75rem' }}>
      <div style={{ fontSize: '0.8rem', color: '#666' }}>{label}</div>
      <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{value}</div>
    </div>
  );
}