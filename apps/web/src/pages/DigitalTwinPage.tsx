import { WorkflowPage } from '../components/WorkflowPage';
import { apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

export function DigitalTwinPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  return (
    <WorkflowPage
      title="Digital Twin"
      description="4D deposit viewer with time slider and alert rules."
      actionLabel="Build twin snapshot"
      onAction={() =>
        apiPost('/gap-closure/digital-twin', {
          project_id: selectedProject?.id,
          time_steps: 4,
        })
      }
    />
  );
}