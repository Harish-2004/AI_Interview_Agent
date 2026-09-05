import React from 'react';
import { UserCheck, Mic, FileBarChart } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, hasSession, hasReport }) {
  return (
    <nav style={{ display: 'flex', gap: '12px', marginBottom: '24px', flexWrap: 'wrap' }}>
      <button
        className={`btn ${activeTab === 'setup' ? 'btn-primary' : 'btn-secondary'}`}
        onClick={() => setActiveTab('setup')}
      >
        <UserCheck size={18} />
        1. Setup Candidate & Job
      </button>

      <button
        className={`btn ${activeTab === 'interview' ? 'btn-primary' : 'btn-secondary'}`}
        onClick={() => setActiveTab('interview')}
        disabled={!hasSession}
      >
        <Mic size={18} />
        2. Live Voice Interview Room
      </button>

      <button
        className={`btn ${activeTab === 'report' ? 'btn-primary' : 'btn-secondary'}`}
        onClick={() => setActiveTab('report')}
        disabled={!hasReport}
      >
        <FileBarChart size={18} />
        3. Recruiter Scorecard Report
      </button>
    </nav>
  );
}
