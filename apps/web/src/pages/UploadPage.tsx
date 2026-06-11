import { useState } from 'react';
import { uploadInstrument } from '../api/client';

const sampleXml = `<?xml version="1.0"?>
<survey>
  <measurement>
    <profile_id>P-01</profile_id>
    <electrode_spacing_m>10</electrode_spacing_m>
    <apparent_resistivity_ohm_m>120</apparent_resistivity_ohm_m>
    <ip_chargeability_ms>2.5</ip_chargeability_ms>
    <sp_mv>10</sp_mv>
    <lon>37.5</lon>
    <lat>-1.15</lat>
  </measurement>
</survey>`;

export function UploadPage() {
  const [instrumentType, setInstrumentType] = useState('terrameter');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  async function uploadSample() {
    setLoading(true);
    setError(null);
    try {
      const blob = new Blob([sampleXml], { type: 'application/xml' });
      const data = await uploadInstrument(instrumentType, blob, 'sample_terrameter.xml');
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Data Upload</h2>
      <label>
        Instrument type{' '}
        <select value={instrumentType} onChange={(e) => setInstrumentType(e.target.value)}>
          <option value="terrameter">Terrameter</option>
          <option value="xrf_bruker">XRF Bruker</option>
          <option value="kappameter">Kappameter</option>
          <option value="gnss_trimble">GNSS Trimble</option>
        </select>
      </label>
      <div style={{ marginTop: '1rem' }}>
        <button type="button" onClick={uploadSample} disabled={loading}>
          {loading ? 'Uploading...' : 'Upload Sample File'}
        </button>
      </div>
      {error ? <pre style={{ color: 'crimson' }}>{error}</pre> : null}
      {result ? <pre>{JSON.stringify(result, null, 2)}</pre> : null}
    </div>
  );
}