import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_API_URL || '';
const STAGES = ['Lead', 'Contacted', 'Qualified', 'Proposal', 'Closed Won', 'Closed Lost'];

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenTone, setRegenTone] = useState('professional');
  const [regenLoading, setRegenLoading] = useState(false);
  const [regenMsg, setRegenMsg] = useState('');
  const [draftDirty, setDraftDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [query, setQuery] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [sortBy, setSortBy] = useState('newest');

  useEffect(() => { fetchLeads(); }, []);

  async function fetchLeads() {
    try {
      const r = await fetch(`${API}/api/leads/`);
      const d = await r.json(); setLeads(Array.isArray(d) ? d : []);
    } catch (_) { setLeads([]); }
    finally { setLoading(false); }
  }

  async function fetchDetail(id) {
    setDraftDirty(false);
    setRegenMsg('');
    try {
      const r = await fetch(`${API}/api/leads/${id}`);
      if (!r.ok) return;
      setSelected(await r.json());
    } catch (_) {}
  }

  async function regenerate() {
    if (!selected || !selected.email_draft) return;
    setRegenLoading(true); setRegenMsg('');
    try {
      const r = await fetch(`${API}/api/emails/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead_name: selected.name || '',
          company: selected.company || '',
          title: selected.title || '',
          context: selected.email_draft,
          tone: regenTone,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) { setRegenMsg(data.detail || `Request failed (${r.status}).`); return; }
      setSelected(prev => ({ ...prev, email_draft: data.email }));
      setDraftDirty(!data.note);
      setRegenMsg(data.note || 'Rewritten. Click Save this version to keep it.');
    } catch (_) {
      setRegenMsg('Could not reach the server.');
    } finally {
      setRegenLoading(false);
    }
  }

  async function saveDraft() {
    if (!selected || !draftDirty) return;
    setSaving(true); setRegenMsg('');
    try {
      const r = await fetch(`${API}/api/leads/${selected.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_draft: selected.email_draft }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) { setRegenMsg(data.detail || `Request failed (${r.status}).`); return; }
      setDraftDirty(false);
      setRegenMsg('Saved.');
      setLeads(prev => prev.map(l => (l.id === selected.id ? { ...l, email_draft: selected.email_draft } : l)));
    } catch (_) {
      setRegenMsg('Could not reach the server.');
    } finally {
      setSaving(false);
    }
  }

  async function exportCsv() {
    try {
      const r = await fetch(`${API}/api/leads/export.csv`);
      if (!r.ok) return;
      const blob = await r.blob();
      const href = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = href;
      a.download = 'leads.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(href);
    } catch (_) {}
  }

  const q = query.trim().toLowerCase();
  let visible = leads
    .filter(l => !stageFilter || l.stage === stageFilter)
    .filter(l => !q || [l.name, l.company, l.title].some(v => String(v || '').toLowerCase().includes(q)));
  if (sortBy === 'score') visible = [...visible].sort((a, b) => (b.score || 0) - (a.score || 0));

  if (loading) return <div style={{ padding: 32, color: 'var(--muted)' }}>Loading leads...</div>;

  return (
    <div style={{ padding: 32 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>Leads</h1>
      <p style={{ color: 'var(--muted)', marginBottom: 16 }}>
        {visible.length === leads.length
          ? `${leads.length} ${leads.length === 1 ? 'lead' : 'leads'} in database`
          : `Showing ${visible.length} of ${leads.length} leads`}
      </p>

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search name, company or title"
          style={{ flex: 1, minWidth: 200, padding: '8px 12px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', fontSize: 13, outline: 'none' }}
        />
        <select
          value={stageFilter}
          onChange={e => setStageFilter(e.target.value)}
          style={{ fontSize: 12, padding: '8px 10px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)' }}
        >
          <option value="">All stages</option>
          {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          style={{ fontSize: 12, padding: '8px 10px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)' }}
        >
          <option value="newest">Newest first</option>
          <option value="score">Highest score</option>
        </select>
        <button
          onClick={exportCsv}
          style={{ fontSize: 12, padding: '8px 14px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text)', cursor: 'pointer' }}
        >
          Export CSV
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1fr' : '1fr', gap: 20 }}>
        {/* Leads table */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface2)' }}>
                {['Name', 'Company', 'Title', 'Score', 'Stage'].map(h => (
                  <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 11, color: 'var(--muted)', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 && (
                <tr><td colSpan={5} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>{leads.length === 0 ? 'No leads yet. Run the agent to add some.' : 'No leads match your filters.'}</td></tr>
              )}
              {visible.map(lead => (
                <tr
                  key={lead.id}
                  onClick={() => fetchDetail(lead.id)}
                  style={{
                    borderBottom: '1px solid var(--border)', cursor: 'pointer',
                    background: selected?.id === lead.id ? 'var(--surface2)' : 'transparent',
                    transition: 'background 0.1s',
                  }}
                >
                  <td style={{ padding: '10px 14px', fontWeight: 600 }}>{lead.name}</td>
                  <td style={{ padding: '10px 14px', color: 'var(--muted)' }}>{lead.company || '-'}</td>
                  <td style={{ padding: '10px 14px', color: 'var(--muted)', fontSize: 12 }}>{lead.title || '-'}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      fontWeight: 700,
                      color: lead.score > 70 ? 'var(--green)' : lead.score > 40 ? 'var(--yellow)' : 'var(--red)',
                    }}>
                      {lead.score?.toFixed(0)}
                    </span>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ fontSize: 11, padding: '2px 8px', background: 'var(--surface2)', borderRadius: 4, color: 'var(--muted)' }}>
                      {lead.stage}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Lead detail */}
        {selected && (
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>{selected.name}</div>
                <div style={{ color: 'var(--muted)', fontSize: 13 }}>{[selected.title, selected.company].filter(Boolean).join(' · ')}</div>
              </div>
              <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', fontSize: 18 }}>×</button>
            </div>

            {selected.linkedin_url && (
              <a href={selected.linkedin_url} target="_blank" rel="noopener noreferrer"
                style={{ fontSize: 12, color: 'var(--accent2)', textDecoration: 'none', display: 'block', marginBottom: 16 }}>
                🔗 LinkedIn Profile
              </a>
            )}

            {selected.email_draft && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8 }}>GENERATED EMAIL</div>
                <pre style={{
                  fontFamily: 'var(--font)', fontSize: 12, lineHeight: 1.7, color: 'var(--text)',
                  whiteSpace: 'pre-wrap', background: 'var(--surface2)', padding: 12, borderRadius: 8,
                  maxHeight: 320, overflow: 'auto',
                }}>
                  {selected.email_draft}
                </pre>
                <div style={{ display: 'flex', gap: 8, marginTop: 10, alignItems: 'center' }}>
                  <select
                    value={regenTone}
                    onChange={e => setRegenTone(e.target.value)}
                    style={{ fontSize: 12, padding: '5px 8px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)' }}
                  >
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="concise">Concise</option>
                    <option value="direct">Direct</option>
                  </select>
                  <button
                    onClick={regenerate}
                    disabled={regenLoading}
                    style={{ fontSize: 12, padding: '5px 12px', background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', cursor: regenLoading ? 'not-allowed' : 'pointer' }}
                  >
                    {regenLoading ? 'Rewriting...' : 'Rewrite in this tone'}
                  </button>
                  <button
                    onClick={saveDraft}
                    disabled={!draftDirty || saving}
                    style={{ fontSize: 12, padding: '5px 12px', background: draftDirty ? 'var(--accent)' : 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6, color: draftDirty ? 'white' : 'var(--muted)', cursor: !draftDirty || saving ? 'not-allowed' : 'pointer' }}
                  >
                    {saving ? 'Saving...' : 'Save this version'}
                  </button>
                </div>
                {regenMsg && <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>{regenMsg}</div>}
              </div>
            )}

            {selected.interactions?.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8 }}>ACTIVITY LOG</div>
                {selected.interactions.map((i, idx) => (
                  <div key={idx} style={{ fontSize: 12, color: 'var(--muted)', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                    {i.type === 'agent_research' ? 'Agent run' : String(i.type || '').replace(/_/g, ' ')} · {new Date(i.created_at).toLocaleDateString()}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
