import React from 'react';

// Catches errors thrown while rendering a page, so a bug shows a message and a
// reload button instead of a blank screen.
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('UI error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 32, maxWidth: 520 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Something went wrong</h1>
          <p style={{ color: 'var(--muted)', marginBottom: 16 }}>
            This page hit an unexpected error. Reloading usually fixes it.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '8px 16px', background: 'var(--surface2)', border: '1px solid var(--border)',
              borderRadius: 8, color: 'var(--text)', cursor: 'pointer', fontSize: 13,
            }}
          >
            Reload the page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}