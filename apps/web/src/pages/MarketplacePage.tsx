import { WorkflowPage } from '../components/WorkflowPage';
import { apiGet } from '../api/client';

export function MarketplacePage() {
  return (
    <WorkflowPage
      title="Marketplace"
      description="Model catalogue, plugins, and payment integration scaffold."
      actionLabel="Load catalogue"
      onAction={() => apiGet('/marketplace/catalogue')}
    />
  );
}