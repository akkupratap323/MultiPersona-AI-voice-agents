# Project Structure

This document describes the organization of the Nester AI Voice Assistant codebase.

## 📁 Root Directory Structure

```
nester-ai-voice-assistant/
├── app/                      # Main application code
│   ├── core/                # Core orchestration (server, voice assistant)
│   ├── services/            # Service layer (STT, TTS, RAG, emotion detection)
│   ├── processors/          # Stream processors (tone-aware, text filter)
│   └── config/              # Configuration files
│
├── client/                   # Frontend web application
│   ├── src/                 # TypeScript/JavaScript source
│   ├── public/              # Static assets
│   └── dist/                # Built frontend files
│
├── data/                     # Data files
│   ├── nester_labs_knowledge.json  # Knowledge base
│   └── sample_documents.json       # Sample data
│
├── docs/                     # Documentation
│   ├── architecture/        # Architecture & technical docs
│   ├── guides/              # Setup and deployment guides
│   ├── comparisons/         # Technology comparison docs
│   └── PROJECT_STRUCTURE.md # This file
│
├── deployment/              # Deployment configurations
│   ├── docker/             # Docker files
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── Caddyfile
│   ├── aws/                # AWS deployment configs
│   │   ├── cloudformation-template.yaml
│   │   ├── ecs-task-definition-*.json
│   │   └── deploy.sh
│   └── scripts/            # Deployment scripts
│       ├── lightsail-deploy.sh
│       └── lightsail-deploy-https.sh
│
├── scripts/                 # Utility scripts
│   ├── restart_server.sh
│   ├── monitor.sh
│   ├── health-check.sh
│   └── setup-*.sh
│
├── .github/                 # GitHub workflows & CI/CD
│   └── workflows/
│       └── deploy.yml
│
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
├── .gitignore
├── README.md                # Project overview
├── Makefile                 # Build automation
└── requirements.txt         # Python dependencies
```

## 📂 Detailed Structure

### `/app` - Application Code

The main Python application following a layered architecture:

- **`/app/core`**: Core orchestration layer
  - `server.py` - FastAPI server and WebSocket handling
  - `voice_assistant.py` - Main voice assistant orchestrator

- **`/app/services`**: Service layer implementations
  - `stt.py` - Speech-to-Text service
  - `tts.py` - Text-to-Speech service
  - `chatterbox_tts.py` - Chatterbox TTS integration
  - `conversation.py` - LLM conversation manager
  - `rag.py` - RAG (Retrieval-Augmented Generation)
  - `msp_emotion_detector.py` - MSP-PODCAST audio emotion detection
  - `llm_text_sentiment.py` - LLM-based text sentiment detection
  - `hybrid_emotion_detector.py` - Hybrid audio+text emotion fusion
  - `tone_detector.py` - Tone detection and classification
  - `latency.py` - Latency monitoring

- **`/app/processors`**: Stream processing components
  - `tone_aware_processor.py` - Real-time emotion detection & voice adaptation
  - `text_filter_processor.py` - Text filtering and formatting

- **`/app/config`**: Configuration management
  - `config.yaml` - Main configuration file
  - `loader.py` - Configuration loader

### `/client` - Frontend Application

Web-based voice chat interface:

- **`/client/src`**: TypeScript/JavaScript source code
  - `app.ts` - Main application logic
  - `audio.ts` - Audio handling
  - `websocket.ts` - WebSocket communication

- **`/client/public`**: Static assets (HTML, CSS, images)
- **`/client/dist`**: Production build output

### `/data` - Data Files

Knowledge base and sample data:

- `nester_labs_knowledge.json` - Company information for RAG
- `sample_documents.json` - Sample data for testing

### `/docs` - Documentation

Comprehensive project documentation:

- **`/docs/architecture`**: Technical architecture docs
  - `SYSTEM_ARCHITECTURE.md` - Overall system design
  - `EMOTION_VISUALIZATION.md` - Emotion detection architecture
  - `TTFB_ANALYSIS.md` - Time-to-first-byte analysis

- **`/docs/guides`**: Setup and deployment guides
  - `DEPLOYMENT_FIX.md` - Deployment troubleshooting
  - `HYBRID_EMOTION_TESTING.md` - Testing emotion detection
  - `CLEANUP_SUMMARY.md` - Code cleanup notes

- **`/docs/comparisons`**: Technology evaluations
  - `EMOTION_MODELS_COMPARISON.md` - Emotion detection models
  - `STT_SERVICES_COMPARISON.md` - Speech-to-text services

- **`/docs`**: Other documentation
  - `CHATTERBOX_MEDIUM_BLOG.md` - Blog post about Chatterbox TTS
  - Existing deployment docs from `/docs/DEPLOYMENT_*.md`

### `/deployment` - Deployment Configurations

Everything needed to deploy the application:

- **`/deployment/docker`**: Docker containerization
  - `Dockerfile` - Main application container
  - `docker-compose.yml` - Multi-container orchestration
  - `docker-compose.ghcr.yml` - GitHub Container Registry config
  - `Caddyfile` - Reverse proxy configuration

- **`/deployment/aws`**: AWS-specific deployments
  - `cloudformation-template.yaml` - Infrastructure as Code
  - `ecs-task-definition-*.json` - ECS task definitions
  - `docker-compose.prod.yml` - Production Docker config
  - `deploy.sh` - AWS deployment script
  - `ec2-deploy.sh` - EC2 deployment script

- **`/deployment/scripts`**: Deployment automation
  - `lightsail-deploy.sh` - AWS Lightsail deployment
  - `lightsail-deploy-https.sh` - HTTPS Lightsail deployment

### `/scripts` - Utility Scripts

Operational and development scripts:

- **Server Management**:
  - `restart_server.sh` - Restart the voice assistant server
  - `monitor.sh` - Monitor server health (Linux)
  - `monitor-mac.sh` - Monitor server health (macOS)

- **Health & Monitoring**:
  - `health-check.sh` - Server health verification
  - `check-server-logs.sh` - Log inspection
  - `check-deployment-env.sh` - Verify deployment environment

- **AWS Setup**:
  - `setup-parameter-store.sh` - AWS Parameter Store setup
  - `install-cloudwatch-agent.sh` - CloudWatch agent installation
  - `cloudwatch-agent-config.json` - CloudWatch configuration

- **Secret Management**:
  - `fetch-secrets.sh` - Retrieve secrets
  - `fetch-secrets-from-secrets-manager.sh` - AWS Secrets Manager
  - `migrate-to-secrets-manager.sh` - Migrate secrets
  - `add-resemble-secrets.sh` - Add Resemble AI secrets

- **Verification**:
  - `verify-and-fix-code-version.sh` - Code version verification

### `/.github` - GitHub Configuration

CI/CD pipelines and GitHub-specific configuration:

- **`/workflows`**: GitHub Actions workflows
  - `deploy.yml` - Automated deployment pipeline

## 🔧 Configuration Files (Root)

Key configuration files in the root directory:

- **`.env`**: Environment variables (not in version control)
- **`.env.example`**: Template for environment variables
- **`.gitignore`**: Git ignore patterns
- **`.dockerignore`**: Docker ignore patterns
- **`Makefile`**: Build and deployment automation
- **`requirements.txt`**: Python dependencies
- **`README.md`**: Project overview and quick start guide

## 🚀 Key Design Principles

1. **Separation of Concerns**: Clear separation between application logic (`/app`), frontend (`/client`), deployment (`/deployment`), and documentation (`/docs`)

2. **Layered Architecture**:
   - Core orchestration layer
   - Service layer for individual capabilities
   - Processor layer for stream processing

3. **Configuration Management**: Centralized configuration in `/app/config`

4. **Deployment Flexibility**: Multiple deployment options (Docker, AWS ECS, AWS Lightsail, EC2)

5. **Documentation First**: Comprehensive documentation organized by purpose

## 📝 Adding New Components

### Adding a New Service

1. Create service file in `/app/services/your_service.py`
2. Implement service interface
3. Register in voice assistant orchestrator (`/app/core/voice_assistant.py`)
4. Update configuration in `/app/config/config.yaml`

### Adding a New Processor

1. Create processor in `/app/processors/your_processor.py`
2. Extend `FrameProcessor` from Pipecat
3. Add to pipeline in voice assistant
4. Document in `/docs/architecture/`

### Adding Documentation

1. Architecture docs → `/docs/architecture/`
2. Setup/deployment guides → `/docs/guides/`
3. Comparisons/evaluations → `/docs/comparisons/`
4. Update this file to reference new docs

### Adding Deployment Config

1. Docker configs → `/deployment/docker/`
2. AWS configs → `/deployment/aws/`
3. Deployment scripts → `/deployment/scripts/`
4. Update `/docs/guides/` with new deployment instructions

## 🔗 Related Documentation

- [README.md](../README.md) - Project overview and quick start
- [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md) - Detailed architecture
- [Deployment Guides](guides/) - Deployment instructions
- [AWS Setup](DEPLOYMENT_OVERVIEW.md) - AWS deployment overview

## 📊 Project Statistics

- **Languages**: Python (backend), TypeScript/JavaScript (frontend)
- **Frameworks**: FastAPI, Pipecat, React-like vanilla JS
- **Architecture**: Microservices-oriented, event-driven streaming
- **Deployment**: Docker, AWS ECS/Lightsail, GitHub Actions CI/CD
