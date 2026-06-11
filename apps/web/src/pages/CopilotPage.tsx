import { FormEvent, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

export function CopilotPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Geo Copilot ready. Ask about vegetation anomalies, indicator species, or drill targeting for your project area.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function askCopilot(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;

    setInput('');
    setLoading(true);
    setError(null);
    setMessages((prev) => [...prev, { role: 'user', content: question }]);

    try {
      const lower = question.toLowerCase();
      let answer = '';

      if (lower.includes('indicator') || lower.includes('species') || lower.includes('plant')) {
        const indicators = await apiGet<{ records: Array<{ species: string; mineral_affinity: string }> }>(
          '/geobotany/indicator-species',
        );
        const top = indicators.records.slice(0, 5);
        answer = `Top indicator species near your AOI:\n${top
          .map((r) => `• ${r.species} (${r.mineral_affinity})`)
          .join('\n')}`;
      } else if (lower.includes('anomaly') || lower.includes('stress') || lower.includes('vegetation')) {
        const anomaly = await apiGet<Record<string, unknown>>('/geobotany/anomaly-map', {
          project_id: selectedProject?.id ?? '',
        });
        answer = `Composite anomaly score: ${String(anomaly.composite_score ?? anomaly.score ?? 'n/a')}. ${
          anomaly.interpretation ?? 'Vegetation stress and biogeochemistry suggest follow-up soil sampling.'
        }`;
      } else if (lower.includes('drill') || lower.includes('target')) {
        const plan = await apiPost<Record<string, unknown>>('/targeting/drill-plan-optimise', {
          targets: [
            { hole_id: 'DDH-01', depth_m: 180, target_probability: 0.82, uncertainty_reduction: 0.65, lon: 37.5, lat: -1.15 },
            { hole_id: 'DDH-02', depth_m: 220, target_probability: 0.74, uncertainty_reduction: 0.58, lon: 37.51, lat: -1.14 },
          ],
          budget_usd: 50000,
        });
        const holes = (plan.selected_holes as Array<Record<string, unknown>>) ?? [];
        answer = `Recommended drill plan under $50k budget:\n${holes
          .map((h) => `• ${String(h.hole_id)} — ${String(h.depth_m)} m (gain ${String(h.information_gain)})`)
          .join('\n') || 'No holes selected within budget.'}`;
      } else if (lower.includes('classify')) {
        const result = await apiPost<Record<string, unknown>>('/geobotany/classify-plant', {
          image_base64: '',
          lon: 37.5,
          lat: -1.15,
          project_id: selectedProject?.id,
        });
        answer = `Classifier: ${String(result.accepted_species ?? result.species ?? 'unknown')} (confidence ${String(result.confidence ?? 'n/a')}). ${String(result.recommended_action ?? '')}`;
      } else {
        answer =
          'I can help with indicator species, vegetation anomalies, drill targeting, and plant classification. Try: "Show indicator species" or "Optimise drill plan".';
      }

      if (selectedProject) {
        answer += `\n\nContext: ${selectedProject.name} (${selectedProject.slug})`;
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: answer }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Sorry, I could not reach the backend: ${message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Geo Copilot</h2>
      <p>Natural-language assistant wired to geobotany and targeting APIs.</p>

      <div
        style={{
          border: '1px solid #ddd',
          borderRadius: 6,
          padding: '1rem',
          minHeight: 320,
          maxHeight: 480,
          overflowY: 'auto',
          marginBottom: '1rem',
          background: '#fafafa',
        }}
      >
        {messages.map((msg, index) => (
          <div
            key={`${msg.role}-${index}`}
            style={{
              marginBottom: '0.75rem',
              textAlign: msg.role === 'user' ? 'right' : 'left',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                padding: '0.5rem 0.75rem',
                borderRadius: 8,
                background: msg.role === 'user' ? '#2d5a87' : '#fff',
                color: msg.role === 'user' ? '#fff' : '#222',
                border: msg.role === 'assistant' ? '1px solid #ddd' : 'none',
                whiteSpace: 'pre-wrap',
                maxWidth: '85%',
              }}
            >
              {msg.content}
            </span>
          </div>
        ))}
        {loading ? <p style={{ color: '#666' }}>Copilot thinking...</p> : null}
      </div>

      <form onSubmit={askCopilot} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about anomalies, species, or drill targets..."
          style={{ flex: 1 }}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          Send
        </button>
      </form>

      {error ? <pre style={{ color: 'crimson', marginTop: '0.75rem' }}>{error}</pre> : null}
    </div>
  );
}