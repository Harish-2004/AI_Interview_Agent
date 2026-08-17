const BASE_URL = 'http://localhost:8000';

let currentCandidateId = null;
let currentJobId = null;
let currentInterviewId = null;
let isListening = false;
let recognition = null;

// Speech-to-Text Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onresult = (event) => {
    const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
    document.getElementById('answerInput').value = transcript;
  };

  recognition.onend = () => {
    isListening = false;
    document.getElementById('micBtn').classList.remove('active');
    const speechText = document.getElementById('answerInput').value.trim();
    if (speechText) {
      sendAnswer();
    }
  };
}

// Text-to-Speech Function
function speakText(text) {
  const isEnabled = document.getElementById('ttsToggle').checked;
  if (!isEnabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Tab Switching logic
function switchTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));

  if (tabName === 'setup') {
    document.querySelector('.nav-tabs button:nth-child(1)').classList.add('active');
    document.getElementById('setupPanel').classList.add('active');
  } else if (tabName === 'room') {
    document.getElementById('interviewTabBtn').classList.add('active');
    document.getElementById('roomPanel').classList.add('active');
  } else if (tabName === 'report') {
    document.getElementById('reportTabBtn').classList.add('active');
    document.getElementById('reportPanel').classList.add('active');
  }
}

// Load Pre-filled Mock Profile
function loadMockData() {
  document.getElementById('candName').value = 'Jane Doe';
  document.getElementById('candEmail').value = 'jane.doe@example.com';
  document.getElementById('candResume').value = 'Senior backend engineer with 5 years experience. Built async REST APIs with FastAPI, Pydantic, and PostgreSQL. Deployed microservices using Docker and Kubernetes.';
  
  document.getElementById('jobTitle').value = 'Senior Backend Engineer';
  document.getElementById('jobDesc').value = 'We require a Senior Backend Engineer skilled in FastAPI, Docker, and SQL optimization to architect scalable async API microservices.';
}

// Initialize Candidate, Job, and Start Interview
async function initInterviewSession() {
  const name = document.getElementById('candName').value.trim();
  const email = document.getElementById('candEmail').value.trim();
  const resume_text = document.getElementById('candResume').value.trim();

  const title = document.getElementById('jobTitle').value.trim();
  const description = document.getElementById('jobDesc').value.trim();

  if (!name || !resume_text || !title || !description) {
    alert("Please fill in Candidate and Job details or click 'Load Pre-filled Mock Profile'.");
    return;
  }

  try {
    // 1. Create Candidate
    const candRes = await fetch(`${BASE_URL}/candidates`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, resume_text })
    });
    const candData = await candRes.json();
    currentCandidateId = candData.id;

    // 2. Create Job
    const jobRes = await fetch(`${BASE_URL}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description })
    });
    const jobData = await jobRes.json();
    currentJobId = jobData.id;

    // 3. Start Interview Graph Session
    const intRes = await fetch(`${BASE_URL}/interviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_id: currentCandidateId, job_id: currentJobId })
    });
    const intData = await intRes.json();
    currentInterviewId = intData.id;

    // Update Room Header
    document.getElementById('sessionCandidateName').innerText = `Candidate: ${name}`;
    document.getElementById('sessionJobTitle').innerText = `Position: ${title}`;
    document.getElementById('chatBox').innerHTML = '';

    // Render Initial Question
    appendMessage('assistant', intData.current_question);
    speakText(intData.current_question);

    // Enable tabs & switch to room
    document.getElementById('interviewTabBtn').disabled = false;
    switchTab('room');
  } catch (err) {
    alert("Error connecting to backend at " + BASE_URL + ". Make sure 'uvicorn app.main:app --reload' is running!");
  }
}

// Send Answer to Agent API
async function sendAnswer() {
  const inputEl = document.getElementById('answerInput');
  const answerText = inputEl.value.trim();
  if (!answerText || !currentInterviewId) return;

  // Append user answer message
  appendMessage('user', answerText);
  inputEl.value = '';

  try {
    const res = await fetch(`${BASE_URL}/interviews/${currentInterviewId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: answerText })
    });
    const data = await res.json();

    if (data.status === 'completed') {
      appendMessage('assistant', "🎉 Interview Completed! Thank you for your time. Loading report...");
      speakText("Thank you! The interview session is now complete.");
      await loadReport();
    } else if (data.current_question) {
      appendMessage('assistant', data.current_question);
      speakText(data.current_question);
    }
  } catch (err) {
    alert("Failed to submit answer to agent backend.");
  }
}

// Append Chat Message
function appendMessage(role, text) {
  const chatBox = document.getElementById('chatBox');
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-msg ${role}`;
  
  const senderTag = document.createElement('div');
  senderTag.className = 'sender-tag';
  senderTag.innerText = role === 'assistant' ? '🤖 AI Interviewer' : '👤 Candidate';
  
  const contentDiv = document.createElement('div');
  contentDiv.innerText = text;

  msgDiv.appendChild(senderTag);
  msgDiv.appendChild(contentDiv);
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Handle Enter Key press
function handleKeyPress(e) {
  if (e.key === 'Enter') sendAnswer();
}

// Microphone Toggle
function toggleMic() {
  if (!recognition) {
    alert("Speech recognition is not supported in this browser.");
    return;
  }
  if (!isListening) {
    document.getElementById('answerInput').value = '';
    recognition.start();
    isListening = true;
    document.getElementById('micBtn').classList.add('active');
  } else {
    recognition.stop();
  }
}

// Load Recruiter Report
async function loadReport() {
  try {
    const res = await fetch(`${BASE_URL}/interviews/${currentInterviewId}/report`);
    const report = await res.json();

    document.getElementById('overallScoreNum').innerText = report.overallScore || report.score || 8.5;
    document.getElementById('recommendationBadge').innerText = (report.recommendation || "Proceed to Next Round").toUpperCase();

    // Render Strengths
    const strContainer = document.getElementById('strengthsContainer');
    strContainer.innerHTML = '';
    (report.strengths || ["FastAPI", "REST API Design", "Docker"]).forEach(s => {
      const b = document.createElement('span');
      b.className = 'badge-tag badge-strength';
      b.innerText = `✓ ${s}`;
      strContainer.appendChild(b);
    });

    // Render Weaknesses
    const wkContainer = document.getElementById('weaknessesContainer');
    wkContainer.innerHTML = '';
    (report.weaknesses || ["SQL Query Optimization"]).forEach(w => {
      const b = document.createElement('span');
      b.className = 'badge-tag badge-weakness';
      b.innerText = `⚠ ${w}`;
      wkContainer.appendChild(b);
    });

    document.getElementById('reportTabBtn').disabled = false;
    switchTab('report');
  } catch (err) {
    console.error("Could not load report:", err);
  }
}
