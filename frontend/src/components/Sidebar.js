import React from 'react';

const items = [
  { key: 'agent', icon: '🤖', label: 'Agent' },
  { key: 'pipeline', icon: '📋', label: 'Pipeline' },
  { key: 'leads', icon: '👥', label: 'Leads' },
];

export default function Sidebar({ current, onNav }) {
  return (
    <aside style={{
      width: 220, background: 'var(--surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', padding: '24px 0', flexShrink: 0,
    }}>
      <div style={{ padding: '0 20px 28px' }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent2)' }}>SalesAgent</div>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>AI-Powered CRM</div>
      </div>
      {items.map(item => (
        <button key={item.key} onClick={() => onNav(item.key)} style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '10px 20px', border: 'none', cursor: 'pointer',
          background: current === item.key ? 'var(--surface2)' : 'transparent',
          color: current === item.key ? 'var(--accent2)' : 'var(--muted)',
          borderLeft: current === item.key ? '2px solid var(--accent)' : '2px solid transparent',
          fontWeight: current === item.key ? 600 : 400,
          fontSize: 14, textAlign: 'left', transition: 'all 0.15s',
        }}>
          <span>{item.icon}</span>
          <span>{item.label}</span>
        </button>
      ))}
      <div style={{ marginTop: 'auto', padding: '0 20px', fontSize: 11, color: 'var(--muted)' }}>
        v1.0.0 · Portfolio Project
      </div>
    </aside>
  );
}
