import { useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { CaptureResultView } from '../components/capture/CaptureResultView';
import { inferDisplay } from '../components/results/inferDisplay';
import { Button } from '../components/ui/Button';
import { PageHeader } from '../components/ui/PageHeader';
import { useProjectStore } from '../stores/projectStore';

type Feature = {
  id: string;
  title: string;
  description: string;
  method: 'GET' | 'POST';
  path: string;
  body?: Record<string, unknown>;
};

const FEATURES: Feature[] = [
  { id: 'fusion', title: 'Fusion v2', description: 'Multi-source score + SHAP-style attribution', method: 'POST', path: '/platform/fusion/v2', body: { sources: { kriging_grade: 85, geobotany: 72, aeromag_structure: 60 } } },
  { id: 'drill', title: 'Drill plan v2', description: 'Budget + slope access + information gain', method: 'POST', path: '/platform/drill/plan-v2', body: { budget_usd: 400000, targets: [{ fusion_score: 80, slope_deg: 18, kriging_variance: 0.4 }] } },
  { id: 'qaqc', title: 'Assay QA/QC', description: 'Standards/blanks/duplicates → kriging gate', method: 'POST', path: '/platform/geochem/qaqc-pipeline', body: { project_id: 'matuu', samples: [{ sample_type: 'standard', expected_ppm: 100, measured_ppm: 102 }] } },
  { id: 'uav', title: 'UAV survey', description: 'Orthomosaic + DSM + change detection', method: 'POST', path: '/platform/uav/survey', body: { project_id: 'matuu', flight_id: 'uav-01' } },
  { id: 'aeromag', title: 'Aeromag + radiometrics', description: 'Structure likelihood map', method: 'POST', path: '/platform/aeromag/fusion', body: { mag_amplitude_nt: 140, radiometric_k_percent: 3.1 } },
  { id: 'lidar', title: 'LiDAR', description: 'DTM, slope, drill access', method: 'POST', path: '/platform/lidar/process', body: { storage_key: 'lidar/demo.laz' } },
  { id: 'dronecv', title: 'Drone video CV', description: 'Alteration + geobotany keyframes', method: 'POST', path: '/platform/drone/cv/analyze', body: { frame_count: 150 } },
  { id: 'gpr', title: 'GPR', description: 'Shallow structure interpretation', method: 'POST', path: '/platform/gpr/interpret', body: { max_depth_m: 10 } },
  { id: 'geomag', title: 'Geomagnetism', description: 'Gradient anomaly scoring', method: 'POST', path: '/platform/geomagnetism/analyze', body: { gradient_nt_m: 3.8 } },
  { id: 'tectonics', title: 'Plate tectonics', description: 'Regional structural context', method: 'POST', path: '/platform/tectonics/context', body: { lon: 37.5, lat: -1.15 } },
  { id: 'seismic', title: 'Seismology', description: 'Passive seismic summary', method: 'POST', path: '/platform/seismic/summary', body: { events: [{ magnitude: 2.8 }] } },
  { id: 'biogeochem', title: 'Biogeochemistry', description: 'ICP-MS ↔ species correlation', method: 'POST', path: '/platform/biogeochem/correlate', body: { samples: [{ Cu: 120, Ta: 8 }] } },
  { id: 'field', title: 'Field agent sync', description: 'Offline queue → kriging refresh', method: 'POST', path: '/platform/field-agent/sync', body: { queued_observations: [{ ta_ppm: 110 }], photos: [] } },
  { id: 'twin', title: 'Live NPV twin', description: 'Price–grade–recovery band', method: 'POST', path: '/platform/digital-twin/live-npv', body: { commodity: 'ta', ore_tonnes: 3000000, price_shock_pct: -8 } },
  { id: 'stop', title: 'Exploration stopping', description: 'Bayesian drill/no-drill criterion', method: 'POST', path: '/platform/exploration/stop-criterion', body: { marginal_npv_next_hole_usd: 180000, next_hole_cost_usd: 42000 } },
  { id: 'conformal', title: 'Conformal grade', description: 'Honest grade intervals for JORC', method: 'POST', path: '/platform/conformal/grade', body: { grades: [95, 110, 130, 88] } },
  { id: 'climate', title: 'Climate-risk NPV', description: 'Water/flood/energy scenarios', method: 'POST', path: '/platform/climate-risk/npv', body: { commodity: 'ta', ore_tonnes: 2500000, water_stress_index: 0.4 } },
  { id: 'iot', title: 'IoT ingest', description: 'Edge XRF/mag stream + QA flags', method: 'POST', path: '/platform/iot/ingest', body: { readings: [{ instrument_type: 'xrf_bruker', count_rate_cps: 250 }] } },
  { id: 'core', title: 'Core tray CV', description: 'RQD + fracture segmentation', method: 'POST', path: '/platform/core-tray/segment', body: { rqd_pct: 68 } },
  { id: 'evidence', title: 'Evidence bundle', description: 'Investor/JORC export package', method: 'POST', path: '/platform/evidence-bundle', body: { project_id: 'matuu', map_layers: ['kriging_grade'] } },
  { id: 'dataroom', title: 'Data room v2', description: 'Signed access + evidence bundle', method: 'POST', path: '/platform/data-room/v2', body: { project_id: 'matuu' } },
  { id: 'lineage', title: 'Lineage list', description: 'Artifact provenance records', method: 'GET', path: '/platform/lineage/list' },
  { id: 'inversion', title: '3D inversion job', description: 'MT/gravity/seismic partner pipeline', method: 'POST', path: '/platform/inversion/submit', body: { method: 'mt' } },
  { id: 'modflow', title: 'MODFLOW coupling', description: 'Dewatering CAPEX → NPV', method: 'POST', path: '/platform/hydro/modflow-coupling', body: { pit_depth_m: 90 } },
  { id: 'nema', title: 'NEMA compliance', description: 'Kenya EIA risk flags', method: 'POST', path: '/platform/compliance/nema', body: { activities: ['drilling', 'pit'] } },
  { id: 'federated', title: 'Federated consent', description: 'Cross-junior training consent registry', method: 'POST', path: '/platform/federated/consent', body: { org: 'junior_a', data_classes: ['geobotany_labels'] } },
  { id: 'checkout', title: 'Marketplace checkout', description: 'M-Pesa / Stripe scaffold', method: 'POST', path: '/platform/marketplace/checkout', body: { amount_usd: 149, provider: 'mpesa' } },
];

export function PlatformHubPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [results, setResults] = useState<Record<string, unknown>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<string | null>(null);

  async function runFeature(feature: Feature) {
    setLoading(feature.id);
    setErrors((prev) => ({ ...prev, [feature.id]: '' }));
    try {
      const body = {
        ...(feature.body ?? {}),
        project_id: selectedProject?.id ?? feature.body?.project_id ?? 'matuu',
      };
      const data =
        feature.method === 'GET'
          ? await apiGet<Record<string, unknown>>(feature.path)
          : await apiPost<Record<string, unknown>>(feature.path, body);
      setResults((prev) => ({ ...prev, [feature.id]: data }));
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        [feature.id]: err instanceof Error ? err.message : String(err),
      }));
    } finally {
      setLoading(null);
    }
  }

  return (
    <div>
      <PageHeader
        domain="core"
        title="Platform Expansion Hub"
        description="Fusion, geophysics, UAV/LiDAR, drone CV, GPR, IoT, compliance, lineage, and AI workflows."
      />

      {selectedProject ? (
        <p className="mb-6 font-mono text-sm text-sediment-muted">
          Active project: <span className="text-mineral-300">{selectedProject.name}</span>
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {FEATURES.map((feature) => (
          <section key={feature.id} className="tf-panel flex flex-col p-4">
            <h3 className="font-display text-base text-ore-300">{feature.title}</h3>
            <p className="mt-1 flex-1 text-sm text-sediment-muted">{feature.description}</p>
            <Button
              variant="secondary"
              className="mt-3 w-full text-xs"
              onClick={() => runFeature(feature)}
              disabled={loading === feature.id}
            >
              {loading === feature.id ? 'Running…' : 'Run pipeline'}
            </Button>
            {errors[feature.id] ? (
              <pre className="tf-error mt-3 max-h-24 text-[10px]">{errors[feature.id]}</pre>
            ) : null}
            {results[feature.id] ? (
              <div className="mt-3 max-h-48 overflow-auto">
                <CaptureResultView
                  display={inferDisplay(results[feature.id])}
                  fallback={results[feature.id]}
                />
              </div>
            ) : null}
          </section>
        ))}
      </div>
    </div>
  );
}