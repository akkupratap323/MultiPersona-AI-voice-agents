# MultiPersona AI Voice Agents

A production-ready, real-time multi-persona voice AI platform built on the [Pipecat](https://github.com/pipecat-ai/pipecat) framework. Five distinct AI agents — each with a unique voice, personality, and role — demonstrate how conversational voice AI can be deployed across different business use cases. Visitors have a natural voice conversation, get their questions answered, and can book a meeting with the team.

**Live end-to-end latency: ~1–1.5 seconds**

---

## Agents

| Agent | Name | Role | Language |
|-------|------|------|----------|
| Receptionist | Brooke | Front-desk welcome, routing, overview | English |
| Customer Support | Blake | Product questions, troubleshooting, escalation | English |
| Hinglish Support | Arushi | Support for the India market | Hinglish (Hindi + English) |
| Sales Consultant | Morgan | Discovery, business value, lead qualification | English |
| Technical Advisor | Daniel | Architecture deep-dives, integration, engineering | English |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [Pipecat](https://github.com/pipecat-ai/pipecat) v0.0.98 |
| Backend | FastAPI + WebSocket |
| Frontend | TypeScript + Vite |
| STT | Deepgram Nova-3 |
| LLM | Groq — `llama-3.1-8b-instant` |
| TTS | Cartesia Sonic-3 |
| VAD | Silero (local, no cloud dependency) |
| End-of-turn | SmartTurn v3 ONNX ML model |
| Emotion Detection | MSP-PODCAST wav2vec2 (70%) + Google Gemini text (30%) |
| Visual UI | A2UI — dynamic component generation from voice |
| Deployment | Docker + Caddy (auto-HTTPS), AWS Lightsail |

---

## Voice Pipeline

```
Audio Input
    → Silero VAD (confidence 0.92)
    → Deepgram Nova-3 STT (WebSocket streaming)
    → SmartTurn v3 ONNX (end-of-turn detection)
    → ToneAwareProcessor (emotion-aware voice switching)
    → LLM Context Aggregator
    → Groq LLM (llama-3.1-8b-instant)
    → VisualHintProcessor (A2UI streaming)
    → TextFilterProcessor (strips markdown before TTS)
    → Cartesia TTS
    → Audio Output
```

---

## Features

- **5 AI Personas** — each with a unique voice, system prompt, personality, and use case scope
- **Real-time voice** — WebSocket audio streaming, ~1–1.5s end-to-end latency
- **Deepgram Nova-3 STT** — streaming transcription, multi-language support
- **Cartesia Sonic-3 TTS** — low-latency neural voice synthesis
- **SmartTurn v3** — ONNX ML model for accurate end-of-turn detection (replaces silence-based)
- **Hybrid Emotion Detection** — non-blocking audio + text sentiment fusion, dynamic voice switching
- **Barge-in** — any speech immediately stops TTS (min_words=0)
- **Hinglish Support** — Hindi + English mixed language for the India market
- **Appointment Booking** — full voice-driven booking flow with Tally.so integration
- **A2UI Visual Responses** — dynamic UI components (cards, grids, timelines) generated from voice
- **Knowledge Graph** — Sigma.js + Graphology visualization in frontend
- **Multi-session** — up to 20 concurrent isolated sessions
- **Docker deployment** — Caddy auto-HTTPS, CPU-only PyTorch, INT8 quantization

---

## Project Structure

```
MultiPersona-AI-voice-agents/
├── app/
│   ├── config/
│   │   ├── config.yaml          # Main configuration (all settings + persona prompts)
│   │   └── loader.py            # YAML loader with ${ENV_VAR} substitution
│   ├── core/
│   │   ├── voice_assistant.py   # Pipeline orchestrator
│   │   └── server.py            # WebSocket session manager
│   ├── processors/
│   │   ├── tone_aware_processor.py       # Emotion detection + voice switching
│   │   ├── text_filter_processor.py      # Strips markdown before TTS
│   │   ├── visual_hint_processor.py      # Word-by-word A2UI streaming
│   │   └── smart_interruption_processor.py
│   ├── services/
│   │   ├── conversation.py      # LLM context, function calling, appointment booking
│   │   ├── groq_llm_service.py  # Groq wrapper (merges consecutive user messages)
│   │   ├── stt.py               # Deepgram STT service
│   │   ├── tts.py               # Cartesia TTS service
│   │   ├── msp_emotion_detector.py      # wav2vec2 audio emotion
│   │   ├── llm_text_sentiment.py        # Gemini text sentiment
│   │   ├── hybrid_emotion_detector.py   # 70/30 fusion
│   │   ├── tally_submission.py          # Appointment booking
│   │   └── a2ui/                        # Visual UI generation system
│   └── main.py                  # FastAPI entrypoint (port 7860)
├── client/
│   ├── src/
│   │   ├── app.ts               # Main frontend app
│   │   └── components/
│   │       ├── a2ui/            # A2UI visual renderers
│   │       └── KnowledgeGraphWidget/    # Sigma.js graph viz
│   ├── public/
│   │   └── config.js            # Runtime frontend config
│   └── index.html
├── deployment/
│   └── docker/
│       ├── docker-compose.https.yml
│       └── Caddyfile
├── tests/
│   ├── unit/
│   └── integration/
└── .env.example
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys (see below)

### 1. Clone and set up backend

```bash
git clone https://github.com/yourusername/MultiPersona-AI-voice-agents.git
cd MultiPersona-AI-voice-agents

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```bash
# Required
DEEPGRAM_API_KEY=your_deepgram_key       # deepgram.com
GROQ_API_KEY=your_groq_key               # console.groq.com (free tier available)
CARTESIA_API_KEY=your_cartesia_key       # play.cartesia.ai
CARTESIA_VOICE_ID=your_voice_id          # from play.cartesia.ai/voices
GOOGLE_API_KEY=your_google_key           # for Gemini text sentiment

# Optional
TALLY_API_KEY=your_tally_key             # for appointment booking
```

### 3. Run the backend

```bash
export PYTHONPATH=$(pwd)
python app/main.py
# → http://localhost:7860
```

### 4. Run the frontend

```bash
cd client
npm install
npm run dev
# → http://localhost:5173
```

Open `http://localhost:5173`, select an agent, and start talking.

---

## Configuration

All settings live in `app/config/config.yaml`. Environment variables are injected via `${VAR_NAME}` syntax.

**Key sections:**

```yaml
# STT
stt:
  provider: "deepgram"
  config:
    model: "nova-3"
    language: "en"

# LLM
conversation:
  llm:
    provider: "groq"
    model: "llama-3.1-8b-instant"

# TTS
tts:
  provider: "cartesia"
  config:
    model: "sonic-3"

# Persona system
personas:
  default_persona: "receptionist"
  agents:
    receptionist:
      name: "Brooke"
      voice_id: "${CARTESIA_VOICE_ID}"
      # ... system_prompt_override, greetings, etc.

# VAD
server:
  vad:
    confidence: 0.92
    stop_secs: 1.0

# SmartTurn v3
  smart_turn:
    enabled: true

# Emotion detection
  emotion_detection_enabled: true
```

---

## Emotion Detection

Non-blocking hybrid system — adds zero latency to the voice pipeline:

- **Audio channel**: MSP-PODCAST wav2vec2 model runs in a background async task (70% weight)
- **Text channel**: Google Gemini analyzes LLM response sentiment (30% weight)
- **Fusion**: Weighted combination with 10s emotion TTL and 2-frame stability before voice switch
- **Result**: TTS voice characteristics adjust dynamically based on detected emotion

---

## A2UI (Agentic Visual UI)

Generates visual UI components in real-time from voice queries — no clicks required:

- **3-tier template selection**: explicit keyword → semantic MiniLM similarity → fallback
- **Template types**: contact cards, service grids, timelines, comparison charts, FAQ accordions, team profiles, stats dashboards
- **Streaming**: word-by-word LLM output streamed to frontend via `VisualHintProcessor`

---

## Appointment Booking

Full voice-driven booking flow:

1. Agent offers appointment at farewell (or when user requests it)
2. Collects name and email conversationally
3. Confirms by spelling out email character-by-character
4. Submits to Tally.so via `submit_appointment(first_name, last_name, email)`
5. Ends session with `end_conversation()`

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ws` | WebSocket | Real-time voice communication |
| `/health` | GET | Health check |
| `/status` | GET | Server and service status |
| `/connect` | POST | Get WebSocket URL and session config |

---

## Deployment

### Docker (with HTTPS)

```bash
cd deployment/docker
docker-compose -f docker-compose.https.yml up -d
```

Set your domain in `.env`:
```bash
DOMAIN=yourdomain.com
PUBLIC_URL=https://yourdomain.com
```

Caddy handles SSL certificates automatically.

### Public access via ngrok (for testing)

```bash
# Terminal 1
python app/main.py

# Terminal 2
ngrok http 7860
```

Update `client/public/config.js` with the ngrok URL.

### CI/CD

GitHub Actions deploys to AWS Lightsail on push to `main`. See `.github/workflows/deploy.yml`.

**Infrastructure**: $7/month Lightsail (1GB RAM, 2 vCPU), CPU-only PyTorch, INT8 quantization, 2GB swap.

---

## Running Tests

```bash
pytest tests/                   # All tests
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
```

```bash
cd client
npm run typecheck               # TypeScript type checking
npm run build                   # Production build
```

---

## Known Limitations

- `SmartInterruptionProcessor` is currently disabled (StartFrame bug)
- AIC Speech Enhancement disabled (SDK v1/v2 version mismatch)
- MSP-PODCAST model may fail with newer versions of `transformers` (falls back to text-only emotion)
- INT8 quantization not supported on Apple Silicon (M1/M2/M3) — skipped automatically

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Pipecat](https://github.com/pipecat-ai/pipecat) — Real-time AI voice pipeline framework
- [Deepgram](https://deepgram.com) — Speech-to-text (Nova-3)
- [Groq](https://groq.com) — Ultra-fast LLM inference
- [Cartesia](https://cartesia.ai) — Low-latency neural TTS (Sonic-3)
- [Google Gemini](https://ai.google.dev) — Text sentiment analysis
- [Silero VAD](https://github.com/snakers4/silero-vad) — Voice activity detection
- [Sigma.js](https://sigmajs.org) + [Graphology](https://graphology.github.io) — Knowledge graph visualization
