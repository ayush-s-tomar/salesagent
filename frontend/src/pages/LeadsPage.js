import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_API_URL || '';

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchLeads(); }, []);

  async function fetchLeads() {
    try {
      const r = await fetch(`${API}/api/leads/`);
      setLeads(await r.json());
    } catch (_) { setLeads([]); }
    finally { setLoading(false); }
  }

  async function fetchDetail(id) {
    const r = await fetch(`${API}/api/leads/${id}`);
    setSelected(await r.json());
  }

  if (loading) return <div style={{ padding: 32, color: 'var(--muted)' }}>Loading leads...</div>;

  return (
    <div style={{ padding: 32 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>Leads</h1>
      <p style={{ color: 'var(--muted)', marginBottom: 24 }}>{leads.length} leads in database</p>

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
              {leads.length === 0 && (
                <tr><td colSpan={5} style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>No leads yet. Run the agent to add some.</td></tr>
              )}
              {leads.map(lead => (
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
                  <td style={{ padding: '10px 14px', color: 'var(--muted)' }}>{lead.company}</td>
                  <td style={{ padding: '10px 14px', color: 'var(--muted)', fontSize: 12 }}>{lead.title}</td>
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
                <div style={{ color: 'var(--muted)', fontSize: 13 }}>{selected.title} · {selected.company}</div>
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
                  maxHeight: 200, overflow: 'auto',
                }}>
                  {selected.email_draft}
                </pre>
              </div>
            )}

            {selected.interactions?.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8 }}>ACTIVITY LOG</div>
                {selected.interactions.map((i, idx) => (
                  <div key={idx} style={{ fontSize: 12, color: 'var(--muted)', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                    {i.type} · {new Date(i.created_at).toLocaleDateString()}
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
