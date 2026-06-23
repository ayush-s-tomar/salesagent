import React, { useState } from 'react';

const API = process.env.REACT_APP_API_URL || '';

const STEP_ICONS = { research: '🔍', score: '📊', email: '✍️', save: '💾', complete: '🎉' };

export default function AgentPage() {
  const [url, setUrl] = useState('');
  const [running, setRunning] = useState(false);
  const [trace, setTrace] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  async function runAgent() {
    if (!url.trim()) return;
    setRunning(true); setTrace([]); setResult(null); setError('');

    try {
      const resp = await fetch(`${API}/api/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedin_url: url }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(l => l.startsWith('data:'));
        for (const line of lines) {
          const data = line.replace('data: ', '').trim();
          if (data === '[DONE]') { setRunning(false); break; }
          try {
            const event = JSON.parse(data);
            if (event.step === 'complete') setResult(event.data);
            else setTrace(prev => [...prev.filter(t => t.step !== event.step), event]);
          } catch (_) {}
        }
      }
    } catch (e) {
      setError('Agent failed. Is the backend running?');
    } finally {
      setRunning(false);
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>AI Sales Agent</h1>
      <p style={{ color: 'var(--muted)', marginBottom: 28 }}>
        Paste a LinkedIn URL → Agent researches, scores, drafts an email &amp; adds to pipeline in 45 seconds
      </p>

      {/* Input */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 28 }}>
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !running && runAgent()}
          placeholder="https://linkedin.com/in/john-doe"
          style={{
            flex: 1, padding: '12px 16px', background: 'var(--surface)',
            border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)',
            fontSize: 14, outline: 'none',
          }}
        />
        <button
          onClick={runAgent}
          disabled={running || !url.trim()}
          style={{
            padding: '12px 24px', background: running ? 'var(--surface2)' : 'var(--accent)',
            border: 'none', borderRadius: 8, color: 'white', fontWeight: 600,
            cursor: running ? 'not-allowed' : 'pointer', fontSize: 14,
            opacity: !url.trim() ? 0.5 : 1,
          }}
        >
          {running ? '⏳ Running...' : '▶ Run Agent'}
        </button>
      </div>

      {error && (
        <div style={{ padding: 12, background: '#2d1a1a', border: '1px solid var(--red)', borderRadius: 8, color: '#fca5a5', marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Live trace */}
      {(trace.length > 0 || running) && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, marginBottom: 24 }}>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12, fontFamily: 'var(--mono)' }}>AGENT TRACE</div>
          {trace.map((t, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 16 }}>{STEP_ICONS[t.step] || '•'}</span>
              <span style={{ flex: 1, color: t.status === 'done' ? 'var(--text)' : 'var(--muted)' }}>{t.msg}</span>
              <span style={{
                fontSize: 10, padding: '2px 8px', borderRadius: 4,
                background: t.status === 'done' ? '#064e3b' : '#1e1b4b',
                color: t.status === 'done' ? 'var(--green)' : 'var(--accent2)',
              }}>
                {t.status === 'done' ? 'DONE' : 'RUNNING'}
              </span>
            </div>
          ))}
          {running && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 0', color: 'var(--muted)' }}>
              <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span>
              <span style={{ fontSize: 13 }}>Agent working...</span>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Lead card */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>LEAD PROFILE</div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{result.profile?.name || 'Lead'}</div>
            <div style={{ color: 'var(--muted)', marginBottom: 12 }}>{result.profile?.title} · {result.profile?.company}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                fontSize: 28, fontWeight: 700,
                color: result.score > 70 ? 'var(--green)' : result.score > 40 ? 'var(--yellow)' : 'var(--red)',
              }}>
                {result.score?.toFixed(0)}
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>/100<br />lead score</div>
            </div>
            {result.deal_id && (
              <div style={{ marginTop: 12, fontSize: 12, color: 'var(--green)' }}>
                ✅ Added to pipeline · Follow-up: {result.followup}
              </div>
            )}
          </div>

          {/* Email draft */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>GENERATED EMAIL</div>
            <pre style={{
              fontFamily: 'var(--font)', fontSize: 12, lineHeight: 1.7,
              color: 'var(--text)', whiteSpace: 'pre-wrap', maxHeight: 220, overflow: 'auto',
            }}>
              {result.email}
            </pre>
            <button
              onClick={() => navigator.clipboard.writeText(result.email || '')}
              style={{
                marginTop: 12, padding: '6px 14px', background: 'var(--surface2)',
                border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)',
                cursor: 'pointer', fontSize: 12,
              }}
            >
              📋 Copy Email
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
