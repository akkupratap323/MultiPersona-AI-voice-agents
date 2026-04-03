# NesterVoiceAI - Real-time Voice Assistant

A production-ready real-time voice conversational assistant built with [Pipecat](https://github.com/pipecat-ai/pipecat). Features speech-to-text, emotion-aware text-to-speech, LightRAG knowledge retrieval, and dynamic visual UI generation (A2UI).

**Developed and open-sourced by [NesterLabs](https://nesterlabs.com)**

## Features

- **Real-time Voice Conversation**: WebSocket-based audio streaming with 1-1.5 second response times
- **Speech-to-Text**: Deepgram Nova-3 for accurate real-time transcription
- **Emotion-Aware TTS**: Chatterbox TTS via Resemble AI with dynamic emotion control
- **Hybrid Emotion Detection**: MSP-PODCAST wav2vec2 (audio 70%) + Groq LLM (text sentiment 30%)
- **LightRAG Integration**: Graph-based knowledge retrieval with streaming support
- **A2UI Visual Responses**: Dynamic UI components generated from voice queries
- **Barge-in Support**: Users can interrupt the bot mid-speech (MinWordsInterruptionStrategy)
- **Automated CI/CD**: GitHub Actions with Docker deployment to AWS Lightsail


## Architecture

```
┌─────────────────┐
│   Web Client    │
│   (TypeScript)  │
└────────┬────────┘
         │ WebSocket
┌────────▼────────┐
│   FastAPI       │
│   + Pipecat     │
└────────┬────────┘
         │
┌────────▼────────────────────────────────────────┐
│              Voice Assistant Pipeline            │
├──────────┬──────────┬───────────┬───────────────┤
│   STT    │   LLM    │    RAG    │     TTS       │
│ Deepgram │  Groq    │ LightRAG  │  Chatterbox   │
│  Nova-3  │ Llama-3  │  + A2UI   │  + Emotion    │
└──────────┴──────────┴───────────┴───────────────┘
```

## Project Structure

```
nester-ai-voice-assistant/
├── app/                    # Main application
│   ├── api/                # FastAPI routes & WebSocket
│   ├── config/             # Configuration (config.yaml)
│   ├── core/               # Voice assistant orchestrator
│   ├── processors/         # Pipecat processors (tone, text filter)
│   ├── services/           # STT, TTS, RAG, LLM, emotion detection
│   └── utils/              # Helper functions
├── client/                 # TypeScript web client
├── deployment/             # Docker & AWS configs
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── tests/                  # Test files
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for client)
- API Keys:
  - Deepgram (STT)
  - Groq (LLM)
  - Resemble AI (TTS with emotion)

### Installation

1. **Clone and install**:
```bash
git clone <repository-url>
cd nester-ai-voice-assistant
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```bash
# Required
DEEPGRAM_API_KEY=your_deepgram_key
GOOGLE_API_KEY=your_google_gemini_key
RESEMBLE_API_KEY=your_resemble_key

# Optional - LightRAG
LIGHTRAG_API_KEY=your_lightrag_key
```

3. **Run the server**:
```bash
export PYTHONPATH=$(pwd)
python app/main.py
```

4. **Run the client**:
```bash
cd client
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Share Your Bot (ngrok)

Want to share your bot with others? Use ngrok to create a public URL:

```bash
# One-time setup
./scripts/setup-ngrok.sh

# Start bot + ngrok (automatic)
./scripts/demo-bot.sh

# Or manually in separate terminals:
# Terminal 1: python app/main.py
# Terminal 2: ./scripts/start-ngrok.sh
```

Share the HTTPS URL with anyone! See [QUICK_START_NGROK.md](QUICK_START_NGROK.md) for details.

## Configuration

Main configuration is in `app/config/config.yaml`:

```yaml
# Speech-to-Text
stt:
  provider: "deepgram"
  config:
    model: "nova-3"
    endpointing: 800

# Text-to-Speech (Emotion-aware)
tts:
  provider: "chatterbox"
  config:
    api_key: "${RESEMBLE_API_KEY}"

# LLM
conversation:
  llm:
    provider: "google"
    model: "gemini-2.0-flash"

# Knowledge Retrieval
rag:
  type: "lightrag"
  config:
    mode: "local"
    use_streaming: true

# Visual UI Generation
a2ui:
  enabled: true
  config:
    tier_mode: "auto"

# Emotion Detection
server:
  emotion_detection_enabled: true
```

## Key Components

### Emotion Detection
Hybrid system combining:
- **Audio**: MSP-PODCAST trained wav2vec2 model (70% weight)
- **Text**: Groq LLM sentiment analysis (30% weight)

Detected emotions dynamically adjust TTS voice characteristics via Chatterbox.

### A2UI (Agentic UI)
Generates visual components from voice queries:
- Contact cards, service grids, team profiles
- FAQ accordions, comparison charts
- Automatically matched to query intent

### Barge-in Support
Users can interrupt bot speech using MinWordsInterruptionStrategy (requires 2+ words to prevent accidental interruptions from backchanneling).

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws` | WebSocket | Real-time voice communication |
| `/health` | GET | Health check |
| `/status` | GET | Server and service status |
| `/connect` | POST | Get WebSocket URL and config |

## Deployment

### Docker

```bash
cd deployment/docker
docker-compose -f docker-compose.https.yml up -d
```

### AWS Lightsail

See `deployment/` folder for AWS deployment scripts and Caddyfile for HTTPS.

### CI/CD

Automated deployment via GitHub Actions on push to `main` branch.

## Development

### Adding New Services

1. Create service class in `app/services/`
2. Register in `VoiceAssistant` (`app/core/voice_assistant.py`)
3. Update `app/config/config.yaml`

### Running Tests

```bash
pytest tests/
```

## Troubleshooting

**Audio not working?**
- Check microphone permissions in browser
- Verify Deepgram API key is valid

**Slow responses?**
- Check LightRAG server connectivity
- Monitor latency in console logs

**Emotion detection issues?**
- Ensure MSP-PODCAST model downloads on first run
- Check `emotion_detection_enabled: true` in config

## About NesterLabs

Developed by **[NesterLabs](https://nesterlabs.com)** - an AI-accelerated studio in Sunnyvale, California specializing in voice AI, conversational interfaces, and AI product development.

**Contact**:
- Website: [nesterlabs.com](https://nesterlabs.com)
- Email: contact@nesterlabs.com
- Phone: +1 (408) 673-1340

## License

MIT License - Copyright (c) 2025 NesterLabs

## Acknowledgments

- [Pipecat](https://github.com/pipecat-ai/pipecat) - Real-time AI pipeline framework
- [Deepgram](https://deepgram.com) - Speech-to-text
- [Resemble AI](https://resemble.ai) - Chatterbox TTS
- [Groq](https://groq.com) - LLM inference
