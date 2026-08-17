"""Terminal Voice Demo Script using Speech-to-Text & Text-to-Speech."""

import asyncio
import sys
import httpx

BASE_URL = "http://localhost:8000"

def speak(text: str) -> None:
    print(f"\n🤖 AI Interviewer: {text}")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        # Fallback if pyttsx3 is not installed
        pass

def listen() -> str:
    print("\n🎙️ Listening... Speak your answer into the microphone:")
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source)
            text = r.recognize_google(audio)
            print(f"🗣️ Transcribed Answer: {text}")
            return text
    except Exception:
        # Fallback to terminal input if audio libraries are missing
        return input("Enter your answer (text fallback): ")

async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        health = await client.get("/health")
        if health.status_code != 200:
            print("API not running. Please start uvicorn backend server first!")
            sys.exit(1)

        start_resp = await client.post("/interviews", json={"candidate_id": 1, "job_id": 1})
        start_resp.raise_for_status()
        interview = start_resp.json()
        
        print(f"=== Started Voice Interview Session #{interview['id']} ===")
        
        while interview["status"] != "completed":
            question = interview.get("current_question", "")
            if not question:
                break
                
            speak(question)
            
            answer = ""
            while not answer:
                answer = listen()
                
            msg_resp = await client.post(
                f"/interviews/{interview['id']}/messages",
                json={"content": answer}
            )
            msg_resp.raise_for_status()
            interview = msg_resp.json()

        speak("Thank you! The interview session is now complete.")

if __name__ == "__main__":
    asyncio.run(main())
