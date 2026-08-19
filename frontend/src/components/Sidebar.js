import React from 'react';
import { Bot, ClipboardList, Users } from 'lucide-react';

const items = [
  { key: 'agent', icon: Bot, label: 'Agent' },
  { key: 'pipeline', icon: ClipboardList, label: 'Pipeline' },
  { key: 'leads', icon: Users, label: 'Leads' },
];

export default function Sidebar({ current, onNav }) {
  return (
    <aside style={{
      width: 232, background: 'var(--surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', padding: '28px 0', flexShrink: 0,
    }}>
      <div style={{ padding: '0 24px 32px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: 'var(--accent)',
          boxShadow: '0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent)',
        }} />
        <div>
          <div style={{ fontSize: 17, fontWeight: 700, color: 'var(--accent2)', letterSpacing: '-0.01em', lineHeight: 1.1 }}>
            SalesAgent
          </div>
          <div style={{ fontSize: 10.5, color: 'var(--muted)', marginTop: 3, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            AI-Powered CRM
          </div>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '0 12px' }}>
        {items.map(item => {
          const Icon = item.icon;
          const active = current === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onNav(item.key)}
              style={{
                position: 'relative',
                display: 'flex', alignItems: 'center', gap: 11,
                padding: '9px 12px', border: 'none', cursor: 'pointer',
                borderRadius: 8,
                background: active ? 'color-mix(in srgb, var(--accent) 12%, transparent)' : 'transparent',
                color: active ? 'var(--accent2)' : 'var(--muted)',
                fontWeight: active ? 600 : 500,
                fontSize: 13.5, textAlign: 'left',
                transition: 'background 0.15s ease, color 0.15s ease',
                width: '100%',
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  e.currentTarget.style.background = 'color-mix(in srgb, var(--muted) 8%, transparent)';
                  e.currentTarget.style.color = 'var(--accent2)';
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--muted)';
                }
              }}
            >
              {active && (
                <span style={{
                  position: 'absolute', left: -12, top: '50%', transform: 'translateY(-50%)',
                  width: 3, height: 16, borderRadius: 2,
                  background: 'var(--accent)',
                }} />
              )}
              <span style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: 26, height: 26, borderRadius: 6, flexShrink: 0,
                background: active ? 'color-mix(in srgb, var(--accent) 18%, transparent)' : 'transparent',
                transition: 'background 0.15s ease',
              }}>
                <Icon size={16} strokeWidth={active ? 2.25 : 1.75} style={{ display: 'block' }} />
              </span>
              <span style={{ lineHeight: 1 }}>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div style={{
        marginTop: 'auto', padding: '16px 24px 0',
        borderTop: '1px solid var(--border)', marginLeft: 24, marginRight: 24, paddingTop: 16,
      }}>
        <div style={{ fontSize: 10.5, color: 'var(--muted)', letterSpacing: '0.02em' }}>
          v1.0.0 · Portfolio Project
        </div>
      </div>
    </aside>
  );
}
