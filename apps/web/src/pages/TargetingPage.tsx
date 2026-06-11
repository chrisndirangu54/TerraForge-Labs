import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type FusionResult = {
  composite_score: number;
  components: Record<string, number>;
  ranked_pathfinders?: Array<{ element: string; halo_score: number }>;
};

type DrillPlan = {
  selected_holes: Array<Record<string, unknown>>;
  planned_metres: number;
  estimated_spend_usd: number;
  remaining_budget_usd: number;
};

const SAMPLE_TARGETS = [
  { hole_id: 'DDH-01', depth_m: 200, target_probability: 0.85, uncertainty_reduction: 0.7, lon: 37.5, lat: -1.15 },
  { hole_id: 'DDH-02', depth_m: 250, target_probability: 0.78, uncertainty_reduction: 0.62, lon: 37.52, lat: -1.14 },
  { hole_id: 'DDH-03', depth_m: 150, target_probability: 0.66, uncertainty_reduction: 0.55, lon: 37.48, lat: -1.16 },
];

const SAMPLE_GEOCHEM = [
  { lon: 37.5, lat: -1.15, As: 45, Sb: 12, Bi: 3.2 },
  { lon: 37.51, lat: -1.14, As: 62, Sb: 18, Bi: 4.1 },
  { lon: 37.49, lat: -1.16, As: 28, Sb: 8, Bi: 1.9 },
];

export function TargetingPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [depositStyle, setDepositStyle] = useState('orogenic_au');
  const [budgetUsd, setBudgetUsd] = useState(75000);
  const [fusion, setFusion] = useState<FusionResult | null>(null);
  const [drillPlan, setDrillPlan] = useState<DrillPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runFusion(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const [anomaly, pathfinder] = await Promise.all([
        apiGet<Record<string, unknown>>('/geobotany/anomaly-map', {
          project_id: selectedProject?.id ?? '',
        }),
        apiPost<Record<string, unknown>>('/targeting/pathfinder-analysis', {
          samples: SAMPLE_GEOCHEM,
          deposit_style: depositStyle,
        }),
      ]);

      const components = {
        vegetation_stress: Number(anomaly.vegetation_stress ?? 75),
        indicator_species: Number(anomaly.indicator_species ?? 80),
        biogeochemistry: Number(anomaly.biogeochemistry ?? 70),
        pathfinder_halo: Number(
          ((pathfinder.ranked_pathfinders as Array<{ halo_score: number }>) ?? [])[0]?.halo_score ?? 0.5,
        ) * 100,
      };
      const composite =
        Number(anomaly.composite_score) ||
        Object.values(components).reduce((sum, v) => sum + v, 0) / Object.keys(components).length;

      setFusion({
        composite_score: Math.round(composite * 10) / 10,
        components,
        ranked_pathfinders: pathfinder.ranked_pathfinders as FusionResult['ranked_pathfinders'],
      });

      const plan = await apiPost<DrillPlan>('/targeting/drill-plan-optimise', {
        targets: SAMPLE_TARGETS,
        budget_usd: budgetUsd,
        max_depth_m: 250,
      });
      setDrillPlan(plan);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Targeting</h2>
      <p>Fusion score across geobotany anomalies and pathfinder geochemistry, plus optimised drill plan.</p>

      <form
        onSubmit={runFusion}
        style={{
          display: 'grid',
          gap: '0.75rem',
          maxWidth: 480,
          padding: '1rem',
          border: '1px solid #ddd',
          borderRadius: 6,
          marginBottom: '1.5rem',
        }}
      >
        <label>
          Deposit style
          <select value={depositStyle} onChange={(e) => setDepositStyle(e.target.value)}>
            <option value="orogenic_au">Orogenic Au</option>
            <option value="epithermal_au">Epithermal Au</option>
            <option value="porphyry_cu">Porphyry Cu</option>
            <option value="critical_metals">Critical metals</option>
          </select>
        </label>
        <label>
          Drill budget (USD)
          <input
            type="number"
            min={10000}
            step={5000}
            value={budgetUsd}
            onChange={(e) => setBudgetUsd(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Computing...' : 'Compute fusion score & drill plan'}
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}

      {fusion ? (
        <section style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem' }}>Fusion score: {fusion.composite_score}</h3>
          <ul>
            {Object.entries(fusion.components).map(([key, value]) => (
              <li key={key}>
                {key.replace(/_/g, ' ')}: {value.toFixed(1)}
              </li>
            ))}
          </ul>
          {fusion.ranked_pathfinders ? (
            <div>
              <strong>Top pathfinders</strong>
              <ul>
                {fusion.ranked_pathfinders.slice(0, 3).map((pf) => (
                  <li key={pf.element}>
                    {pf.element}: {pf.halo_score}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}

      {drillPlan ? (
        <section>
          <h3 style={{ fontSize: '1rem' }}>Optimised drill plan</h3>
          <p>
            {drillPlan.planned_metres} m planned · ${drillPlan.estimated_spend_usd.toLocaleString()} spend · $
            {drillPlan.remaining_budget_usd.toLocaleString()} remaining
          </p>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Hole</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Depth (m)</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Info gain</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Cost (USD)</th>
              </tr>
            </thead>
            <tbody>
              {drillPlan.selected_holes.map((hole) => (
                <tr key={String(hole.hole_id)}>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{String(hole.hole_id)}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{String(hole.depth_m)}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    {String(hole.information_gain)}
                  </td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    {String(hole.estimated_cost_usd)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}
    </div>
  );
}