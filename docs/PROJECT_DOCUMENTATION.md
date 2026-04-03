# NesterConversationalBot - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [What is Pipecat?](#what-is-pipecat)
3. [Architecture Overview](#architecture-overview)
4. [Directory Structure](#directory-structure)
5. [File-by-File Documentation](#file-by-file-documentation)
6. [Pipecat Integration Details](#pipecat-integration-details)
7. [Configuration Guide](#configuration-guide)
8. [Data Flow](#data-flow)
9. [Dependencies](#dependencies)

---

## Project Overview

**NesterConversationalBot** is an open-source voice conversational AI assistant developed by NesterLabs. It combines real-time:
- **Speech-to-Text (STT)** - Deepgram and Whisper support
- **Text-to-Speech (TTS)** - ElevenLabs and Cartesia integration
- **Retrieval-Augmented Generation (RAG)** - Knowledge base retrieval
- **Large Language Model (LLM)** - Google AI integration

### Key Features
- Real-time voice conversation via WebSocket
- Ultra-low latency (1-1.5 seconds response time)
- Native Hinglish (Hindi-English mix) support
- Performance monitoring and latency analysis
- Flexible deployment (FastAPI or standalone WebSocket server)

---

## What is Pipecat?

**Pipecat** is an open-source framework for building real-time voice and multimodal AI applications. It provides:

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Pipeline** | A chain of processors that data flows through sequentially |
| **Frame** | A unit of data (audio, text, transcription) that moves through the pipeline |
| **Transport** | Handles input/output communication (WebSocket, WebRTC, Daily) |
| **Service** | Wrapper around AI providers (STT, TTS, LLM) |
| **FrameProcessor** | Base class for custom processing logic |

### Why Pipecat?
- **Real-time streaming**: Audio/video processing with minimal latency
- **Provider agnostic**: Easy switching between AI service providers
- **Extensible**: Custom processors can be added to the pipeline
- **Built-in VAD**: Voice Activity Detection for natural conversations

### Pipecat Components Used in This Project

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPECAT FRAMEWORK                        │
├─────────────────────────────────────────────────────────────┤
│  Transport Layer                                            │
│  ├── WebsocketServerTransport (WebSocket communication)     │
│  ├── ProtobufFrameSerializer (frame serialization)          │
│  └── SileroVADAnalyzer (voice activity detection)           │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                              │
│  ├── DeepgramSTTService / WhisperSTTService (speech-to-text)│
│  ├── ElevenLabsTTSService / CartesiaTTSService (text-to-speech)│
│  └── GoogleLLMService (language model)                      │
├─────────────────────────────────────────────────────────────┤
│  Pipeline Components                                        │
│  ├── Pipeline (chains processors together)                  │
│  ├── PipelineTask (manages execution)                       │
│  ├── PipelineRunner (runs with signal handling)             │
│  └── FrameProcessor (custom processing base class)          │
├─────────────────────────────────────────────────────────────┤
│  Context & Tools                                            │
│  ├── OpenAILLMContext (conversation context)                │
│  ├── FunctionSchema / ToolsSchema (LLM function calling)    │
│  └── RTVIProcessor / RTVIObserver (real-time interaction)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Web Client                            │
│                   (TypeScript/RTVI)                         │
│                   client/src/app.ts                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket Connection
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server                                 │
│              src/websocket_server.py                        │
│  ├── POST /connect → Returns WebSocket URL                  │
│  ├── GET /ws → WebSocket endpoint                           │
│  └── GET /status → Service status                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         Pipecat Transport Layer                             │
│         src/voice_assistant_server.py                       │
│  ├── WebsocketServerTransport                               │
│  ├── SileroVADAnalyzer (Voice Activity Detection)           │
│  └── ProtobufFrameSerializer                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│          Voice Assistant Orchestrator                       │
│          src/core/voice_assistant.py                        │
│  ├── Initializes all services                               │
│  ├── Creates Pipecat pipeline                               │
│  └── Manages conversation flow                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  PIPECAT PIPELINE                           │
│                                                             │
│  Transport Input                                            │
│       ↓                                                     │
│  STT Service (Deepgram/Whisper)                             │
│       ↓                                                     │
│  Context Aggregator (user messages)                         │
│       ↓                                                     │
│  RTVI Processor                                             │
│       ↓                                                     │
│  LLM Service (Google) ←→ RAG Service (knowledge retrieval)  │
│       ↓                                                     │
│  TTS Service (ElevenLabs/Cartesia)                          │
│       ↓                                                     │
│  Latency Analyzer                                           │
│       ↓                                                     │
│  Transport Output                                           │
│       ↓                                                     │
│  Context Aggregator (assistant messages)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
NesterConversationalBot/
├── src/                          # Python backend
│   ├── __init__.py
│   ├── websocket_server.py       # FastAPI server entry point
│   ├── voice_assistant_server.py # WebSocket transport wrapper
│   │
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── config.py             # Config loader with env substitution
│   │   └── config.yaml           # YAML configuration file
│   │
│   ├── core/                     # Core orchestration
│   │   ├── __init__.py
│   │   └── voice_assistant.py    # Main Voice Assistant class
│   │
│   └── services/                 # Service modules
│       ├── __init__.py
│       ├── conversation_manager.py  # LLM orchestration
│       ├── input_analyzer.py        # Input classification
│       ├── latency_analyzer.py      # Performance tracking
│       ├── rag_service.py           # Knowledge retrieval
│       ├── speech_to_text.py        # STT abstraction
│       └── text_to_speech.py        # TTS abstraction
│
├── client/                       # TypeScript frontend
│   ├── src/
│   │   └── app.ts                # RTVI client implementation
│   ├── package.json              # Node dependencies
│   ├── tsconfig.json             # TypeScript config
│   └── README.md                 # Client documentation
│
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables template
└── README.md                     # Main documentation
```

---

## File-by-File Documentation

### Server Entry Points

#### `src/websocket_server.py`
**Purpose:** Main server entry point with FastAPI HTTP and WebSocket endpoints

| Function | Description |
|----------|-------------|
| `websocket_endpoint()` | Handles WebSocket connections at `/ws` |
| `bot_connect()` | POST `/connect` - Returns WebSocket URL based on server mode |
| `get_status()` | GET `/status` - Returns server and service status |
| `main()` | Orchestrates startup of FastAPI and optional WebSocket servers |
| `load_config()` | Loads configuration from config.yaml |

**Pipecat Usage:**
- Uses `VoiceAssistant` for conversation handling
- Uses `VoiceAssistantServer` for WebSocket transport

**Server Modes:**
- `fast_api` (default): HTTP API + WebSocket at port 7860
- `websocket`: Standalone WebSocket server at port 8765

---

#### `src/voice_assistant_server.py`
**Purpose:** Manages WebSocket transport configuration and server initialization

| Method | Description |
|--------|-------------|
| `__init__()` | Initializes server with config |
| `_apply_server_defaults()` | Applies default configurations from environment |
| `create_websocket_transport()` | Creates WebSocket transport with Silero VAD |
| `run_websocket_server()` | Runs standalone WebSocket server |
| `setup_websocket_transport_handlers()` | Sets up client connection/disconnection handlers |
| `get_server_status()` | Returns server and voice assistant status |

**Pipecat Components:**
- `WebsocketServerTransport` - Handles WebSocket communication
- `SileroVADAnalyzer` - Voice Activity Detection
- `ProtobufFrameSerializer` - Frame serialization

**Configuration Parameters:**
- Host/port settings
- Audio input/output settings (16kHz, 1 channel)
- Session timeout (default 180 seconds)
- VAD configuration

---

### Core Orchestration

#### `src/core/voice_assistant.py`
**Purpose:** Central orchestrator that coordinates all services and manages the Pipecat pipeline

| Method | Description |
|--------|-------------|
| `initialize_services()` | Initializes STT, TTS, RAG, conversation manager, latency analyzer |
| `create_pipeline()` | Builds the Pipecat processing pipeline |
| `create_task()` | Creates PipelineTask with metrics enabled |
| `setup_transport_handlers()` | Sets up WebSocket transport event handlers |
| `run()` | Main execution method |
| `get_service_status()` | Returns status of all services |
| `get_latency_statistics()` | Returns performance metrics |

**Pipeline Architecture:**
```
Transport Input
  → STT (Speech-to-Text)
  → Context Aggregator (user)
  → RTVI Processor
  → LLM (Conversation)
  → TTS (Text-to-Speech)
  → Latency Analyzer
  → Transport Output
  → Context Aggregator (assistant)
```

**Pipecat Components:**
- `Pipeline` - Chains processors
- `PipelineRunner` - Executes pipeline
- `PipelineTask` - Manages execution with params
- `RTVIProcessor/RTVIObserver` - Real-time voice interaction

---

### Configuration

#### `src/config/config.py`
**Purpose:** Loads YAML configuration with environment variable substitution

| Function | Description |
|----------|-------------|
| `_substitute_env_vars()` | Replaces `${VARIABLE_NAME}` with environment values |
| `load_config_from_yaml()` | Loads config.yaml and performs substitution |
| `get_assistant_config()` | Loads and validates required API keys |

**Key Feature:** All sensitive data (API keys) loaded from `.env` file

---

#### `src/config/config.yaml`
**Purpose:** Main configuration file

| Section | Description |
|---------|-------------|
| `language` | Primary language, Hinglish support, auto-detection |
| `stt` | STT provider config (Deepgram), model, language |
| `tts` | TTS provider config (ElevenLabs), voice IDs |
| `rag` | RAG system type and configuration |
| `conversation` | LLM API key configuration |
| `input_analyzer` | Custom greeting/feedback patterns |
| `server` | Default host/port values |

---

### Services

#### `src/services/speech_to_text.py`
**Purpose:** Abstraction layer for speech-to-text providers

| Class/Method | Description |
|--------------|-------------|
| `TextNormalizedDeepgramSTTService` | Custom Deepgram with Unicode normalization for Hinglish |
| `SpeechToTextService.initialize()` | Creates STT service based on provider |
| `SpeechToTextService.get_service()` | Returns initialized STT service |
| `SpeechToTextService.update_config()` | Updates and reinitializes |

**Supported Providers:**
- **Whisper** - Offline STT with device selection (cpu/gpu)
- **Deepgram** - Cloud-based with language detection and Hinglish support

**Pipecat Services:** `WhisperSTTService`, `DeepgramSTTService`

---

#### `src/services/text_to_speech.py`
**Purpose:** Abstraction layer for text-to-speech providers

| Method | Description |
|--------|-------------|
| `initialize()` | Creates TTS service based on provider |
| `get_service()` | Returns initialized TTS service |
| `speak_text()` | Converts text to speech and queues for playback |
| `get_voice_settings()` | Returns voice configuration |

**Supported Providers:**
- **ElevenLabs** - Cloud-based with multilingual support
- **Cartesia** - Alternative voice synthesis

**Language Support:** Voice switching based on language (English/Hindi/Hinglish)

**Pipecat Services:** `ElevenLabsTTSService`, `CartesiaTTSService`

---

#### `src/services/conversation_manager.py`
**Purpose:** Manages LLM interactions, conversation flow, and function handling

| Method | Description |
|--------|-------------|
| `initialize_llm()` | Sets up Google LLM and registers function handlers |
| `set_tts_service()` | Links TTS for function call feedback |
| `_handle_rag_call()` | Processes RAG function calls |
| `create_function_schemas()` | Defines available functions for LLM |
| `create_context()` | Creates LLM context with system message and tools |
| `create_context_aggregator()` | Creates message aggregator |
| `get_conversation_stats()` | Returns conversation status |

**Function Registration:**
- `call_rag_system` - LLM calls this to search knowledge base

**Pipecat Components:**
- `GoogleLLMService` - LLM provider
- `OpenAILLMContext` - Message and tool schema management
- `FunctionSchema` / `ToolsSchema` - Function definitions

---

#### `src/services/rag_service.py`
**Purpose:** Knowledge base retrieval for question answering

| Method | Description |
|--------|-------------|
| `get_response()` | Async method to get response to user question |
| `_search_knowledge_base()` | Keyword matching against knowledge base |
| `get_status()` | Returns service status |

**Current Implementation:** Simple keyword-based matching (demo/mock)

**Built-in Topics:** President, LLM concepts, AI, Python, Climate Change

**Extension Points:**
- Replace with vector database (Pinecone, Weaviate)
- Integrate semantic search
- Support dynamic knowledge base updates

---

#### `src/services/input_analyzer.py`
**Purpose:** Analyzes user input to determine processing type

| Method | Description |
|--------|-------------|
| `is_greeting_or_feedback()` | Pattern matching for greetings/feedback |
| `analyze_input()` | Classifies input as conversation or RAG-needing |
| `get_input_type_details()` | Detailed analysis with confidence scores |
| `add_custom_pattern()` | Dynamically add new patterns |

**Processing Types:**
- `"normal_conversation"` - Greetings, feedback, polite responses → LLM responds directly
- `"needs_rag"` - Complex questions → LLM calls RAG system

---

#### `src/services/latency_analyzer.py`
**Purpose:** Comprehensive latency tracking throughout the voice pipeline

| Method | Description |
|--------|-------------|
| `process_frame()` | Tracks timestamps for each frame type |
| `_complete_interaction()` | Finalizes metrics for completed interaction |
| `_update_statistics()` | Calculates aggregate statistics |
| `get_statistics()` | Returns metrics and recent interactions |
| `log_summary_report()` | Comprehensive analysis report |

**Metrics Tracked:**
- STT latency (speech-to-text processing time)
- LLM latency (language model inference time)
- TTS latency (text-to-speech generation time)
- Total latency (end-to-end processing time)
- Voice-to-voice latency (transcription to audio output)

**Statistical Analysis:** min, max, mean, p95, p99 percentiles

**Pipecat Integration:** Extends `FrameProcessor` to intercept all pipeline frames

---

### Client

#### `client/src/app.ts`
**Purpose:** TypeScript/HTML client for browser-based voice chat

| Method | Description |
|--------|-------------|
| `connect()` | Establishes connection to bot server |
| `disconnect()` | Gracefully closes connection |
| `setupMediaTracks()` | Configures audio tracks |
| `setupAudioTrack()` | Sets up audio playback |
| `updateConnectionVisuals()` | Updates UI based on connection state |

**Features:**
- RTVI (Real-Time Voice Interaction) client
- WebSocket-based connection
- Microphone input and speaker output
- Real-time transcription display

**Configuration:**
- Base URL: `http://localhost:7860`
- Endpoints: `/connect` for WebSocket URL discovery
- Transport: WebSocket
- Enables microphone, disables camera

**Pipecat Client Libraries:**
- `RTVIClient` - Main client for RTVI protocol
- `WebSocketTransport` - WebSocket communication

---

## Pipecat Integration Details

### Frame Types in the Pipeline

| Frame Type | Stage | Description |
|------------|-------|-------------|
| `AudioRawFrame` | Input | Raw audio from user microphone |
| `TranscriptionFrame` | STT | Transcribed text from speech |
| `TextFrame` | LLM | Generated response text |
| `TTSStartedFrame` | TTS | TTS processing started |
| `TTSAudioRawFrame` | TTS | Synthesized audio chunks |
| `AudioRawFrame` | Output | Audio sent to user speaker |

### Pipeline Flow

```
User Speaks
    ↓
┌─────────────────────────────────────────────────────────┐
│ Transport Input (WebsocketServerTransport)              │
│   - Receives audio via WebSocket                        │
│   - VAD detects speech boundaries                       │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ STT Service (DeepgramSTTService)                        │
│   - Converts audio to text                              │
│   - Emits TranscriptionFrame                            │
│   - Latency tracked: STT_LATENCY                        │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Context Aggregator (User)                               │
│   - Collects user messages                              │
│   - Builds conversation history                         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ RTVI Processor                                          │
│   - Real-time interaction monitoring                    │
│   - Emits events for client                             │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ LLM Service (GoogleLLMService)                          │
│   - Processes conversation context                      │
│   - May call RAG function for knowledge retrieval       │
│   - Emits TextFrame with response                       │
│   - Latency tracked: LLM_LATENCY                        │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ TTS Service (ElevenLabsTTSService)                      │
│   - Converts text to speech                             │
│   - Emits TTSAudioRawFrame                              │
│   - Latency tracked: TTS_LATENCY                        │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Latency Analyzer                                        │
│   - Tracks all latency metrics                          │
│   - Calculates statistics                               │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ Transport Output (WebsocketServerTransport)             │
│   - Sends audio via WebSocket                           │
│   - Client plays through speaker                        │
└─────────────────────────────────────────────────────────┘
    ↓
User Hears Response
```

---

## Configuration Guide

### Required Environment Variables

Create a `.env` file based on `env.example`:

```bash
# STT Configuration (Required)
DEEPGRAM_API_KEY=your_deepgram_api_key

# TTS Configuration (Required)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_HINGLISH_VOICE_ID=optional_hinglish_voice_id

# LLM Configuration (Required)
GOOGLE_API_KEY=your_google_api_key

# Server Configuration (Optional)
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=7860
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765
WEBSOCKET_SERVER=fast_api

# Other Settings (Optional)
SESSION_TIMEOUT=180
LOG_LEVEL=INFO
```

### Getting API Keys

| Service | Where to Get |
|---------|--------------|
| Deepgram | https://console.deepgram.com/ |
| ElevenLabs | https://elevenlabs.io/app/settings/api-keys |
| Google AI | https://aistudio.google.com/app/apikey |

---

## Data Flow

### Complete Conversation Flow

1. **User Speech Input**
   - Client captures microphone audio
   - Audio sent via WebSocket to server
   - VAD detects speech start/end

2. **Speech-to-Text**
   - Deepgram/Whisper converts audio to text
   - Unicode normalization for Hinglish
   - Emits `TranscriptionFrame`

3. **Input Analysis**
   - Input analyzer classifies the input
   - Greeting/feedback → direct LLM response
   - Complex question → RAG retrieval

4. **LLM Processing**
   - LLM receives conversation context
   - May call `call_rag_system` function
   - Generates response with or without RAG data

5. **RAG Retrieval (if needed)**
   - Searches knowledge base
   - Returns relevant information
   - LLM incorporates into response

6. **Text-to-Speech**
   - ElevenLabs/Cartesia synthesizes speech
   - Appropriate voice selected for language
   - Audio frames generated

7. **Output to Client**
   - Audio sent via WebSocket
   - Client plays through speaker
   - Latency metrics calculated

---

## Dependencies

### Python Backend (`requirements.txt`)

| Package | Purpose |
|---------|---------|
| `fastapi~=0.115.14` | HTTP/WebSocket framework |
| `uvicorn~=0.35.0` | ASGI server |
| `python-dotenv~=1.1.1` | Environment variable loading |
| `PyYAML~=6.0.2` | YAML configuration parsing |
| `loguru~=0.7.3` | Structured logging |
| `pipecat-ai[...]` | Pipecat framework with providers |
| `pipecat-ai-small-webrtc-prebuilt` | WebRTC support |

### Pipecat Extras Installed
- `webrtc` - WebRTC transport support
- `daily` - Daily.co integration
- `deepgram` - Deepgram STT service
- `cartesia` - Cartesia TTS service
- `whisper` - Whisper STT service
- `silero` - Silero VAD
- `websocket` - WebSocket transport
- `google` - Google LLM service

### Client (`client/package.json`)

| Package | Purpose |
|---------|---------|
| `@pipecat-ai/client-js` | RTVI client library |
| `@pipecat-ai/websocket-transport` | WebSocket transport |
| `protobufjs` | Protocol buffer support |
| `vite` | Build tool |
| `typescript` | TypeScript compiler |

---

## Quick Start

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/nesterlabs-ai/NesterConversationalBot.git
cd NesterConversationalBot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys

# Run the server
python -m src.websocket_server
```

### Client Setup

```bash
cd client

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access
- Server: http://localhost:7860
- Client: http://localhost:5173 (or Vite's default port)
- WebSocket: ws://localhost:7860/ws

---

## Extension Points

| Component | How to Extend |
|-----------|---------------|
| STT Provider | Add new provider in `speech_to_text.py` |
| TTS Provider | Add new provider in `text_to_speech.py` |
| RAG System | Replace mock in `rag_service.py` with vector DB |
| LLM Functions | Register new functions in `conversation_manager.py` |
| Input Patterns | Add patterns in `input_analyzer.py` or config |
| Metrics | Extend `latency_analyzer.py` |
| Pipeline | Modify stages in `voice_assistant.py` |

---

*Documentation generated for NesterConversationalBot v1.0*
