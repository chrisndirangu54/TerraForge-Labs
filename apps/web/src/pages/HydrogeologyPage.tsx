import { WorkflowPage } from '../components/WorkflowPage';
import { apiPost } from '../api/client';

export function HydrogeologyPage() {
  return (
    <WorkflowPage
      title="Hydrogeology"
      description="Slug tests, pump tests, MODFLOW scaffold, and borehole siting."
      actionLabel="Run slug test"
      onAction={() => apiPost('/hydro/slug-test', { casing_radius_m: 0.05 })}
    />
  );
}