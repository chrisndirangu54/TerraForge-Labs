import { WorkflowPage } from '../components/WorkflowPage';
import { apiGet, apiPost } from '../api/client';

export function SatellitePage() {
  return (
    <WorkflowPage
      title="Satellite Feeds"
      description="Scene browser, spectral indices, and InSAR change detection."
      actionLabel="List scenes + run InSAR"
      onAction={async () => {
        const scenes = await apiGet('/satellite/scenes');
        const insar = await apiPost('/satellite/insar', { bbox: '37.45,-1.2,37.55,-1.1' });
        return { scenes, insar };
      }}
    />
  );
}