import { ApiPanel } from '../components/ApiPanel';
import { PageHeader } from '../components/ui/PageHeader';
import { apiGet, apiPost } from '../api/client';

type DomainPageProps = {
  title: string;
};

export function DomainPage({ title }: DomainPageProps) {
  return (
    <div>
      <PageHeader title={title} description={`${title} workspace — API-backed exploration tools.`} />

      {title === 'Main Map' ? (
        <ApiPanel
          title="Mapping layers"
          description="Load layer catalogue and a sample tile from the backend."
          actionLabel="Load map data"
          onAction={async () => {
            const layers = await apiGet('/mapping/layers');
            const tile = await apiGet('/tiles/10/500/400');
            return { layers, tile };
          }}
        />
      ) : null}
      {title === 'Kriging Studio' ? (
        <ApiPanel
          title="Kriging"
          description="POST /fuse-geodata"
          actionLabel="Run kriging"
          onAction={() => apiPost('/fuse-geodata', { element: 'ta_ppm' })}
        />
      ) : null}
      {title === 'Reports' ? (
        <ApiPanel
          title="JORC report"
          description="POST /reports/jorc then poll the job."
          actionLabel="Generate JORC report"
          onAction={async () => {
            const started = await apiPost<{ job_id: string }>('/reports/jorc', {
              project_name: 'TerraForge Demo',
              commodity: 'Ta',
            });
            return apiGet(`/jobs/${started.job_id}`);
          }}
        />
      ) : null}
      {title === 'Marketplace' ? (
        <ApiPanel
          title="Catalogue"
          description="GET /marketplace/catalogue"
          actionLabel="Load catalogue"
          onAction={() => apiGet('/marketplace/catalogue')}
        />
      ) : null}
      {title === 'Hydrogeology' ? (
        <ApiPanel
          title="Hydrogeology"
          description="Groundwater table and boreholes."
          actionLabel="Load hydro data"
          onAction={async () => ({
            groundwater: await apiGet('/hydro/groundwater-table'),
            boreholes: await apiGet('/hydro/boreholes'),
          })}
        />
      ) : null}
      {title === 'Urban Planning' ? (
        <ApiPanel
          title="Urban"
          description="GET /urban/settlements"
          actionLabel="Load settlements"
          onAction={() => apiGet('/urban/settlements')}
        />
      ) : null}
      {title === 'Infrastructure' ? (
        <ApiPanel
          title="Infrastructure"
          description="GET /infra/roads"
          actionLabel="Load roads"
          onAction={() => apiGet('/infra/roads')}
        />
      ) : null}
      {title === 'Satellite Feeds' ? (
        <ApiPanel
          title="Satellite"
          description="GET /satellite/scenes"
          actionLabel="Load scenes"
          onAction={() =>
            apiGet('/satellite/scenes', {
              bbox: '37.45,-1.20,37.55,-1.10',
              start: '2026-01-01',
              end: '2026-06-30',
            })
          }
        />
      ) : null}
      {![
        'Main Map',
        'Kriging Studio',
        'Reports',
        'Marketplace',
        'Hydrogeology',
        'Urban Planning',
        'Infrastructure',
        'Satellite Feeds',
      ].includes(title) ? (
        <p className="rounded-lg border border-forge-600/50 bg-forge-850/50 p-4 text-sm text-sediment-muted">
          Page scaffold connected to the shared API client. Extend this view for{' '}
          <span className="text-ore-300">{title}</span>.
        </p>
      ) : null}
    </div>
  );
}