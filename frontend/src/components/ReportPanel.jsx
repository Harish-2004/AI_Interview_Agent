import React from 'react';
import { Award, CheckCircle, AlertTriangle, Printer, User, Briefcase, FileText } from 'lucide-react';

export default function ReportPanel({ candidate, job, report }) {
  const overallScore = report?.overallScore || report?.score || 8.5;
  const recommendation = report?.recommendation || 'Proceed to Next Round';
  const strengths = report?.strengths || ['Async REST APIs with FastAPI', 'System Microservice Architecture', 'Pydantic Data Validation'];
  const weaknesses = report?.weaknesses || ['Advanced SQL Index Tuning', 'Distributed Cache Eviction Strategies'];
  const summary = report?.summary || `${candidate?.name || 'Alex Chen'} demonstrated strong core technical competence in FastAPI async architecture, Docker containerization, and backend microservices design. Recommended for technical round 2.`;

  return (
    <div className="glass-card" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: '700' }}>📊 Technical Candidate Scorecard</h2>
          <p style={{ fontSize: '0.88rem', color: '#94a3b8' }}>
            Multi-Agent Evaluator & Report Synthesis (Dual-Context Grounded)
          </p>
        </div>

        <button className="btn btn-secondary" onClick={() => window.print()}>
          <Printer size={16} />
          Print / Export PDF Report
        </button>
      </div>

      {/* Candidate Profile Summary Header */}
      <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '16px 20px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)', marginBottom: '24px', display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        <div>
          <span style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase' }}>Candidate</span>
          <p style={{ fontWeight: '600', color: '#06b6d4' }}>{candidate?.name || 'Alex Chen'}</p>
        </div>
        <div>
          <span style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase' }}>Target Position</span>
          <p style={{ fontWeight: '600', color: '#3b82f6' }}>{job?.title || 'Senior Backend Engineer'}</p>
        </div>
        <div>
          <span style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase' }}>Evaluation Mode</span>
          <p style={{ fontWeight: '600', color: '#10b981' }}>Dual-Context (JD + Resume)</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '28px' }}>
        
        {/* Score & Recommendation Card */}
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '24px', borderRadius: '14px', border: '1px solid rgba(6, 182, 212, 0.3)', textAlign: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px' }}>
            Overall Score
          </span>
          <div style={{ fontSize: '3.6rem', fontWeight: '800', background: 'linear-gradient(135deg, #06b6d4, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: '8px 0' }}>
            {overallScore} <span style={{ fontSize: '1.5rem', color: '#94a3b8' }}>/ 10</span>
          </div>
          
          <div className="badge badge-emerald" style={{ padding: '8px 16px', fontSize: '0.9rem', width: '100%', justifyContent: 'center' }}>
            <Award size={18} />
            {recommendation.toUpperCase()}
          </div>
        </div>

        {/* Strengths & Weaknesses */}
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '24px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '600', color: '#10b981', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={18} /> Verified Technical Strengths
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
            {strengths.map((str, i) => (
              <span key={i} className="badge badge-emerald">
                ✓ {str}
              </span>
            ))}
          </div>

          <h3 style={{ fontSize: '1rem', fontWeight: '600', color: '#f43f5e', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} /> Areas for Improvement
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {weaknesses.map((wk, i) => (
              <span key={i} className="badge badge-rose">
                ⚠ {wk}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Recruiter Detailed Summary */}
      <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '24px', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '600', color: '#f8fafc', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileText size={18} color="#06b6d4" /> Recruiter Executive Summary
        </h3>
        <p style={{ fontSize: '0.95rem', color: '#cbd5e1', lineHeight: '1.7' }}>
          {summary}
        </p>
      </div>

    </div>
  );
}
