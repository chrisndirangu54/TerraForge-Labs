import { FormEvent, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { CashflowPanel } from '../components/financial/CashflowPanel';
import { SensitivityChart } from '../components/financial/SensitivityChart';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { StatCard } from '../components/ui/StatCard';
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
      <PageHeader
        domain="geology"
        title="Ore Financials"
        description="NPV, IRR, payback, cash flow schedule, and price-risk Monte Carlo for mineral projects."
      />

      <form
        onSubmit={runAnalysis}
        className="mb-8 grid max-w-2xl gap-4 rounded-xl border border-forge-600/50 bg-forge-900/40 p-5"
      >
        <label className="flex flex-col gap-1 text-sm text-sediment-muted">
          Commodity
          <select
            className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
          >
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

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Ore tonnes (life-of-mine)
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={oreTonnes}
              onChange={(e) => setOreTonnes(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Grade {preset ? `(${preset.grade_unit})` : ''}
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Recovery (0–1)
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={recovery}
              onChange={(e) => setRecovery(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Metal price (USD)
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={metalPrice}
              onChange={(e) => setMetalPrice(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Opex (USD / tonne ore)
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={opex}
              onChange={(e) => setOpex(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Capex (USD)
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={capex}
              onChange={(e) => setCapex(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Mine life (years)
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={mineLife}
              onChange={(e) => setMineLife(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-sediment-muted">
            Discount rate
            <input
              className="rounded-lg border border-forge-600 bg-forge-950 px-3 py-2 text-sediment"
              value={discountRate}
              onChange={(e) => setDiscountRate(e.target.value)}
            />
          </label>
        </div>

        <label className="flex items-center gap-2 text-sm text-sediment-muted">
          <input
            type="checkbox"
            checked={runMonteCarlo}
            onChange={(e) => setRunMonteCarlo(e.target.checked)}
          />
          Run price Monte Carlo
        </label>

        {selectedProject ? (
          <p className="text-xs text-sediment-dim">
            Linked project: {selectedProject.name} — grade from geodata when left blank.
          </p>
        ) : (
          <p className="text-xs text-sediment-dim">No project selected; Matuu synthetic grade used.</p>
        )}

        <Button type="submit" variant="primary" disabled={loading}>
          {loading ? 'Analyzing…' : 'Run financial analysis'}
        </Button>
      </form>

      {error ? <pre className="tf-error mb-6">{error}</pre> : null}

      {analysis ? (
        <div className="tf-stagger space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="NPV" value={formatUsd(analysis.metrics.npv_usd)} accent="ore" />
            <StatCard label="IRR" value={formatPct(analysis.metrics.irr)} accent="mineral" />
            <StatCard
              label="Payback"
              value={
                analysis.metrics.payback_years != null
                  ? `${analysis.metrics.payback_years.toFixed(1)} yrs`
                  : 'n/a'
              }
              accent="strata"
            />
            <StatCard
              label="Annual revenue"
              value={formatUsd(analysis.annual.annual_revenue_usd)}
              accent="moss"
            />
          </div>

          {analysis.grade_from_geodata ? (
            <p className="text-sm text-sediment-muted">
              Grade from geodata: {analysis.grade_from_geodata.grade.toFixed(1)}{' '}
              {analysis.grade_from_geodata.grade_unit} (
              {analysis.grade_from_geodata.observation_count} samples)
            </p>
          ) : null}

          <Card title="Cash flow schedule" subtitle="Annual flows and cumulative position" accent="ore">
            <CashflowPanel
              cashFlows={analysis.cash_flows}
              paybackYears={analysis.metrics.payback_years}
              npvUsd={analysis.metrics.npv_usd}
            />
          </Card>

          <div className="grid gap-5 lg:grid-cols-2">
            {analysis.monte_carlo ? (
              <Card title="Price risk" subtitle="Monte Carlo NPV bands" accent="mineral">
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg border border-forge-600/40 bg-forge-950/50 p-3">
                      <p className="tf-label">P10</p>
                      <p className="font-mono text-sm text-ore-300">
                        {formatUsd(analysis.monte_carlo.npv.p10_usd)}
                      </p>
                    </div>
                    <div className="rounded-lg border border-forge-600/40 bg-forge-950/50 p-3">
                      <p className="tf-label">P50</p>
                      <p className="font-mono text-sm text-mineral-300">
                        {formatUsd(analysis.monte_carlo.npv.p50_usd)}
                      </p>
                    </div>
                    <div className="rounded-lg border border-forge-600/40 bg-forge-950/50 p-3">
                      <p className="tf-label">P90</p>
                      <p className="font-mono text-sm text-moss-400">
                        {formatUsd(analysis.monte_carlo.npv.p90_usd)}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-sediment-muted">
                    Positive NPV probability:{' '}
                    <span className="font-mono text-ore-300">
                      {(analysis.monte_carlo.npv.positive_probability * 100).toFixed(0)}%
                    </span>
                  </p>
                </div>
              </Card>
            ) : null}

            {sensitivity ? (
              <Card title="Sensitivity" subtitle="Top NPV drivers" accent="mineral">
                <SensitivityChart
                  rows={sensitivity.tornado}
                  baseNpvUsd={sensitivity.base_npv_usd}
                />
              </Card>
            ) : null}
          </div>

          <Card title="Operating summary">
            <dl className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="tf-label">Recovered metal / year</dt>
                <dd className="font-mono text-sediment">
                  {analysis.annual.annual_metal_tonnes.toFixed(2)} t
                </dd>
              </div>
              <div>
                <dt className="tf-label">Annual opex</dt>
                <dd className="font-mono text-sediment">
                  {formatUsd(analysis.annual.annual_opex_usd)}
                </dd>
              </div>
              <div>
                <dt className="tf-label">Annual EBITDA</dt>
                <dd className="font-mono text-sediment">
                  {formatUsd(analysis.annual.annual_ebitda_usd)}
                </dd>
              </div>
              <div>
                <dt className="tf-label">Undiscounted cash flow</dt>
                <dd className="font-mono text-sediment">
                  {formatUsd(analysis.metrics.undiscounted_cash_flow_usd)}
                </dd>
              </div>
            </dl>
          </Card>
        </div>
      ) : null}
    </div>
  );
}