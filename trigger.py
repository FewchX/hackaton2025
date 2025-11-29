import speech_recognition as sr
import requests
import pyttsx3
import os
from datetime import datetime
from dotenv import load_dotenv
from rapidfuzz import fuzz

load_dotenv()

# Configuration
WAKE_WORD = os.getenv("WAKE_WORD", "anka")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
LANGUAGE = os.getenv("LANGUAGE", "en-US")
RECOGNITION_TIMEOUT = int(os.getenv("RECOGNITION_TIMEOUT", 10))

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)  # Speed of speech

def setup_recognizer():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 100  # Very low - maximum sensitivity
    recognizer.dynamic_energy_adjustment_damping = 0.10  # Faster adaptation
    recognizer.dynamic_energy_ratio = 1.2  # Lower ratio for noisy environments
    recognizer.pause_threshold = 1.0  # Allow longer pauses
    return recognizer

def listen_for_wake_word():
    """Continuously listen for wake word"""
    recognizer = setup_recognizer()
    mic = sr.Microphone()
    
    print(f"\n👂 Listening for wake word '{WAKE_WORD}'...")
    
    with mic as source:
        print("🔧 Calibrating microphone for noisy environment...")
        print("   (Please stay quiet for 5 seconds)")
        recognizer.adjust_for_ambient_noise(source, duration=5)
        
        # Get current energy level
        energy_level = recognizer.energy_threshold
        print(f"✅ Ready! Energy threshold: {energy_level:.0f}")
        print(f"💡 Tip: Speak CLEARLY and LOUDLY near your microphone\n")
    
    while True:
        try:
            with mic as source:
                # Show that we're actively listening
                print("   [Listening...]", end='\r')
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            text = recognizer.recognize_google(audio, language=LANGUAGE).lower()
            
            # Split text into words and check each one
            words = text.split()
            best_match = ""
            best_score = 0
            
            for word in words:
                # Calculate similarity score (0-100)
                score = fuzz.ratio(WAKE_WORD, word)
                if score > best_score:
                    best_score = score
                    best_match = word
            
            # Accept if similarity is 70% or higher
            if best_score >= 70:
                print(f"   ✓ Heard: '{text}' → Matched '{best_match}' ({best_score:.0f}% similar)     ")
                print(f"✅ Wake word '{WAKE_WORD}' detected!")
                return True
            else:
                print(f"   ✗ Heard: '{text}' → Best: '{best_match}' ({best_score:.0f}% similar)       ")
        
        except sr.UnknownValueError:
            print("   [...]", end='\r')  # Show we're still here
        except sr.RequestError as e:
            print(f"\n❌ API error: {e}")
        except sr.WaitTimeoutError:
            pass  # Timeout, keep listening

def listen_for_question():
    """Listen for the actual question after wake word"""
    recognizer = setup_recognizer()
    mic = sr.Microphone()
    
    print("\n🎤 I'm listening... What's your question?")
    
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
            audio = recognizer.listen(source, timeout=RECOGNITION_TIMEOUT, phrase_time_limit=20)
        
        question = recognizer.recognize_google(audio, language=LANGUAGE)
        print(f"📝 Question: \"{question}\"")
        return question
    
    except sr.UnknownValueError:
        print("❌ Sorry, I didn't understand that")
        return None
    except sr.RequestError as e:
        print(f"❌ Speech recognition error: {e}")
        return None
    except sr.WaitTimeoutError:
        print("❌ No question detected")
        return None

def send_to_n8n_and_speak(question):
    """Send question to n8n and speak the text response"""
    if not N8N_WEBHOOK_URL:
        print("⚠️  N8N webhook URL not configured in .env")
        return None
    
    payload = {
        "text": f"Anka, {question}",
        "timestamp": datetime.now().isoformat(),
        "language": "English"
    }
    
    print("📤 Sending to n8n...")
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Response received (Status: {response.status_code})")
        
        # Get the text response
        try:
            data = response.json()
            text_response = data.get('message') or data.get('text') or str(data)
        except ValueError:
            text_response = response.text
        
        if text_response:
            print(f"💬 Response: {text_response}")
            print("🔊 Speaking...")
            
            # Speak the response
            tts_engine.say(text_response)
            tts_engine.runAndWait()
            
            print("✅ Done")
        else:
            print("⚠️  Empty response from n8n")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send to n8n: {e}")
        return None

def main():
    print("=" * 60)
    print("🎙️  ANKA - Voice AI Assistant (FUZZY MATCH MODE)")
    print("=" * 60)
    print(f"Wake word: '{WAKE_WORD}'")
    print(f"n8n webhook: {N8N_WEBHOOK_URL}")
    print(f"Language: {LANGUAGE}")
    print("=" * 60)
    print(f"\nSay '{WAKE_WORD}' followed by your question")
    print("Press Ctrl+C to exit anytime\n")
    
    try:
        while True:
            # Wait for wake word
            listen_for_wake_word()
            
            # Now listen for the actual question
            question = listen_for_question()
            
            if question:
                send_to_n8n_and_speak(question)
            
            print("\n" + "-" * 60)
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down... Goodbye!")

if __name__ == "__main__":
    main()