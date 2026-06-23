import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_API_URL || '';
const STAGES = ['Lead', 'Contacted', 'Qualified', 'Proposal', 'Closed Won', 'Closed Lost'];

const STAGE_COLORS = {
  'Lead': '#6366f1', 'Contacted': '#8b5cf6', 'Qualified': '#f59e0b',
  'Proposal': '#3b82f6', 'Closed Won': '#10b981', 'Closed Lost': '#ef4444',
};

export default function PipelinePage() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchDeals(); }, []);

  async function fetchDeals() {
    try {
      const r = await fetch(`${API}/api/deals/`);
      setDeals(await r.json());
    } catch (_) { setDeals([]); }
    finally { setLoading(false); }
  }

  async function moveStage(dealId, stage) {
    await fetch(`${API}/api/deals/${dealId}/stage`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage }),
    });
    fetchDeals();
  }

  if (loading) return <div style={{ padding: 32, color: 'var(--muted)' }}>Loading pipeline...</div>;

  return (
    <div style={{ padding: 32 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>Sales Pipeline</h1>
      <p style={{ color: 'var(--muted)', marginBottom: 28 }}>{deals.length} deals tracked</p>

      <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 16 }}>
        {STAGES.map(stage => {
          const stageDeals = deals.filter(d => d.stage === stage);
          return (
            <div key={stage} style={{
              minWidth: 220, background: 'var(--surface)',
              border: '1px solid var(--border)', borderRadius: 12, padding: 16, flexShrink: 0,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{stage}</div>
                <div style={{
                  background: STAGE_COLORS[stage] + '22', color: STAGE_COLORS[stage],
                  fontSize: 11, padding: '2px 8px', borderRadius: 10, fontWeight: 600,
                }}>
                  {stageDeals.length}
                </div>
              </div>
              {stageDeals.length === 0 && (
                <div style={{ color: 'var(--muted)', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>
                  No deals
                </div>
              )}
              {stageDeals.map(deal => (
                <div key={deal.id} style={{
                  background: 'var(--surface2)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: 12, marginBottom: 8,
                }}>
                  <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{deal.lead_name || deal.title}</div>
                  <div style={{ color: 'var(--muted)', fontSize: 11, marginBottom: 8 }}>{deal.company}</div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{
                      fontSize: 12, fontWeight: 700,
                      color: deal.score > 70 ? 'var(--green)' : deal.score > 40 ? 'var(--yellow)' : 'var(--red)',
                    }}>
                      {deal.score?.toFixed(0)}/100
                    </div>
                    <select
                      value={deal.stage}
                      onChange={e => moveStage(deal.id, e.target.value)}
                      style={{
                        fontSize: 10, padding: '2px 6px', background: 'var(--surface)',
                        border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text)', cursor: 'pointer',
                      }}
                    >
                      {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
