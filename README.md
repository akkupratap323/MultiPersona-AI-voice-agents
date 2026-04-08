# PersonaAI

**Production-ready real-time voice AI with multi-agent personas, hybrid emotion detection, live agent transfer, and dynamic visual UI — all in 1–1.5 second end-to-end latency.**

🔗 **Live Demo:** [https://3.6.92.112.nip.io/](https://3.6.92.112.nip.io/)

---

## Screenshots

<div align="center">
  <img src="docs/images/screenshot1.png" width="85%"/>
  <br/><br/>
  <img src="docs/images/screenshot2.png" width="85%"/>
</div>

---

## What Is This?

PersonaAI is a full-stack voice conversational assistant built on the [Pipecat](https://github.com/pipecat-ai/pipecat) framework (v0.0.98). You speak — the AI listens, understands your emotion, thinks, responds with the right voice, and optionally renders a live visual UI card — all in real time.

It supports **6 distinct AI agent personas**, each with their own voice, personality, and domain expertise. Agents are aware of each other and can **transfer mid-call** — the old agent says a connecting line, the new agent picks up with full context of your conversation.

---

## Core Features

### 6 Expert AI Agents (Fully Interconnected)

Every agent knows every other agent and can transfer you mid-call. Voice changes instantly. The new agent receives context of what you were discussing and picks up naturally — no awkward restarts.

| Agent | Role | Specialty | Language |
|-------|------|-----------|----------|
| **Brooke** | General Assistant | Knows a bit about everything, connects you to the right person | English |
| **Blake** | Problem Solver | Troubleshooting — tech issues, broken workflows, stuck decisions | English |
| **Arushi** | Hinglish All-Rounder | Warm desi assistant — science to Bollywood, all in Hinglish | Hinglish |
| **Morgan** | Business Strategist | Strategy, sales, fundraising, go-to-market, negotiation | English |
| **Daniel** | Tech Expert | Coding, AI/ML, distributed systems, cloud infra, voice AI | English |
| **Naya** | Lifestyle Coach | Health, fitness, travel, food, self-improvement, relationships | English |

**How live agent transfer works:**
1. Any agent can call `transfer_to_agent()` mid-conversation
2. The old agent speaks a brief handoff line: *"Let me connect you with Daniel — this is his territory."*
3. The LLM system prompt swaps silently to the new agent's persona
4. TTS voice switches in real time via `tts.set_voice(voice_id)` — no reconnect, no reload
5. The orb color, avatar, and UI accent all update on the frontend instantly
6. The new agent picks up with full context: *"Brooke filled me in — you were asking about distributed caching, right?"*

---

### Hybrid Emotion Detection (Original Research)

The core research contribution of this project: a **two-channel, weighted fusion emotion detection system** that runs non-blocking in the background — adding zero latency to the voice pipeline.

#### Architecture

```
Audio Frames ──► MSP-PODCAST wav2vec2 ──► arousal, dominance, valence
                    (70% weight)
                                         \
                                          ──► Weighted Fusion ──► Emotion Label ──► Voice Switch
                                         /
Text Transcription ──► Google Gemini ──► text sentiment
                         (30% weight)
```

#### Channel 1: Audio Emotion (MSP-PODCAST wav2vec2)

- **Model:** `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim`
- **Training data:** MSP-Podcast v1.7 — real podcast conversations (not acted speech)
- **Output:** Dimensional emotions — arousal (0–1), dominance (0–1), valence (0–1)
- **Why dimensional?** Categorical models (happy/sad/angry) trained on acted datasets fail on natural conversational speech. Dimensional models trained on real conversations generalize far better to real-world prosody.
- **Optimizations for 4GB RAM / 2 vCPU Lightsail:**
  - INT8 dynamic quantization → 2–3x faster inference, 75% smaller model footprint
  - Thread tuning: 2 threads matches vCPU count, prevents CPU thrashing
  - Intel MKL-DNN enabled for Lightsail's Intel Xeon CPUs
  - Periodic GC to prevent memory fragmentation on long sessions

#### Channel 2: Text Sentiment (Google Gemini Flash)

- **Model:** Gemini 2.0 Flash via Google AI API
- **Input:** Raw transcription text
- **Output:** Sentiment label + confidence score
- **Role:** Catches masked emotion — someone saying "I'm fine" in a frustrated voice. Audio captures the frustration; text captures the literal words. Fusion resolves the conflict.

#### Fusion Logic

```
final_emotion = (audio_result × 0.7) + (text_result × 0.3)
```

Dynamic weight adjustment when confidence is low. Mismatch detection threshold at 0.8 — when audio and text strongly disagree (potential sarcasm), both signals are flagged and the system uses a conservative fallback.

#### Dimensional → Voice Tone Mapping

| Arousal | Valence | Mapped Tone |
|---------|---------|-------------|
| High | Low (negative) | frustrated |
| High | High (positive) | excited |
| Low | Low (negative) | sad |
| Low | High (positive) | neutral / calm |

#### Stability System

- Emotions require **2-frame stability** before triggering a voice switch (prevents jitter from transient readings)
- Detected emotions have a **10-second TTL** — stale readings don't persist across long silences
- Voice switching is non-blocking: background async tasks, pipeline never waits for emotion inference

---

### Voice Pipeline (Pipecat)

```
Mic Input
  │
  ▼
[Silero VAD] (conf=0.92 — only clear direct speech triggers)
  │
  ▼
[Deepgram Nova-3 STT] (streaming, 300ms endpointing for SmartTurn)
  │
  ▼
[ToneAwareProcessor] ← MSP-PODCAST + Gemini hybrid emotion (background async)
  │
  ▼
[STTMuteFilter] (mutes STT during initial greeting — prevents self-interruption)
  │
  ▼
[SmartTurn v3] (ONNX ML end-of-turn detection — replaces silence heuristics)
  │
  ▼
[LLM Context Aggregator + DeepSeek V3]
  │
  ├─► call_rag_system()     → LightRAG → Answer + optional A2UI visual card
  ├─► transfer_to_agent()   → Live agent swap (voice + persona + context)
  └─► end_conversation()    → Farewell TTS + graceful disconnect
  │
  ▼
[VisualHintProcessor] (word-by-word streaming to frontend for A2UI)
  │
  ▼
[TextFilterProcessor] (strips markdown before TTS)
  │
  ▼
[Cartesia Sonic-3 TTS] (word-level timestamps, emotion voice control)
  │
  ▼
Audio Output
```

**Key design decisions:**
- **Silero VAD over Deepgram VAD** — local control; Deepgram VAD caused false interruptions
- **SmartTurn v3 ONNX** — replaces simple silence detection with ML end-of-turn prediction
- **Non-blocking emotion** — background async tasks, zero pipeline latency impact
- **Immediate barge-in** (`min_words=0`) — any speech stops TTS instantly
- **CPU-only PyTorch** — fits 2GB RAM constraint on $12/month Lightsail instance
- **Connection pooling** — shared `httpx` async client for LightRAG queries

---

### A2UI — Voice-Driven Visual Cards

When the LLM answers a query through RAG, it can also trigger a **dynamic visual card** rendered in the frontend — no user action needed. The card appears alongside the voice response.

Template selection uses a 3-tier system:
1. **Explicit keyword match** — fast, pattern-based detection
2. **Semantic match** — MiniLM sentence transformer for fuzzy intent matching
3. **Fallback** — `simple-card` default

Available templates: `simple-card`, `template-grid`, `timeline`, `contact-card`, `comparison-chart`, `stats-flow-layout`, `team-flip-cards`, `service-hover-reveal`, `magazine-hero`, `faq-accordion`, `image-gallery`, `video-gallery`, `sales-dashboard`

---

### RAG (Retrieval-Augmented Generation)

Knowledge queries route through **LightRAG** — a graph-based RAG system that understands entity relationships, not just keyword similarity.

- Streaming response via `/query/stream`
- Non-streaming fallback via `/query`
- Authenticated with `X-API-Key` header
- Connection pooling via shared `httpx` async client

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Voice Pipeline** | Pipecat v0.0.98 |
| **STT** | Deepgram Nova-3 |
| **LLM** | DeepSeek V3 (`deepseek-chat`) |
| **TTS** | Cartesia Sonic-3 (word timestamps + emotion control) |
| **Audio Emotion** | MSP-PODCAST wav2vec2 (`audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim`) |
| **Text Sentiment** | Google Gemini 2.0 Flash |
| **Fusion** | Custom 70/30 weighted hybrid detector |
| **RAG** | LightRAG (graph-based) |
| **Turn Detection** | SmartTurn v3 ONNX |
| **VAD** | Silero VAD (conf=0.92) |
| **Backend** | FastAPI + uvicorn |
| **Frontend** | TypeScript + Vite |
| **Real-time Transport** | Pipecat RTVI WebSocket |
| **Deployment** | Docker + Caddy (auto-HTTPS) on AWS Lightsail |
| **CI/CD** | GitHub Actions → GHCR → SSH deploy |

---

## Architecture

```
Browser (TypeScript/Vite)
    │
    │  WebSocket (/ws) — Pipecat RTVI Protocol
    │
FastAPI (app/main.py) — port 7860
    │
    ├─ Pipecat Pipeline (per session)
    │   ├─ STT: Deepgram Nova-3
    │   ├─ LLM: DeepSeek V3
    │   ├─ TTS: Cartesia Sonic-3
    │   ├─ Emotion: HybridEmotionDetector (background async)
    │   │   ├─ MSP-PODCAST wav2vec2 (audio channel, 70%)
    │   │   └─ Gemini Flash (text channel, 30%)
    │   ├─ Turn: SmartTurn v3 ONNX
    │   └─ A2UI: VisualHintProcessor → frontend card render
    │
    ├─ Session Management
    │   ├─ ConnectionManager (max 20 concurrent sessions)
    │   ├─ Per-session VoiceAssistant isolation
    │   └─ Live agent transfer (in-session swap, no reconnect)
    │
    └─ External Services
        ├─ LightRAG (graph RAG server)
        ├─ Deepgram (STT streaming API)
        ├─ Cartesia (TTS API)
        └─ Google AI (Gemini text sentiment)
```

---

## Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys: `DEEPGRAM_API_KEY`, `DEEPSEEK_API_KEY`, `CARTESIA_API_KEY`, `CARTESIA_VOICE_ID`, `GOOGLE_API_KEY`, `LIGHTRAG_API_KEY`, `LIGHTRAG_BASE_URL`

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Fill in your API keys
export PYTHONPATH=$(pwd)
python app/main.py             # → http://localhost:7860
```

### Frontend

```bash
cd client
npm install
npm run dev                    # → http://localhost:5173
npm run build                  # Production build
npm run typecheck              # TypeScript type checking
```

### Tests

```bash
pytest tests/                  # All tests
pytest tests/unit/             # Unit tests only
pytest tests/integration/      # Integration tests only
```

---

## Docker Deployment

```bash
cd deployment/docker
docker-compose -f docker-compose.https.yml up -d
```

Caddy handles auto-HTTPS (Let's Encrypt via nip.io). Backend on port 7860, frontend on 80/443.

---

## Configuration

All settings live in `app/config/config.yaml`, loaded at startup with `${ENV_VAR}` substitution from `.env`.

Key sections:

| Section | What it controls |
|---------|-----------------|
| `conversation.system_prompt` | Default agent (Brooke) system prompt |
| `personas.agents` | All 6 agent definitions — voice ID, personality, greetings |
| `server.vad` | VAD confidence and volume thresholds |
| `server.smart_turn` | SmartTurn ONNX timeout and CPU settings |
| `server.emotion_detection_enabled` | Toggle hybrid emotion detection |
| `a2ui` | Template tier mode, confidence threshold, streaming |
| `stt.config` | Deepgram streaming settings, corrections |

---

## Project Structure

```
app/
├── main.py                          # FastAPI entrypoint
├── core/
│   ├── voice_assistant.py           # Pipeline assembly + agent transfer wiring
│   └── server.py                    # WebSocket server + session management
├── services/
│   ├── conversation.py              # LLM context, function calling, agent transfer logic
│   ├── msp_emotion_detector.py      # MSP-PODCAST wav2vec2 audio emotion (INT8 quantized)
│   ├── hybrid_emotion_detector.py   # 70/30 fusion of audio + text sentiment
│   ├── llm_text_sentiment.py        # Google Gemini text sentiment
│   ├── rag.py                       # LightRAG graph RAG integration
│   └── a2ui/                        # Agentic UI — template selection + rendering
├── processors/
│   ├── tone_aware_processor.py      # Emotion detection + Cartesia voice switching
│   ├── smart_interruption.py        # Context-aware barge-in (disabled — StartFrame bug)
│   └── text_filter.py               # Strips markdown before TTS
└── config/
    ├── config.yaml                  # All configuration (env var substitution)
    └── loader.py                    # Config loader with ${VAR} substitution

client/src/
├── app.ts                           # Main app — RTVI client, agent transfer, orb, UI
├── components/
│   ├── EmotionAnalysisWidget/       # Live emotion visualization panel
│   ├── KnowledgeGraphWidget/        # RAG knowledge graph (Sigma.js + Graphology)
│   ├── SynchronizedAnalysisWidget/  # Topic flow analysis
│   └── a2ui/                        # A2UI visual card renderers
└── style.css                        # Agent color theming + transfer animations
```

---

## Known Limitations

- `SmartInterruptionProcessor` disabled — StartFrame ordering bug (fix in progress)
- AIC Speech Enhancement disabled — SDK v1/v2 mismatch
- MSP-PODCAST model falls back to text-only emotion on newer `transformers` versions
- INT8 quantization not supported on Apple Silicon (M1/M2/M3) — skipped automatically
- Koala noise suppression requires paid API key; WebRTC AEC used as free fallback

---

## Deployment

**Live:** [https://3.6.92.112.nip.io/](https://3.6.92.112.nip.io/)  
**Infrastructure:** AWS Lightsail — $12/month (2GB RAM, 2 vCPU, 60GB SSD, 1.5TB transfer)  
**CI/CD:** GitHub Actions → Docker build → push to GHCR → SSH pull + restart  
**HTTPS:** Caddy with automatic Let's Encrypt via nip.io  
**RAM management:** 2GB swap + INT8 quantization for model loading on constrained hardware

---


