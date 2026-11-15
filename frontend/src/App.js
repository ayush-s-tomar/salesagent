import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import AgentPage from './pages/AgentPage';
import PipelinePage from './pages/PipelinePage';
import LeadsPage from './pages/LeadsPage';

export default function App() {
  const [page, setPage] = useState('agent');

  useEffect(() => {
    const names = { agent: 'Agent', pipeline: 'Pipeline', leads: 'Leads' };
    document.title = 'SalesAgent | ' + (names[page] || 'Agent');
  }, [page]);

  const pages = { agent: <AgentPage />, pipeline: <PipelinePage />, leads: <LeadsPage /> };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar current={page} onNav={setPage} />
      <main style={{ flex: 1, overflow: 'auto', background: 'var(--bg)' }}>
        <ErrorBoundary key={page}>{pages[page]}</ErrorBoundary>
      </main>
    </div>
  );
}
