import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Send, Bot, User, CheckCircle, Clock } from 'lucide-react';

export default function InterviewRoom({
  candidate,
  job,
  session,
  messages,
  onSendAnswer,
  isEvaluating
}) {
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [preferredVoice, setPreferredVoice] = useState(null);
  const [statusState, setStatusState] = useState('ready'); // ready, speaking, listening, evaluating

  const recognitionRef = useRef(null);
  const chatBottomRef = useRef(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isEvaluating]);

  // Load natural TTS voice
  useEffect(() => {
    const updateVoices = () => {
      if ('speechSynthesis' in window) {
        const voices = window.speechSynthesis.getVoices();
        const bestVoice = voices.find(v => 
          v.name.includes("Google US English") || 
          v.name.includes("Natural") || 
          v.name.includes("Samantha") || 
          v.name.includes("Alex")
        ) || voices[0];
        setPreferredVoice(bestVoice);
      }
    };

    updateVoices();
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }, []);

  // Setup Browser Speech Recognition (STT)
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;

      rec.onstart = () => {
        setIsListening(true);
        setStatusState('listening');
      };

      rec.onresult = (e) => {
        const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
        setInputText(transcript);
      };

      rec.onend = () => {
        setIsListening(false);
        setStatusState('ready');
      };

      rec.onerror = () => {
        setIsListening(false);
        setStatusState('ready');
      };

      recognitionRef.current = rec;
    }
  }, []);

  // Speak AI Question text when new assistant message arrives
  const lastMessage = messages[messages.length - 1];
  useEffect(() => {
    if (lastMessage && lastMessage.role === 'assistant' && ttsEnabled && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(lastMessage.content);
      if (preferredVoice) utterance.voice = preferredVoice;
      utterance.rate = 1.0;

      utterance.onstart = () => {
        setIsSpeaking(true);
        setStatusState('speaking');
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setStatusState('ready');
      };

      window.speechSynthesis.speak(utterance);
    }
  }, [lastMessage, ttsEnabled, preferredVoice]);

  // Toggle STT Microphone
  const toggleMicrophone = () => {
    if (!recognitionRef.current) {
      alert('Speech Recognition API is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    if (!isListening) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setInputText('');
      recognitionRef.current.start();
    } else {
      recognitionRef.current.stop();
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isEvaluating) return;
    const answer = inputText;
    setInputText('');
    setStatusState('evaluating');
    onSendAnswer(answer);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
      
      {/* Candidate & Position Context Bar */}
      <div className="glass-card" style={{ padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <span style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '1px', color: '#06b6d4', fontWeight: '700' }}>
            Active Candidate
          </span>
          <h3 style={{ fontSize: '1.15rem', fontWeight: '700' }}>{candidate?.name || 'Alex Chen'}</h3>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Position: {job?.title || 'Senior Backend Engineer'}</p>
        </div>

        {/* Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setTtsEnabled(!ttsEnabled)}
            style={{ padding: '6px 14px', fontSize: '0.82rem' }}
          >
            {ttsEnabled ? <Volume2 size={16} color="#10b981" /> : <VolumeX size={16} color="#f43f5e" />}
            TTS Voice: {ttsEnabled ? 'On' : 'Off'}
          </button>

          <div className={`badge ${
            statusState === 'speaking' ? 'badge-emerald' :
            statusState === 'listening' ? 'badge-rose' :
            statusState === 'evaluating' ? 'badge-purple' : 'badge-cyan'
          }`}>
            {statusState === 'speaking' && '🤖 AI Interviewer Talking...'}
            {statusState === 'listening' && '🔴 Mic Active (Listening...)'}
            {statusState === 'evaluating' && '⏳ AI Evaluating Answer...'}
            {statusState === 'ready' && '🟢 Ready for Candidate Answer'}
          </div>
        </div>
      </div>

      {/* Main Room Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '20px' }}>
        
        {/* Left Column: Animated AI Avatar Visualizer */}
        <div className="glass-card avatar-container" style={{ textAlign: 'center' }}>
          <div className={`avatar-ring ${isSpeaking ? 'speaking' : ''}`}>
            🤖
          </div>
          <h4 style={{ marginTop: '12px', fontSize: '0.95rem', fontWeight: '600' }}>AI Technical Interviewer</h4>
          <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>Gemini 3.6 Multi-Agent</p>

          {/* Equalizer Audio Waveform */}
          <div className={`sound-waveform ${isSpeaking ? 'active' : ''}`}>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
            <div className="wave-bar"></div>
          </div>

          <div style={{ marginTop: '20px', textAlign: 'left', width: '100%', fontSize: '0.78rem', color: '#94a3b8', background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: '8px' }}>
            <p style={{ fontWeight: '600', color: '#f8fafc', marginBottom: '4px' }}>💡 How to Answer:</p>
            1. Listen to the AI question.<br />
            2. Click the red microphone button to speak.<br />
            3. Pause speaking or click again to submit!
          </div>
        </div>

        {/* Right Column: Chat & Speech Input */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '520px' }}>
          
          {/* Chat Messages */}
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  gap: '12px',
                  alignSelf: msg.role === 'assistant' ? 'flex-start' : 'flex-end',
                  maxWidth: '85%'
                }}
              >
                {msg.role === 'assistant' && (
                  <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: '#06b6d4', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Bot size={18} color="#ffffff" />
                  </div>
                )}

                <div style={{
                  background: msg.role === 'assistant' ? 'rgba(15, 23, 42, 0.9)' : 'rgba(59, 130, 246, 0.2)',
                  border: msg.role === 'assistant' ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid rgba(59, 130, 246, 0.4)',
                  padding: '14px 18px',
                  borderRadius: '14px',
                  color: '#f8fafc',
                  fontSize: '0.94rem',
                  lineHeight: '1.5'
                }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: '700', color: msg.role === 'assistant' ? '#06b6d4' : '#60a5fa', marginBottom: '4px' }}>
                    {msg.role === 'assistant' ? '🤖 AI Interviewer' : '👤 Candidate (Alex)'}
                  </div>
                  {msg.content}
                </div>

                {msg.role === 'user' && (
                  <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <User size={18} color="#ffffff" />
                  </div>
                )}
              </div>
            ))}

            {isEvaluating && (
              <div style={{ display: 'flex', gap: '12px', alignSelf: 'flex-start' }}>
                <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Clock size={18} color="#ffffff" />
                </div>
                <div style={{ background: 'rgba(139, 92, 246, 0.15)', border: '1px solid rgba(139, 92, 246, 0.3)', padding: '12px 18px', borderRadius: '14px', color: '#c084fc', fontSize: '0.9rem', fontStyle: 'italic' }}>
                  Multi-Agent Graph evaluating candidate answer against JD & Resume...
                </div>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* Speech-to-Text Input Control Bar */}
          <form onSubmit={handleFormSubmit} style={{ marginTop: '16px', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              type="button"
              className={`btn btn-mic ${isListening ? 'recording' : ''}`}
              onClick={toggleMicrophone}
              disabled={isEvaluating}
              style={{ padding: '12px 16px', flexShrink: 0 }}
              title={isListening ? 'Click to stop listening' : 'Click to speak your answer'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
              {isListening ? 'Listening...' : 'Speak'}
            </button>

            <input
              type="text"
              className="input-field"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={isListening ? 'Listening to your voice...' : 'Type or speak your technical answer...'}
              disabled={isEvaluating}
            />

            <button type="submit" className="btn btn-primary" style={{ padding: '12px 20px', flexShrink: 0 }} disabled={!inputText.trim() || isEvaluating}>
              <Send size={18} />
            </button>
          </form>

        </div>
      </div>
    </div>
  );
}
