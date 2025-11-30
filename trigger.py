import speech_recognition as sr
import requests
import pyttsx3
import os
import threading
import queue
import time
import io
from datetime import datetime
from dotenv import load_dotenv
from rapidfuzz import fuzz

# Try to import OpenAI and pygame for TTS
try:
    from openai import OpenAI
    import pygame
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

load_dotenv()

# Configuration
WAKE_WORD = os.getenv("WAKE_WORD", "anka")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
LANGUAGE = os.getenv("LANGUAGE", "en-US")
RECOGNITION_TIMEOUT = int(os.getenv("RECOGNITION_TIMEOUT", 10))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY and OPENAI_AVAILABLE else None

class VoiceAssistant:
    def __init__(self):
        self.is_running = False
        self.event_queue = queue.Queue()
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.recognizer = self._setup_recognizer()
        self.mic = sr.Microphone()
        self.thread = None
        
        # Initialize pygame mixer for OpenAI TTS
        if OPENAI_AVAILABLE:
            pygame.mixer.init(frequency=24000)

    def _setup_recognizer(self):
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 50
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.pause_threshold = 0.8
        return recognizer

    def log(self, message, type="info"):
        """Emit a log event to the frontend"""
        self.event_queue.put({"type": "log", "message": message, "level": type})
        print(f"[{type.upper()}] {message}")

    def speak(self, text):
        """Speak text using OpenAI TTS or pyttsx3 fallback"""
        self.event_queue.put({"type": "speaking", "text": text})
        
        # Try OpenAI TTS first
        if openai_client:
            try:
                self._speak_openai(text)
            except Exception as e:
                self.log(f"OpenAI TTS failed: {e}, using fallback", "warning")
                self._speak_pyttsx3(text)
        else:
            self._speak_pyttsx3(text)
        
        self.event_queue.put({"type": "speaking_stopped"})
    
    def _speak_openai(self, text):
        """Use OpenAI TTS to generate and play audio"""
        # Generate speech using OpenAI
        response = openai_client.audio.speech.create(
            model="tts-1",  # Use tts-1-hd for higher quality
            voice="nova",   # nova, alloy, echo, fable, onyx, shimmer
            input=text
        )
        
        # Play audio using pygame
        audio_data = io.BytesIO(response.content)
        pygame.mixer.music.load(audio_data)
        pygame.mixer.music.play()
        
        # Wait for audio to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    
    def _speak_pyttsx3(self, text):
        """Fallback TTS using pyttsx3"""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        self.log("Voice Assistant Started", "success")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.log("Voice Assistant Stopped", "warning")

    def _run_loop(self):
        with self.mic as source:
            self.log("Calibrating microphone for 5 seconds...", "info")
            self.log("Please remain quiet during calibration.", "info")
            self.recognizer.adjust_for_ambient_noise(source, duration=5)
            self.log(f"Ready! Threshold: {self.recognizer.energy_threshold:.0f}", "success")
            self.log(f"You can now speak normally from a comfortable distance.", "info")

        while self.is_running:
            try:
                if self._listen_for_wake_word():
                    question = self._listen_for_question()
                    if question:
                        self._process_question(question)
            except Exception as e:
                self.log(f"Error in main loop: {e}", "error")
                time.sleep(1)

    def _listen_for_wake_word(self):
        self.event_queue.put({"type": "status", "status": "listening_wake"})
        
        try:
            with self.mic as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio, language=LANGUAGE).lower()
            
            words = text.split()
            best_score = 0
            
            for word in words:
                score = fuzz.ratio(WAKE_WORD, word)
                if score > best_score:
                    best_score = score
            
            if best_score >= 30:
                self.log(f"Wake word detected! ({best_score}%)", "success")
                return True
            else:
                return False
                
        except sr.WaitTimeoutError:
            return False
        except sr.UnknownValueError:
            return False
        except sr.RequestError as e:
            self.log(f"API Error: {e}", "error")
            return False

    def _listen_for_question(self):
        self.event_queue.put({"type": "status", "status": "listening_question"})
        self.log("Listening for question...", "info")
        self.speak("Yes?")
        
        try:
            with self.mic as source:
                audio = self.recognizer.listen(source, timeout=15, phrase_time_limit=20)
            
            question = self.recognizer.recognize_google(audio, language=LANGUAGE)
            self.log(f"Question: {question}", "info")
            self.event_queue.put({"type": "transcription", "text": question})
            return question
            
        except sr.WaitTimeoutError:
            self.log("No question detected", "warning")
            return None
        except sr.UnknownValueError:
            self.log("Could not understand audio", "warning")
            self.speak("Sorry, I didn't catch that.")
            return None
        except sr.RequestError as e:
            self.log(f"Speech service error: {e}", "error")
            return None

    def _process_question(self, question):
        self.event_queue.put({"type": "status", "status": "processing"})
        
        if not N8N_WEBHOOK_URL:
            self.log("N8N URL not configured", "error")
            return

        payload = {
            "text": f"Anka, {question}",
            "timestamp": datetime.now().isoformat(),
            "language": "English"
        }

        try:
            response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=30)
            response.raise_for_status()
            
            # Try to parse as JSON first, fall back to text
            try:
                data = response.json()
                text_response = data.get('message') or data.get('text') or str(data)
            except:
                # If not JSON, use the text response directly
                text_response = response.text
            
            self.log(f"Response: {text_response}", "success")
            self.event_queue.put({"type": "response", "text": text_response})
            
            # ALWAYS speak the response with OpenAI TTS
            self.speak(text_response)
            
        except Exception as e:
            self.log(f"Failed to get response: {e}", "error")
            error_msg = "I'm having trouble connecting to my brain."
            self.event_queue.put({"type": "response", "text": error_msg})
            self.speak(error_msg)

# Global instance for Flask to use
assistant = VoiceAssistant()

if __name__ == "__main__":
    try:
        assistant.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        assistant.stop()