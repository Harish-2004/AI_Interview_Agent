import React, { useState } from 'react';
import { Zap, ArrowRight, User, Briefcase, FileText } from 'lucide-react';

export default function SetupPanel({ onStartSession, isLoading }) {
  const [candidateName, setCandidateName] = useState('Alex Chen');
  const [candidateEmail, setCandidateEmail] = useState('alex.chen@example.com');
  const [resumeText, setResumeText] = useState(
    'Senior Full-Stack Engineer with 5+ years experience building async APIs with FastAPI, Pydantic, and PostgreSQL. Experienced with Docker microservices and React dashboards.'
  );

  const [jobTitle, setJobTitle] = useState('Senior Backend Engineer');
  const [jobDescription, setJobDescription] = useState(
    'We are seeking a Senior Backend Engineer to architect scalable async microservices using Python, FastAPI, PostgreSQL, and Docker. Experience with system design and SQL optimization required.'
  );

  const handlePreFillMock = () => {
    setCandidateName('Alex Chen');
    setCandidateEmail('alex.chen@example.com');
    setResumeText(
      'Senior Full-Stack Engineer with 5+ years experience building async APIs with FastAPI, Pydantic, and PostgreSQL. Experienced with Docker microservices and React dashboards.'
    );
    setJobTitle('Senior Backend Engineer');
    setJobDescription(
      'We are seeking a Senior Backend Engineer to architect scalable async microservices using Python, FastAPI, PostgreSQL, and Docker. Experience with system design and SQL optimization required.'
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!candidateName || !resumeText || !jobTitle || !jobDescription) {
      alert('Please complete Candidate and Job details before starting.');
      return;
    }
    onStartSession({
      name: candidateName,
      email: candidateEmail,
      resume_text: resumeText,
      title: jobTitle,
      description: jobDescription
    });
  };

  return (
    <div className="glass-card" style={{ padding: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700' }}>📄 Candidate & Position Setup</h2>
          <p style={{ fontSize: '0.88rem', color: '#94a3b8' }}>
            Set up the target position and candidate resume to ground dual-context evaluation.
          </p>
        </div>

        <button type="button" className="btn btn-secondary" onClick={handlePreFillMock}>
          <Zap size={16} color="#06b6d4" />
          Pre-fill Demo Mock Data
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginBottom: '28px' }}>
          
          {/* Candidate Form Card */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', color: '#06b6d4', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <User size={18} /> Candidate Profile
            </h3>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Full Name</label>
              <input
                type="text"
                className="input-field"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                placeholder="e.g. Alex Chen"
                required
              />
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Email Address</label>
              <input
                type="email"
                className="input-field"
                value={candidateEmail}
                onChange={(e) => setCandidateEmail(e.target.value)}
                placeholder="alex@example.com"
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                Candidate Resume Text
              </label>
              <textarea
                className="input-field"
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste candidate background, tech stack, experience..."
                required
              />
            </div>
          </div>

          {/* Job Requirements Form Card */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', color: '#3b82f6', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Briefcase size={18} /> Target Position Requirements
            </h3>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Job Title</label>
              <input
                type="text"
                className="input-field"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Senior Backend Engineer"
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                Job Description (JD)
              </label>
              <textarea
                className="input-field"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                style={{ minHeight: '180px' }}
                placeholder="Paste position technical requirements and expectations..."
                required
              />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '12px 28px' }} disabled={isLoading}>
            {isLoading ? (
              <span>Initializing Multi-Agent Graph...</span>
            ) : (
              <>
                Start Voice Interview Session
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
