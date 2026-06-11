import { FormEvent, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import { useProjectStore } from '../stores/projectStore';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{ id: string; title: string; source: string }>;
};

type CopilotResponse = {
  answer: string;
  citations: Array<{ id: string; title: string; source: string; excerpt?: string }>;
  provider: string;
  model: string;
};

export function CopilotPage() {
  const selectedProject = useProjectStore((s) => s.getSelectedProject());
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Geo Copilot is connected to TerraForge RAG + Gemini. Ask about JORC sampling, kriging uncertainty, geobotany indicators, or drill targeting.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [llmInfo, setLlmInfo] = useState<string>('');

  useEffect(() => {
    apiGet<{ provider: string; model: string; active: boolean; gemini_configured: boolean }>(
      '/copilot/status',
    )
      .then((status) => {
        const mode = status.active ? 'Gemini live' : 'stub fallback';
        setLlmInfo(`${status.provider} / ${status.model} (${mode})`);
      })
      .catch(() => setLlmInfo('LLM status unavailable'));
  }, []);

  async function askCopilot(event: FormEvent) {
    event.preventDefault();
    const question = input.trim();
    if (!question) return;

    setInput('');
    setLoading(true);
    setError(null);
    setMessages((prev) => [...prev, { role: 'user', content: question }]);

    try {
      const result = await apiPost<CopilotResponse>('/copilot/query', {
        query: question,
        project_id: selectedProject?.id,
        context: {
          project_name: selectedProject?.name,
          project_slug: selectedProject?.slug,
        },
      });

      let answer = result.answer;
      if (selectedProject) {
        answer += `\n\nProject context: ${selectedProject.name} (${selectedProject.slug})`;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: answer,
          citations: result.citations,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Sorry, copilot request failed: ${message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Geo Copilot</h2>
      <p>Grounded geoscience assistant with citation enforcement. {llmInfo ? `Backend: ${llmInfo}` : null}</p>

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
                textAlign: 'left',
              }}
            >
              {msg.content}
              {msg.citations?.length ? (
                <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#555' }}>
                  <strong>Citations:</strong>{' '}
                  {msg.citations.map((c) => `[${c.id}] ${c.title}`).join(' · ')}
                </div>
              ) : null}
            </span>
          </div>
        ))}
        {loading ? <p style={{ color: '#666' }}>Copilot thinking...</p> : null}
      </div>

      <form onSubmit={askCopilot} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about JORC, kriging, indicators, or targeting..."
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