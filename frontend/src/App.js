import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import AgentPage from './pages/AgentPage';
import PipelinePage from './pages/PipelinePage';
import LeadsPage from './pages/LeadsPage';

export default function App() {
  const [page, setPage] = useState('agent');

  const pages = { agent: <AgentPage />, pipeline: <PipelinePage />, leads: <LeadsPage /> };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar current={page} onNav={setPage} />
      <main style={{ flex: 1, overflow: 'auto', background: 'var(--bg)' }}>
        {pages[page]}
      </main>
    </div>
  );
}
