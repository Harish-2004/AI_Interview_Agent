# Frontend Web Application

A modern, high-performance web interface for the AI Interview Agent built with custom CSS design tokens, live Speech-to-Text (STT) voice input, Text-to-Speech (TTS) synthesizer, and recruiter reporting dashboard.

## How to Run Frontend

1. Ensure the FastAPI backend is running on `http://localhost:8000`:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Simply open `frontend/index.html` in Google Chrome or Microsoft Edge!
   - Or serve with any static web server: `npx serve frontend` / `python -m http.server --directory frontend 3000`

## Features

- **Candidate & JD Onboarding**: Upload custom resumes/JDs or click "Load Pre-filled Mock Profile".
- **Live Voice & Text Interview Room**:
  - Microphone Speech-to-Text input.
  - Automatic Text-to-Speech AI voice question narration.
- **Recruiter Evaluation Dashboard**: Real-time score metrics, strengths/weaknesses tags, and print-ready report generator.
