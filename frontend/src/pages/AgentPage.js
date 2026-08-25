import React, { useState, useEffect, useRef } from 'react';
import { Search, BarChart3, PenLine, Save, PartyPopper, Loader2, Play, Copy, CheckCircle2 } from 'lucide-react';

const API = process.env.REACT_APP_API_URL || '';

const STEP_ICONS = { research: Search, score: BarChart3, email: PenLine, save: Save, complete: PartyPopper };

export default function AgentPage() {
  const [url, setUrl] = useState('');
  const [running, setRunning] = useState(false);
  const [trace, setTrace] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const [backendWarm, setBackendWarm] = useState(false);
  const timerRef = useRef(null);

  // FIX: Render's free-tier backend spins down after inactivity and takes
  // 30-60s to cold-start on the first request. Previously the only way a
  // visitor found this out was by staring at a static spinner for up to a
  // minute with zero feedback - indistinguishable from the app being
  // broken. Firing a lightweight health check the moment the page loads
  // (before the user has even pasted a URL) wakes the backend early, so by
  // the time they click "Run Agent" the real request is much more likely
  // to hit an already-warm instance instead of paying the cold-start cost
  // inline with their actual task.
  useEffect(() => {
    fetch(`${API}/api/health`)
      .then(() => setBackendWarm(true))
      .catch(() => {});
  }, []);

  // FIX: elapsed-time counter so "Running..." shows a moving number
  // instead of a static label. A visitor watching "Running... 42s" can
  // tell the app is alive and working; a static spinner past ~10s reads as
  // frozen, and most people will bounce rather than wait out a silent
  // 60-second cold start.
  useEffect(() => {
    if (running) {
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => timerRef.current && clearInterval(timerRef.current);
  }, [running]);

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
        {/* FIX: was hardcoded "45 seconds" - real end-to-end runs (cold start
            included) were landing at 75-85s, so the claim didn't match what
            a visitor actually experienced. Framed as a range instead of a
            single number, with the cold-start caveat folded in up front
            rather than surfacing only after the visitor is already waiting. */}
        Paste a LinkedIn URL → Agent researches, scores, drafts an email &amp; adds to pipeline in ~45-90s (first run may take longer while the free-tier backend wakes up)
      </p>

      {/* Input */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
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
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '12px 24px', background: running ? 'var(--surface2)' : 'var(--accent)',
            border: 'none', borderRadius: 8, color: 'white', fontWeight: 600,
            cursor: running ? 'not-allowed' : 'pointer', fontSize: 14,
            opacity: !url.trim() ? 0.5 : 1,
            minWidth: 150, justifyContent: 'center',
          }}
        >
          {running ? (
            <>
              <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
              Running... {elapsed}s
            </>
          ) : (
            <>
              <Play size={15} fill="white" />
              Run Agent
            </>
          )}
        </button>
      </div>

      {/* Cold-start hint, only shown once the wait is long enough to matter */}
      {running && elapsed >= 8 && elapsed < 70 && (
        <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 20 }}>
          {backendWarm
            ? 'Working through research → scoring → drafting → saving...'
            : 'First request can take 30–60s while the free-tier backend wakes up. Hang tight.'}
        </div>
      )}
      {running && elapsed >= 70 && (
        <div style={{ fontSize: 12, color: 'var(--yellow)', marginBottom: 20 }}>
          This is taking longer than usual — the backend may still be waking up from a cold start, or a search step is running slow. Still working, no need to refresh.
        </div>
      )}
      {!running && trace.length === 0 && !error && (
        <div style={{ marginBottom: 20 }} />
      )}

      {error && (
        <div style={{ padding: 12, background: '#2d1a1a', border: '1px solid var(--red)', borderRadius: 8, color: '#fca5a5', marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Live trace */}
      {(trace.length > 0 || running) && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20, marginBottom: 24 }}>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12, fontFamily: 'var(--mono)' }}>AGENT TRACE</div>
          {trace.map((t, i) => {
            const Icon = STEP_ICONS[t.step];
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  width: 22, height: 22, flexShrink: 0,
                }}>
                  {Icon ? (
                    <Icon size={16} strokeWidth={1.9} color={t.status === 'done' ? 'var(--accent2)' : 'var(--muted)'} />
                  ) : (
                    <span style={{ color: 'var(--muted)' }}>•</span>
                  )}
                </span>
                <span style={{ flex: 1, color: t.status === 'done' ? 'var(--text)' : 'var(--muted)' }}>{t.msg}</span>
                <span style={{
                  fontSize: 10, padding: '2px 8px', borderRadius: 4,
                  background: t.status === 'done' ? '#064e3b' : '#1e1b4b',
                  color: t.status === 'done' ? 'var(--green)' : 'var(--accent2)',
                }}>
                  {t.status === 'done' ? 'DONE' : 'RUNNING'}
                </span>
              </div>
            );
          })}
          {running && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 0', color: 'var(--muted)' }}>
              <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
              <span style={{ fontSize: 13 }}>Agent working... {elapsed}s elapsed</span>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
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
            {/* FIX: score_reasons was already being sent by the backend
                (ml/scorer.py + agent/graph.py::node_score) but the UI never
                rendered it, so the score looked like a bare unexplained
                number. Shown as small tags under the score. */}
            {result.score_reasons && result.score_reasons.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
                {result.score_reasons.map((reason, i) => (
                  <span key={i} style={{
                    fontSize: 11, padding: '3px 8px', borderRadius: 999,
                    background: 'var(--surface2)', border: '1px solid var(--border)',
                    color: 'var(--muted)',
                  }}>
                    {reason}
                  </span>
                ))}
              </div>
            )}
            {result.deal_id && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 12, fontSize: 12, color: 'var(--green)' }}>
                <CheckCircle2 size={14} />
                Added to pipeline · Follow-up: {result.followup}
              </div>
            )}
          </div>

          {/* Email draft */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>GENERATED EMAIL</div>
            {/* FIX: maxHeight: 220 with overflow:auto was clipping the email
                mid-sentence in a short visible window (only ~6 lines
                visible before scroll), which looked broken/truncated in
                screenshots since nothing signaled there was more below the
                fold. Raised to 420 so a typical <150-word email (the hard
                cap enforced in node_email/_validate_email) fits without
                scrolling at all in the common case; overflow:auto is kept
                as a safety net for the rare longer draft rather than as
                the default viewing mode. */}
            <pre style={{
              fontFamily: 'var(--font)', fontSize: 12, lineHeight: 1.7,
              color: 'var(--text)', whiteSpace: 'pre-wrap', maxHeight: 420, overflow: 'auto',
            }}>
              {result.email}
            </pre>
            <button
              onClick={() => navigator.clipboard.writeText(result.email || '')}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                marginTop: 12, padding: '6px 14px', background: 'var(--surface2)',
                border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)',
                cursor: 'pointer', fontSize: 12,
              }}
            >
              <Copy size={13} />
              Copy Email
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
