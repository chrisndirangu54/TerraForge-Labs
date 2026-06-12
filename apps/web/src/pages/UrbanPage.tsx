import { WorkflowPage } from '../components/WorkflowPage';
import { apiPost } from '../api/client';

export function UrbanPage() {
  return (
    <WorkflowPage
      title="Urban Planning"
      description="Settlement classification and land-use conflict checks."
      actionLabel="Classify settlement"
      onAction={() => apiPost('/urban/classify-settlement', { bbox: [37.45, -1.2, 37.55, -1.1] })}
    />
  );
}