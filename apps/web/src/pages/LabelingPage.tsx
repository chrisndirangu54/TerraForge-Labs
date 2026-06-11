import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type QueueItem = {
  id: string;
  species: string;
  lon: number;
  lat: number;
  model_confidence: number;
  status: 'pending' | 'confirmed' | 'rejected';
};

type ActiveLearningStatus = {
  new_confirmed_labels: number;
  trigger_retrain: boolean;
  next_model_version: string | null;
};

const SEED_QUEUE: QueueItem[] = [
  { id: 'lbl-001', species: 'ocimum_centraliafricanum', lon: 37.48, lat: -1.14, model_confidence: 0.62, status: 'pending' },
  { id: 'lbl-002', species: 'haumaniastrum_robertii', lon: 37.51, lat: -1.16, model_confidence: 0.71, status: 'pending' },
  { id: 'lbl-003', species: 'unknown_vegetation', lon: 37.49, lat: -1.12, model_confidence: 0.44, status: 'pending' },
];

export function LabelingPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [queue, setQueue] = useState<QueueItem[]>(SEED_QUEUE);
  const [activeLearning, setActiveLearning] = useState<ActiveLearningStatus | null>(null);
  const [species, setSpecies] = useState('ocimum_centraliafricanum');
  const [lon, setLon] = useState('37.50');
  const [lat, setLat] = useState('-1.15');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitLabel(item: QueueItem, confirmed: boolean) {
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<{
        observation: Record<string, unknown>;
        active_learning: ActiveLearningStatus;
      }>('/geobotany/log-observation', {
        species: item.species,
        lon: item.lon,
        lat: item.lat,
        label_confidence: confirmed ? 'geologist_confirmed' : 'rejected',
        project_id: selectedProject?.id,
      });
      setActiveLearning(response.active_learning);
      setQueue((prev) =>
        prev.map((entry) =>
          entry.id === item.id
            ? { ...entry, status: confirmed ? 'confirmed' : 'rejected' }
            : entry,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function addObservation(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<{
        observation: Record<string, unknown>;
        active_learning: ActiveLearningStatus;
      }>('/geobotany/log-observation', {
        species,
        lon: Number(lon),
        lat: Number(lat),
        label_confidence: 'geologist_confirmed',
        project_id: selectedProject?.id,
      });
      setActiveLearning(response.active_learning);
      setQueue((prev) => [
        ...prev,
        {
          id: `lbl-${prev.length + 1}`,
          species,
          lon: Number(lon),
          lat: Number(lat),
          model_confidence: 1,
          status: 'confirmed',
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function refreshIndicators() {
    setError(null);
    try {
      await apiGet('/geobotany/indicator-species');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const pending = queue.filter((item) => item.status === 'pending');

  return (
    <div>
      <h2>Active Learning Queue</h2>
      <p>Review low-confidence geobotany classifications and feed confirmed labels back to training.</p>

      <div style={{ marginBottom: '1rem' }}>
        <button type="button" onClick={refreshIndicators}>
          Refresh indicator species
        </button>
      </div>

      {activeLearning ? (
        <div
          style={{
            padding: '0.75rem',
            marginBottom: '1rem',
            border: '1px solid #ddd',
            borderRadius: 6,
            background: activeLearning.trigger_retrain ? '#f0fff4' : '#fafafa',
          }}
        >
          <strong>Retrain status:</strong> {activeLearning.new_confirmed_labels} confirmed labels
          {activeLearning.trigger_retrain
            ? ` — retrain triggered (${activeLearning.next_model_version})`
            : ' — awaiting more labels'}
        </div>
      ) : null}

      <section style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem' }}>Pending queue ({pending.length})</h3>
        {pending.length === 0 ? (
          <p>Queue clear. Add a confirmed observation below.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Species</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Location</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Confidence</th>
                <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '0.5rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((item) => (
                <tr key={item.id}>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{item.species}</td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    {item.lon.toFixed(3)}, {item.lat.toFixed(3)}
                  </td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    {(item.model_confidence * 100).toFixed(0)}%
                  </td>
                  <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                    <button type="button" disabled={loading} onClick={() => submitLabel(item, true)}>
                      Confirm
                    </button>{' '}
                    <button type="button" disabled={loading} onClick={() => submitLabel(item, false)}>
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <form
        onSubmit={addObservation}
        style={{
          display: 'grid',
          gap: '0.75rem',
          maxWidth: 420,
          padding: '1rem',
          border: '1px solid #ddd',
          borderRadius: 6,
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1rem' }}>Add confirmed observation</h3>
        <label>
          Species
          <input value={species} onChange={(e) => setSpecies(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Longitude
          <input value={lon} onChange={(e) => setLon(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Latitude
          <input value={lat} onChange={(e) => setLat(e.target.value)} style={{ width: '100%' }} />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Submitting...' : 'Log observation'}
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
    </div>
  );
}