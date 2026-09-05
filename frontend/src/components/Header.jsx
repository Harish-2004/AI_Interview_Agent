import React from 'react';
import { Bot, Zap, Activity, ExternalLink } from 'lucide-react';

export default function Header({ isConnected }) {
  return (
    <header className="glass-card" style={{ padding: '16px 24px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 15px rgba(6, 182, 212, 0.4)'
        }}>
          <Bot size={26} color="#ffffff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: '700', background: 'linear-gradient(135deg, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AI Technical Interview Agent
          </h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
            Multi-Agent LangGraph System with Dual-Context JD & Resume Grounding
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Backend Connectivity Status */}
        <div className={`badge ${isConnected ? 'badge-emerald' : 'badge-rose'}`}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#10b981' : '#f43f5e',
            display: 'inline-block'
          }}></span>
          {isConnected ? 'Backend Ready (:8000)' : 'Backend Offline'}
        </div>

        {/* Arize Phoenix Tracing Link */}
        <a 
          href="http://localhost:6006" 
          target="_blank" 
          rel="noreferrer"
          className="badge badge-purple"
          style={{ textDecoration: 'none', cursor: 'pointer' }}
          title="Open Arize Phoenix Observability UI"
        >
          <Activity size={14} />
          Arize Phoenix (:6006)
          <ExternalLink size={12} />
        </a>
      </div>
    </header>
  );
}
