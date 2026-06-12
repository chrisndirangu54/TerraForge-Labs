import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../../api/client';
import { Button } from '../ui/Button';
import { CaptureResultView, type CaptureDisplay } from './CaptureResultView';

type Transport = { id: string; label: string; description: string };
type Device = {
  device_id: string;
  name: string;
  instrument_type: string;
  transports: string[];
  battery_pct: number;
};

type TransportPanelProps = {
  projectId?: string;
  transport: string;
  onTransportChange: (transport: string) => void;
};

export function TransportPanel({ projectId, transport, onTransportChange }: TransportPanelProps) {
  const [transports, setTransports] = useState<Transport[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [connectedDevice, setConnectedDevice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ display?: CaptureDisplay } | null>(null);

  useEffect(() => {
    apiGet<{ transports: Transport[] }>('/capture/catalog')
      .then((catalog) => setTransports(catalog.transports))
      .catch(() => setTransports([]));
  }, []);

  async function scan() {
    setLoading(true);
    setError(null);
    try {
      const scanResult = await apiGet<{ devices: Device[] }>('/capture/devices/scan', {
        transport,
      });
      setDevices(scanResult.devices);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function connect(deviceId: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<Record<string, unknown>>(`/capture/devices/${deviceId}/connect`, {
        transport,
      });
      setSessionId(String(response.session_id));
      setConnectedDevice(deviceId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function sync() {
    if (!sessionId || !projectId) {
      setError('Connect a device and select a project first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<{ display?: CaptureDisplay }>(
        `/capture/devices/sessions/${sessionId}/sync`,
        { project_id: projectId, count: 6 },
      );
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {transports.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onTransportChange(item.id)}
            className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
              transport === item.id
                ? 'border-mineral-500/50 bg-mineral-600/15 text-mineral-300'
                : 'border-forge-600/50 text-sediment-muted hover:border-forge-500'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <p className="text-sm text-sediment-muted">
        {transports.find((t) => t.id === transport)?.description ??
          'Select a transport channel for wireless or serial capture.'}
      </p>

      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={scan} disabled={loading}>
          Scan devices
        </Button>
        {sessionId ? (
          <Button variant="primary" onClick={sync} disabled={loading || !projectId}>
            Sync readings
          </Button>
        ) : null}
      </div>

      {connectedDevice ? (
        <p className="font-mono text-xs text-moss-500">
          Connected: {connectedDevice} · session {sessionId?.slice(0, 8)}…
        </p>
      ) : null}

      {devices.length ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {devices.map((device) => (
            <div key={device.device_id} className="tf-panel p-4">
              <h4 className="font-display text-sm text-sediment">{device.name}</h4>
              <p className="mt-1 font-mono text-xs text-sediment-dim">
                {device.instrument_type} · {device.battery_pct}% batt
              </p>
              <Button
                variant="ghost"
                className="mt-3 text-xs"
                onClick={() => connect(device.device_id)}
                disabled={loading}
              >
                Connect via {transport}
              </Button>
            </div>
          ))}
        </div>
      ) : null}

      {error ? <pre className="tf-error">{error}</pre> : null}
      {result?.display ? <CaptureResultView display={result.display} /> : null}
    </div>
  );
}