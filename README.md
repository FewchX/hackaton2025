# Voice Assistant with Multi-Agent AI System "ANKA"(TELIT Hackathon2025)

A hybrid voice and text-based assistant that integrates with a sophisticated n8n multi-agent workflow for intelligent query processing.

## Overview

This project combines a local voice assistant frontend with a cloud-based multi-agent AI system. The assistant can accept input through both voice commands (using wake word "Anka") and text input, processing queries through an intelligent agent orchestration system that dynamically assembles expert teams based on query complexity.

## Architecture

### Frontend Components

- **Flask Web Server** (`app.py`) - Serves the web interface and handles API requests
- **Voice Recognition** (`trigger.py`) - Handles wake word detection, speech-to-text, and text-to-speech
- **Web UI** - Modern chat interface with both voice and text input capabilities

### Backend Processing (n8n Workflow)

The n8n workflow implements a multi-agent system with the following stages:

1. **Manager Agent** - Analyzes incoming requests and determines complexity (1-5 scale)
2. **Role Selection** - Dynamically selects solver and reviewer agents based on task requirements
3. **Parallel Processing** - Multiple specialist agents work on the problem simultaneously
4. **Evaluation Layer** - Reviewer agents critically assess solutions across 5 dimensions
5. **Synthesis** - Chief Editor consolidates all feedback into a final response

## Features

### Voice Capabilities
- Wake word detection ("Anka")
- Continuous listening with adjustable sensitivity
- Speech-to-text using Google Speech Recognition
- Text-to-speech using OpenAI TTS (natural-sounding voice)
- Fallback to pyttsx3 if OpenAI is unavailable

### Text Capabilities
- Direct text input through web interface
- Typing animations with contextual messages
- Real-time response streaming via Server-Sent Events

### Multi-Agent Processing
- Adaptive complexity assessment
- Dynamic team assembly from available roles
- Parallel solver execution
- Multi-perspective evaluation
- Consensus-based final answers
- Context persistence in Supabase
- RAG (Retrieval-Augmented Generation) support for document queries

## Prerequisites

### Required Accounts
- OpenAI API account (for GPT-4 and TTS)
- n8n Cloud account or self-hosted n8n instance
- Supabase account (for role prompts and context storage)

### System Requirements
- Python 3.8+
- Microphone for voice input
- Audio output device
- Modern web browser

## Installation

### 1. Clone the Repository

```bash
cd Hackathon25
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
WAKE_WORD=anka
N8N_WEBHOOK_URL=https://your-n8n-instance.app.n8n.cloud/webhook/anka-wake-word
OPENAI_API_KEY=sk-your-openai-api-key
LANGUAGE=en-US
RECOGNITION_TIMEOUT=10
```

### 4. Set Up n8n Workflow

1. Import the provided n8n workflow JSON into your n8n instance
2. Configure the following credentials in n8n:
   - OpenAI API credentials
   - Supabase API credentials
3. Set up Supabase tables:
   - `role_prompts` - Contains agent roles and their system prompts
   - `user_context` - Stores conversation history

### 5. Populate Role Database

Insert agent roles into Supabase `role_prompts` table:
- Mode: "user" (or custom mode)
- Name: Role name (e.g., "Analyst", "Creative", "Skeptic")
- Prompt: System prompt defining the agent's behavior

## Usage

### Starting the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Using Voice Mode

1. Click the "Voice" button in the web interface
2. Wait for 5-second calibration (stay quiet)
3. Say "Anka" to activate
4. Speak your question clearly
5. Wait for the assistant to process and respond

### Using Text Mode

1. Type your question in the text input field
2. Press Enter or click "Send"
3. The assistant will process your query and respond

### Voice Sensitivity Tuning

If the assistant has trouble hearing you:
- Adjust `energy_threshold` in `trigger.py` (lower = more sensitive)
- Check Windows microphone boost settings
- Ensure correct microphone is selected in system settings

## Project Structure

```
Hackathon25/
├── app.py                 # Flask server & API endpoints
├── trigger.py             # Voice assistant core logic
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── style.css         # UI styling
│   └── script.js         # Frontend JavaScript
└── README.md             # This file
```

## Configuration Options

### Voice Settings (trigger.py)

- `energy_threshold` - Microphone sensitivity (default: 50, lower = more sensitive)
- `pause_threshold` - Silence detection (default: 0.8 seconds)
- `phrase_time_limit` - Max question length (default: 20 seconds)

### TTS Voice Options

Available OpenAI voices (change in `trigger.py` line 89):
- `nova` - Pleasant female (default)
- `alloy` - Neutral
- `echo` - Male
- `fable` - Expressive
- `onyx` - Deep male
- `shimmer` - Soft female

## API Endpoints

- `POST /api/start` - Start voice assistant
- `POST /api/stop` - Stop voice assistant
- `POST /api/ask` - Send text question
- `GET /events` - SSE stream for real-time updates

## Troubleshooting

### Issue: CSS not loading
**Solution**: Hard refresh browser (Ctrl+Shift+R) or open in incognito mode

### Issue: Voice not detected
**Solution**: 
- Lower `energy_threshold` value
- Check microphone permissions
- Increase system microphone boost

### Issue: n8n workflow errors
**Solution**:
- Verify webhook URL in `.env`
- Check OpenAI API key validity
- Ensure Supabase credentials are configured

### Issue: TTS fails
**Solution**: System will automatically fall back to pyttsx3

## Cost Considerations

- OpenAI GPT-4 API calls: ~$0.01-0.10 per query (varies by complexity)
- OpenAI TTS: ~$0.015 per 1000 characters
- n8n Cloud: Free tier available, paid plans for production
- Supabase: Free tier supports up to 500MB database

## Development

### Adding New Agent Roles

1. Add new role to Supabase `role_prompts` table
2. Define role name and comprehensive system prompt
3. The Manager will automatically consider it for task assignment

### Modifying Workflow Logic

Edit the n8n workflow to:
- Change complexity scoring criteria
- Adjust evaluation dimensions
- Add new tools or integrations
- Modify synthesis logic

## License

This project is provided as-is for educational and development purposes.

## Credits

Built with:
- Flask
- speech_recognition
- OpenAI API
- n8n workflow automation
- Supabase
- pyttsx3 / pygame


