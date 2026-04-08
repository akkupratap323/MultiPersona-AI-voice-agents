# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PersonaAI** is a production-ready, real-time voice conversational assistant built using the Pipecat framework (v0.0.98). It combines STT, LLM, TTS, RAG, emotion detection, and dynamic visual UI generation (A2UI) into a streaming voice pipeline with a 1-1.5 second end-to-end latency target.

## Build & Run Commands

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Add API keys
export PYTHONPATH=$(pwd)
python app/main.py             # http://localhost:7860

# Frontend
cd client && npm install
npm run dev                    # http://localhost:5173
npm run build                  # Production build
npm run typecheck              # TypeScript type checking

# Tests
pytest tests/                  # All tests
pytest tests/unit/             # Unit tests only
pytest tests/integration/      # Integration tests only
pytest tests/unit/test_input_analyzer.py  # Single test file

# Docker deployment
cd deployment/docker && docker-compose -f docker-compose.https.yml up -d
```

## Architecture

```
Web Client (TypeScript/Vite + React)
    ↓ WebSocket (/ws)
FastAPI (app/main.py) + Pipecat Pipeline
    ↓
├─ STT: Deepgram Nova-3
├─ LLM: Groq Llama-3.3-70b (via GroqLLMService wrapper)
├─ TTS: ElevenLabs Turbo v2.5
├─ RAG: LightRAG (external server, X-API-Key auth)
├─ Emotion: MSP-PODCAST wav2vec2 (70%) + Gemini text (30%)
├─ SmartTurn v3: ONNX ML end-of-turn detection
└─ A2UI: Dynamic visual UI from voice queries
```

## Voice Pipeline Flow

This is the core processing chain assembled in `app/core/voice_assistant.py`. Understanding this flow is essential:

```
Audio Input → [Noise Suppression (if enabled)] → [Silero VAD]
    → [Deepgram STT] → [SmartInterruptionProcessor (if enabled)]
    → [ToneAwareProcessor] → [STTMuteFilter]
    → [LLM Context Aggregator + SmartTurn v3]
    → [LLM (Groq)] → [call_rag_system() / end_conversation()]
    → [VisualHintProcessor] → [TextFilterProcessor]
    → [TTS (ElevenLabs)] → Audio Output
```

Key processors in `app/processors/`:
- **SmartInterruptionProcessor**: Context-aware barge-in validation (currently disabled due to StartFrame bug)
- **ToneAwareProcessor**: Non-blocking hybrid emotion detection, adjusts TTS voice tone
- **STTMuteFilter**: Mutes STT during initial bot greeting only (prevents self-interruption)
- **TextFilterProcessor**: Strips markdown before sending to TTS
- **VisualHintProcessor**: Word-by-word streaming of LLM output to frontend for A2UI

## Configuration System

**Load order:** `.env` → `app/config/config.yaml` (with `${VAR}` substitution via `app/config/loader.py`) → env overrides

The system prompt lives in `config.yaml` under `conversation.system_prompt`. Identity enforcement is prepended in `app/services/conversation.py:create_context()`.

Required env vars: `DEEPGRAM_API_KEY`, `GROQ_API_KEY`, `GOOGLE_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `LIGHTRAG_API_KEY`, `LIGHTRAG_BASE_URL`

## Key Architectural Patterns

### Session Management
Each WebSocket connection creates a fresh `VoiceAssistant` instance (`app/core/server.py`). The `ConnectionManager` limits concurrent sessions (max 20). Sessions are fully isolated.

### LLM Context System (Pipecat 0.0.98)
Uses universal `LLMContext` (not deprecated `OpenAILLMContext`). `LLMContextAggregatorPair` manages user/assistant message aggregation. `GroqLLMService` (`app/services/groq_llm_service.py`) wraps the standard service to merge consecutive user messages (prevents Groq API errors).

### Function Calling
Two functions registered on the LLM service in `app/services/conversation.py`:
- `call_rag_system(question)`: Queries LightRAG, returns text + optional A2UI template
- `end_conversation()`: Sends farewell TTS, waits 3.5s, then sends EndFrame

During function calls, a cycling "thinking phrase" plays via TTS (20 natural phrases like "Hmm, let me check that").

### RAG + A2UI Integration
`app/services/rag.py` handles LightRAG queries (streaming via `/query/stream`, non-streaming via `/query`). When A2UI is enabled, `app/services/a2ui/a2ui_rag_service.py` wraps RAG calls to also select and populate visual templates. Template selection uses a 3-tier system in `app/services/a2ui/orchestrator.py`: explicit keyword match → semantic (MiniLM) → fallback.

### Emotion Detection
Non-blocking hybrid system in `app/processors/tone_aware_processor.py`. Audio emotion runs in background async tasks via `app/services/msp_emotion_detector.py` (wav2vec2 model). Text sentiment via `app/services/llm_text_sentiment.py` (Google Gemini). 70/30 weighted fusion. Emotions have 10s TTL, require 2-frame stability before voice switch.

### Interruption Handling
Multi-layer: Silero VAD (conf=0.7) → SmartInterruptionProcessor (disabled) → STTMuteFilter (greeting only) → MinWordsInterruptionStrategy (min_words=0 = immediate). Client-side echo cancellation prevents self-interruption.

## Frontend

TypeScript/Vite app using `@pipecat-ai/client-js` and `@pipecat-ai/websocket-transport` for real-time audio. Knowledge graph visualization uses Sigma.js + Graphology (`client/src/components/KnowledgeGraphWidget/`). A2UI renderers in `client/src/components/a2ui/`. Runtime config in `client/public/config.js` (overwritten by docker-entrypoint.sh in production).

## Deployment

AWS Lightsail ($7/month: 1GB RAM, 2 vCPU). Docker + Caddy (auto HTTPS). CI/CD: GitHub Actions (`.github/workflows/deploy.yml`) → GHCR → SSH deploy. CPU-only PyTorch with 2GB swap. INT8 quantization for MSP-PODCAST model (skipped on Apple Silicon).

## Key Design Decisions

1. **CPU-only PyTorch** - Fits 4GB RAM constraint on Lightsail
2. **Silero VAD over Deepgram VAD** - Local control, Deepgram VAD caused false interruptions
3. **SmartTurn v3 ML** - ONNX end-of-turn detection replaces simple silence-based
4. **Non-blocking emotion** - Background async tasks add zero pipeline latency
5. **GroqLLMService wrapper** - Merges consecutive user messages to prevent Groq API errors
6. **Connection pooling** - Shared httpx client for LightRAG queries
7. **Immediate barge-in** (min_words=0) - Any speech stops TTS instantly

## Known Issues

- SmartInterruptionProcessor disabled (StartFrame error needs fix)
- AIC Speech Enhancement disabled (SDK v1/v2 mismatch)
- MSP-PODCAST model may fail with newer transformers (falls back to text-only)
- INT8 quantization not supported on Apple Silicon (M1/M2/M3)
- Koala noise suppression requires API key; WebRTC used as free fallback
