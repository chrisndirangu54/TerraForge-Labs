import { WorkflowPage } from '../components/WorkflowPage';
import { apiPost } from '../api/client';

export function InfrastructurePage() {
  return (
    <WorkflowPage
      title="Infrastructure"
      description="Mining infrastructure assessment and pipeline routing."
      actionLabel="Assess mining infrastructure"
      onAction={() => apiPost('/infra/mining-assessment', { corridor_km: 12 })}
    />
  );
}