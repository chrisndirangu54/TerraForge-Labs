import { FormEvent, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type CommodityPreset = {
  name: string;
  grade_unit: string;
  default_grade: number;
  recovery: number;
  metal_price_usd: number;
  price_unit: string;
  opex_usd_per_tonne_ore: number;
};

type PresetsResponse = {
  commodities: Record<string, CommodityPreset>;
  defaults: { discount_rate: number; price_volatility: number };
};

type AnalyzeResponse = {
  commodity: string;
  inputs: Record<string, number | string>;
  resource: Record<string, number>;
  annual: Record<string, number>;
  metrics: {
    npv_usd: number;
    irr: number | null;
    payback_years: number | null;
    undiscounted_cash_flow_usd: number;
  };
  cash_flows: Array<{ year: number; amount_usd: number }>;
  monte_carlo?: {
    npv: {
      p10_usd: number;
      p50_usd: number;
      p90_usd: number;
      mean_usd: number;
      positive_probability: number;
    };
    irr: { p10: number | null; p50: number | null; p90: number | null };
  };
  grade_from_geodata?: {
    grade: number;
    grade_unit: string;
    observation_count: number;
  };
};

type SensitivityResponse = {
  base_npv_usd: number;
  tornado: Array<{
    variable: string;
    factor: number;
    npv_usd: number;
    delta_npv_usd: number;
  }>;
};

function formatUsd(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value: number | null) {
  if (value === null) return 'n/a';
  return `${(value * 100).toFixed(1)}%`;
}

export function FinancialAnalysisPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [presets, setPresets] = useState<PresetsResponse | null>(null);
  const [commodity, setCommodity] = useState('ta');
  const [oreTonnes, setOreTonnes] = useState('3000000');
  const [grade, setGrade] = useState('');
  const [recovery, setRecovery] = useState('');
  const [metalPrice, setMetalPrice] = useState('');
  const [opex, setOpex] = useState('');
  const [capex, setCapex] = useState('60000000');
  const [mineLife, setMineLife] = useState('10');
  const [discountRate, setDiscountRate] = useState('0.12');
  const [runMonteCarlo, setRunMonteCarlo] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResponse | null>(null);

  useEffect(() => {
    apiGet<PresetsResponse>('/financial/ore/presets')
      .then(setPresets)
      .catch(() => setPresets(null));
  }, []);

  useEffect(() => {
    const preset = presets?.commodities[commodity];
    if (!preset) return;
    if (!grade) setGrade(String(preset.default_grade));
    if (!recovery) setRecovery(String(preset.recovery));
    if (!metalPrice) setMetalPrice(String(preset.metal_price_usd));
    if (!opex) setOpex(String(preset.opex_usd_per_tonne_ore));
    if (presets?.defaults.discount_rate) {
      setDiscountRate(String(presets.defaults.discount_rate));
    }
  }, [presets, commodity, grade, recovery, metalPrice, opex]);

  function buildPayload() {
    return {
      commodity,
      ore_tonnes: Number(oreTonnes),
      grade: grade ? Number(grade) : undefined,
      recovery: recovery ? Number(recovery) : undefined,
      metal_price_usd: metalPrice ? Number(metalPrice) : undefined,
      opex_usd_per_tonne_ore: opex ? Number(opex) : undefined,
      capex_usd: Number(capex),
      mine_life_years: Number(mineLife),
      discount_rate: Number(discountRate),
      project_id: selectedProject?.id,
      element: commodity === 'ta' ? 'ta_ppm' : `${commodity}_ppm`,
      dataset: selectedProject ? undefined : 'matuu_synthetic',
      run_monte_carlo: runMonteCarlo,
      monte_carlo_iterations: 500,
    };
  }

  async function runAnalysis(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setAnalysis(null);
    setSensitivity(null);
    try {
      const payload = buildPayload();
      const [result, sens] = await Promise.all([
        apiPost<AnalyzeResponse>('/financial/ore/analyze', payload),
        apiPost<SensitivityResponse>('/financial/ore/sensitivity', payload),
      ]);
      setAnalysis(result);
      setSensitivity(sens);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const preset = presets?.commodities[commodity];

  return (
    <div>
      <h2>Ore Financial Analysis</h2>
      <p>
        NPV, IRR, payback, and price-risk Monte Carlo for mineral ore projects. Grade can
        auto-fill from kriging/ingest when a project is selected.
      </p>

      <form
        onSubmit={runAnalysis}
        style={{
          display: 'grid',
          gap: '0.75rem',
          maxWidth: 520,
          padding: '1rem',
          border: '1px solid #ddd',
          borderRadius: 6,
        }}
      >
        <label>
          Commodity
          <select value={commodity} onChange={(e) => setCommodity(e.target.value)}>
            {presets
              ? Object.entries(presets.commodities).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value.name}
                  </option>
                ))
              : (
                <option value="ta">Tantalum (Ta)</option>
              )}
          </select>
        </label>
        <label>
          Ore tonnes (life-of-mine)
          <input value={oreTonnes} onChange={(e) => setOreTonnes(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Grade {preset ? `(${preset.grade_unit})` : ''}
          <input value={grade} onChange={(e) => setGrade(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Recovery (0–1)
          <input value={recovery} onChange={(e) => setRecovery(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Metal price (USD)
          <input value={metalPrice} onChange={(e) => setMetalPrice(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Opex (USD / tonne ore)
          <input value={opex} onChange={(e) => setOpex(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Capex (USD)
          <input value={capex} onChange={(e) => setCapex(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Mine life (years)
          <input value={mineLife} onChange={(e) => setMineLife(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Discount rate
          <input value={discountRate} onChange={(e) => setDiscountRate(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <input
            type="checkbox"
            checked={runMonteCarlo}
            onChange={(e) => setRunMonteCarlo(e.target.checked)}
          />
          Run price Monte Carlo
        </label>
        {selectedProject ? (
          <p style={{ fontSize: '0.85rem', margin: 0 }}>
            Linked project: {selectedProject.name} — grade from geodata when left blank.
          </p>
        ) : (
          <p style={{ fontSize: '0.85rem', margin: 0 }}>No project selected; Matuu synthetic grade used.</p>
        )}
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Run financial analysis'}
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}

      {analysis ? (
        <section style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Key metrics</h3>
          <table style={{ borderCollapse: 'collapse', minWidth: 360 }}>
            <tbody>
              <tr>
                <td style={{ padding: '0.25rem 0.75rem 0.25rem 0' }}>NPV</td>
                <td>{formatUsd(analysis.metrics.npv_usd)}</td>
              </tr>
              <tr>
                <td style={{ padding: '0.25rem 0.75rem 0.25rem 0' }}>IRR</td>
                <td>{formatPct(analysis.metrics.irr)}</td>
              </tr>
              <tr>
                <td style={{ padding: '0.25rem 0.75rem 0.25rem 0' }}>Payback</td>
                <td>
                  {analysis.metrics.payback_years !== null
                    ? `${analysis.metrics.payback_years.toFixed(1)} years`
                    : 'n/a'}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '0.25rem 0.75rem 0.25rem 0' }}>Annual revenue</td>
                <td>{formatUsd(analysis.annual.annual_revenue_usd)}</td>
              </tr>
              <tr>
                <td style={{ padding: '0.25rem 0.75rem 0.25rem 0' }}>Recovered metal / year</td>
                <td>{analysis.annual.annual_metal_tonnes.toFixed(2)} t</td>
              </tr>
            </tbody>
          </table>

          {analysis.grade_from_geodata ? (
            <p style={{ fontSize: '0.85rem' }}>
              Grade from geodata: {analysis.grade_from_geodata.grade.toFixed(1)}{' '}
              {analysis.grade_from_geodata.grade_unit} (
              {analysis.grade_from_geodata.observation_count} samples)
            </p>
          ) : null}

          {analysis.monte_carlo ? (
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ margin: '0 0 0.5rem' }}>Price risk (Monte Carlo)</h4>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>
                NPV P10 / P50 / P90: {formatUsd(analysis.monte_carlo.npv.p10_usd)} /{' '}
                {formatUsd(analysis.monte_carlo.npv.p50_usd)} /{' '}
                {formatUsd(analysis.monte_carlo.npv.p90_usd)} — positive probability{' '}
                {(analysis.monte_carlo.npv.positive_probability * 100).toFixed(0)}%
              </p>
            </div>
          ) : null}

          {sensitivity ? (
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ margin: '0 0 0.5rem' }}>Sensitivity (top drivers)</h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.9rem' }}>
                {sensitivity.tornado.slice(0, 5).map((row) => (
                  <li key={`${row.variable}-${row.factor}`}>
                    {row.variable} ×{row.factor.toFixed(1)} → ΔNPV{' '}
                    {formatUsd(row.delta_npv_usd)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <details style={{ marginTop: '1rem' }}>
            <summary>Cash flows</summary>
            <pre style={{ fontSize: '0.8rem' }}>{JSON.stringify(analysis.cash_flows, null, 2)}</pre>
          </details>
        </section>
      ) : null}
    </div>
  );
}