import speech_recognition as sr
import pyaudio
import pvcobra
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
WAKE_WORD = os.getenv("WAKE_WORD", "anka")
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGUAGE = os.getenv("LANGUAGE", "sk-SK")
RECOGNITION_TIMEOUT = int(os.getenv("RECOGNITION_TIMEOUT", 10))

def setup_recognizer():
    recognizer = sr.Recognizer()
    # Dynamic energy threshold - adjusts automatically to ambient noise
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 1000 # Lower threshold for better sensitivity
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = 0.8  # Shorter pause detection
    return recognizer

def listen_for_wake_word():
    recognizer = setup_recognizer()
    mic = sr.Microphone()
    
    print(f"🎤 Listening for wake word: '{WAKE_WORD}'...")
    
    with mic as source:
        # Longer noise adjustment for better accuracy
        recognizer.adjust_for_ambient_noise(source, duration=2)
    
    while True:
        try:
            with mic as source:
                # More forgiving timeouts for wake word
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            # Use Google Speech Recognition for Slovak
            text = recognizer.recognize_google(audio, language=LANGUAGE).lower()
            print(f"Detected: {text}")
            
            if WAKE_WORD in text:
                print(f"✅ Wake word '{WAKE_WORD}' detected!")
                return True
        
        except sr.UnknownValueError:
            pass  
        except sr.RequestError as e:
            print(f"❌ API error: {e}")
        except sr.WaitTimeoutError:
            pass 

def listen_for_question(recognizer):
    mic = sr.Microphone()
    
    print(f"⏱️  Listening for question ({RECOGNITION_TIMEOUT}s)...")
    
    try:
        with mic as source:
            # Adjust for current ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
            # More forgiving timeouts for questions
            audio = recognizer.listen(source, timeout=RECOGNITION_TIMEOUT, phrase_time_limit=15)
        
        question = recognizer.recognize_google(audio, language=LANGUAGE)
        print(f"📝 Question: {question}")
        return question
    
    except sr.UnknownValueError:
        print("❌ Could not understand the question")
        return None
    except sr.RequestError as e:
        print(f"❌ API error: {e}")
        return None
    except sr.WaitTimeoutError:
        print("❌ No speech detected within timeout")
        return None

def send_to_n8n(question):
    if not N8N_WEBHOOK_URL:
        print("⚠️  N8N webhook URL not configured. Skipping n8n integration.")
        return None
    
    payload = {
        "text": f"Anka, {question}",
        "timestamp": datetime.now().isoformat(),
        "language": "Slovak"
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"✅ Sent to n8n. Status: {response.status_code}")
        print(f"Response text: '{response.text}'")
        if response.text:
            print(f"Response length: {len(response.text)} characters")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send to n8n: {e}")
        return None

def send_to_openai(question):
    if not OPENAI_API_KEY:
        print("⚠️  OpenAI API key not configured.")
        return None
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Odpoveď na túto otázku (v slovenčine): {question}"
                    }
                ]
            }
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        print(f"🤖 AI Response: {answer}")
        return answer
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAI API error: {e}")
        return None

def main():
    print("=" * 50)
    print("Slovak Voice Assistant - Anka (Enhanced)")
    print("=" * 50)
    print("Improvements:")
    print("✓ Dynamic noise adjustment")
    print("✓ Better sensitivity in noisy environments")
    print("✓ More forgiving speech recognition")
    print("=" * 50)
    
    recognizer = setup_recognizer()
    
    try:
        while True:
            listen_for_wake_word()
            
            question = listen_for_question(recognizer)
            
            if question:
                n8n_result = send_to_n8n(question)
                
                print("-" * 50)
            
            print(f"🎤 Listening for wake word again...\n")
    
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == "__main__":
    main()