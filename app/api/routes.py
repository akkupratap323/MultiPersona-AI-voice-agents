"""
FastAPI routes for the Voice Assistant API.

This module defines the HTTP endpoints for:
- WebSocket connection management
- Health checks and status
- Configuration endpoints
"""

import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from loguru import logger

from app.config.loader import get_assistant_config
from app.services.rag import create_rag_service

try:
    from app.services.a2ui import get_a2ui_rag_service
    A2UI_AVAILABLE = True
except ImportError as e:
    A2UI_AVAILABLE = False
    logger.warning(f"A2UI system not available in routes: {e}")

try:
    from app.services.graph_keywords import get_graph_keyword_extractor
    GRAPH_KEYWORDS_AVAILABLE = True
except ImportError as e:
    GRAPH_KEYWORDS_AVAILABLE = False
    logger.warning(f"Graph keyword extraction not available: {e}")

router = APIRouter(tags=["voice-assistant"])
BASE_DIR = Path(__file__).resolve().parents[2]


def get_server_instance():
    """Get the global server instance (lazy import to avoid circular imports)."""
    from app.core.server import voice_assistant_server
    return voice_assistant_server


@router.post("/connect")
async def connect(request: Request) -> Dict[str, Any]:
    """Get WebSocket connection URL.

    Returns the appropriate WebSocket URL based on server configuration
    and deployment environment (development vs production).
    Accepts optional persona_id in POST body to select agent persona.

    Returns:
        Dict containing the WebSocket URL (with persona_id query param if provided)
    """
    server = get_server_instance()
    server_mode = os.getenv("WEBSOCKET_SERVER", "fast_api")
    public_url = os.getenv("PUBLIC_URL", "")

    # Read persona_id from POST body (sent by RTVI client via requestData)
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    persona_id = body.get("persona_id", "")

    # Check if request came over HTTPS (from reverse proxy headers)
    request_scheme = request.headers.get("X-Forwarded-Proto", "").lower()
    is_https = request_scheme == "https" or (public_url and public_url.startswith("https"))

    if public_url:
        # Production: Use configured public URL
        # Always use wss if public_url is https OR request came over HTTPS (required for browser security)
        ws_scheme = "wss" if (public_url.startswith("https") or is_https) else "ws"
        public_host = public_url.replace("https://", "").replace("http://", "").rstrip("/")
        ws_url = f"{ws_scheme}://{public_host}/ws"
        logger.info(f"Public URL: {public_url}, Request scheme: {request_scheme}, Using WebSocket: {ws_url}")
    elif server_mode == "websocket_server":
        # Development: Standalone WebSocket server
        host = server.server_config.get("websocket_host", "localhost")
        port = server.server_config.get("websocket_port", 8765)
        ws_url = f"ws://{host}:{port}"
    else:
        # Development: FastAPI WebSocket endpoint
        # Always use localhost for client connections (even if server binds to 0.0.0.0)
        host = "localhost"
        port = server.server_config.get("fastapi_port", 7860)
        ws_url = f"ws://{host}:{port}/ws"

    # Append persona_id as query parameter if provided
    if persona_id:
        separator = "&" if "?" in ws_url else "?"
        ws_url = f"{ws_url}{separator}persona_id={persona_id}"
        logger.info(f"Persona selected: {persona_id}")

    logger.info(f"Returning WebSocket URL: {ws_url} (mode: {server_mode})")
    return {"ws_url": ws_url}


@router.get("/personas")
async def get_personas() -> Dict[str, Any]:
    """Get available agent personas for the selection screen.

    Returns persona list with name, role, description, avatar, and tags.
    Voice IDs and system prompts are NOT exposed to the client.
    """
    config = get_assistant_config()
    personas_config = config.get("personas", {})
    agents = personas_config.get("agents", {})
    default_persona = personas_config.get("default_persona", "")

    persona_list = []
    for persona_id, persona in agents.items():
        persona_list.append({
            "id": persona_id,
            "name": persona.get("name", ""),
            "role": persona.get("role", ""),
            "description": persona.get("description", ""),
            "avatar": persona.get("avatar", ""),
            "tags": persona.get("tags", []),
        })

    return {
        "personas": persona_list,
        "default_persona": default_persona,
    }


@router.post("/vad-mode")
async def set_vad_mode(request: Request) -> Dict[str, Any]:
    """Toggle VAD parameters between tight (noise cancellation) and relaxed modes.

    When noise cancellation is ON (tight mode), VAD requires higher confidence
    and volume to trigger — filtering out background noise.
    When OFF (relaxed mode), VAD is more sensitive for responsive detection.

    Request body:
        session_id (str): Active session ID
        mode (str): "tight" or "relaxed"

    Returns:
        Dict with applied VAD parameters
    """
    from app.core.connection_manager import connection_manager
    from pipecat.audio.vad.vad_analyzer import VADParams

    body = await request.json()
    session_id = body.get("session_id", "")
    mode = body.get("mode", "tight")

    if mode not in ("tight", "relaxed"):
        raise HTTPException(status_code=400, detail="mode must be 'tight' or 'relaxed'")

    # If no session_id provided, use the most recent active session
    if not session_id:
        active_ids = connection_manager.get_session_ids()
        if not active_ids:
            raise HTTPException(status_code=404, detail="No active sessions")
        session_id = active_ids[-1]

    vad_analyzer = connection_manager.get_vad_analyzer(session_id)
    if not vad_analyzer:
        raise HTTPException(status_code=404, detail=f"No active session '{session_id}'")

    if mode == "tight":
        new_params = VADParams(
            confidence=0.92,
            start_secs=0.3,
            stop_secs=1.0,
            min_volume=0.80,
        )
    else:
        new_params = VADParams(
            confidence=0.65,
            start_secs=0.15,
            stop_secs=0.6,
            min_volume=0.50,
        )

    vad_analyzer.set_params(new_params)
    logger.info(
        f"[Session {session_id}] 🎚️ VAD mode → {mode}: "
        f"confidence={new_params.confidence}, start={new_params.start_secs}s, "
        f"stop={new_params.stop_secs}s, vol={new_params.min_volume}"
    )

    return {
        "session_id": session_id,
        "mode": mode,
        "params": {
            "confidence": new_params.confidence,
            "start_secs": new_params.start_secs,
            "stop_secs": new_params.stop_secs,
            "min_volume": new_params.min_volume,
        },
    }


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get server and voice assistant status.

    Returns:
        Dict containing server status and configuration
    """
    server = get_server_instance()
    return server.get_server_status()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for load balancers and monitoring.

    Returns:
        Dict with health status
    """
    return {"status": "healthy"}


@router.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information.

    Returns:
        Dict with API information
    """
    return {
        "name": "NesterVoiceAI",
        "version": "1.0.0",
        "description": "Voice Assistant API with RAG capabilities",
        "docs": "/docs",
    }


@router.get("/a2ui/tester", response_class=HTMLResponse)
async def a2ui_tester_page() -> str:
    """Simple HTML page to test A2UI with typed queries."""
    return """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>A2UI Tester</title>
    <link rel="stylesheet" href="/a2ui/styles.css" />
    <style>
      :root { color-scheme: dark; }
      body { font-family: Arial, sans-serif; margin: 0; background: #0b0f14; color: #e6edf3; }
      .tester-root { padding: 24px; }
      .tester-container { max-width: 1200px; margin: 0 auto; }
      .tester-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
      .tester-row { display: grid; grid-template-columns: 1fr; gap: 12px; }
      .tester-card { border: 1px solid #2b3645; border-radius: 10px; padding: 12px; background: #0f172a; }
      .tester-label { font-weight: 600; margin-bottom: 6px; }
      textarea { width: 100%; height: 90px; background: #111827; color: #e6edf3; border: 1px solid #2b3645; border-radius: 8px; padding: 12px; box-sizing: border-box; }
      button { padding: 10px 16px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
      pre { background: #111827; padding: 12px; border-radius: 8px; overflow: auto; max-height: 320px; }
      .a2ui-panel { position: relative; margin-top: 0; width: 100%; }
      .a2ui-panel.visible { display: block; }
      .a2ui-content { width: 100%; overflow: hidden; }
      @media (min-width: 1100px) {
        .tester-grid { grid-template-columns: 1fr 1fr; }
        .tester-row.full { grid-column: 1 / -1; }
      }
    </style>
  </head>
  <body>
    <div class="tester-root">
    <div class="tester-container">
      <h2>A2UI Tester</h2>
      <p>Type a query and get text + A2UI JSON. Cards render below using the same styles as the main UI.</p>
      <div class="tester-row full">
        <textarea id="query" placeholder="Ask a question..."></textarea>
        <div>
          <button onclick="runQuery()">Run Query</button>
        </div>
      </div>
      <div class="tester-grid">
        <div class="tester-row">
          <div class="tester-label">Text Response</div>
          <div class="tester-card"><pre id="text"></pre></div>
        </div>
        <div class="tester-row">
          <div class="tester-label">A2UI JSON</div>
          <div class="tester-card"><pre id="a2ui"></pre></div>
        </div>
        <div class="tester-row full">
          <div class="tester-label">A2UI Live Preview</div>
          <div class="a2ui-panel glass-panel visible tester-card">
            <div class="panel-header">
              <span class="panel-title">VISUAL RESPONSE</span>
              <span class="panel-status" id="a2ui-status">READY</span>
            </div>
            <div class="a2ui-content" id="a2ui-container"></div>
          </div>
        </div>
      </div>
    </div>
    </div>
    <script>
      class A2UIRenderer {
        constructor(containerId) {
          const element = document.getElementById(containerId);
          if (!element) throw new Error('A2UI container not found');
          this.container = element;
        }
        render(doc) {
          if (!doc || !doc.root) return;
          const templateType = doc.root.type;
          const props = doc.root.props || {};
          this.container.innerHTML = '';
          const wrapper = document.createElement('div');
          wrapper.className = 'a2ui-wrapper a2ui-fade-in';
          switch (templateType) {
            case 'simple-card': wrapper.appendChild(this.renderSimpleCard(props)); break;
            case 'template-grid': wrapper.appendChild(this.renderTemplateGrid(props)); break;
            case 'timeline': wrapper.appendChild(this.renderTimeline(props)); break;
            case 'contact-card': wrapper.appendChild(this.renderContactCard(props)); break;
            case 'comparison-chart': wrapper.appendChild(this.renderComparisonChart(props)); break;
            case 'stats-flow-layout': wrapper.appendChild(this.renderStatsFlowLayout(props)); break;
            case 'team-flip-cards': wrapper.appendChild(this.renderTeamFlipCards(props)); break;
            case 'service-hover-reveal': wrapper.appendChild(this.renderServiceHoverReveal(props)); break;
            case 'magazine-hero': wrapper.appendChild(this.renderMagazineHero(props)); break;
            case 'faq-accordion': wrapper.appendChild(this.renderFAQAccordion(props)); break;
            case 'image-gallery': wrapper.appendChild(this.renderImageGallery(props)); break;
            case 'video-gallery': wrapper.appendChild(this.renderVideoGallery(props)); break;
            default: wrapper.appendChild(this.renderFallback(props)); break;
          }
          if (doc._metadata && doc._metadata.tier_name) {
            const badge = document.createElement('div');
            badge.className = 'a2ui-tier-badge';
            badge.textContent = doc._metadata.tier_name;
            wrapper.appendChild(badge);
          }
          this.container.appendChild(wrapper);
        }
        renderSimpleCard(props) {
          const card = document.createElement('div');
          card.className = 'a2ui-simple-card';
          card.innerHTML = `
            <div class="a2ui-card-header">
              ${props.icon ? `<span class="a2ui-icon">${this.getIcon(props.icon)}</span>` : ''}
              <h3 class="a2ui-card-title">${this.escapeHtml(props.title || '')}</h3>
            </div>
            <div class="a2ui-card-content">
              <p>${this.escapeHtml(props.content || '')}</p>
            </div>
          `;
          return card;
        }
        renderTemplateGrid(props) {
          const grid = document.createElement('div');
          grid.className = 'a2ui-template-grid';
          const header = document.createElement('div');
          header.className = 'a2ui-grid-header';
          header.innerHTML = `
            <h3 class="a2ui-grid-title">${this.escapeHtml(props.title || '')}</h3>
            ${props.showCount ? `<span class="a2ui-grid-count">${(props.templates || []).length} items</span>` : ''}
          `;
          grid.appendChild(header);
          const items = document.createElement('div');
          items.className = 'a2ui-grid-items';
          (props.templates || []).forEach((item, idx) => {
            const card = document.createElement('div');
            card.className = 'a2ui-grid-item';
            card.style.animationDelay = `${idx * 0.1}s`;
            card.innerHTML = `
              <div class="a2ui-item-header">
                <h4 class="a2ui-item-name">${this.escapeHtml(item.name || '')}</h4>
                ${item.category ? `<span class="a2ui-item-category">${this.escapeHtml(item.category)}</span>` : ''}
              </div>
              <p class="a2ui-item-description">${this.escapeHtml(item.description || '')}</p>
            `;
            items.appendChild(card);
          });
          grid.appendChild(items);
          return grid;
        }
        renderTimeline(props) {
          const timeline = document.createElement('div');
          timeline.className = 'a2ui-timeline';
          const header = document.createElement('h3');
          header.className = 'a2ui-timeline-title';
          header.textContent = props.title || '';
          timeline.appendChild(header);
          const events = document.createElement('div');
          events.className = 'a2ui-timeline-events';
          (props.events || []).forEach((event, idx) => {
            const item = document.createElement('div');
            item.className = 'a2ui-timeline-event';
            item.style.animationDelay = `${idx * 0.15}s`;
            item.innerHTML = `
              <div class="a2ui-event-marker">
                <span class="a2ui-event-year">${this.escapeHtml(event.year || '')}</span>
              </div>
              <div class="a2ui-event-content">
                <h4 class="a2ui-event-title">${this.escapeHtml(event.title || '')}</h4>
                <p class="a2ui-event-description">${this.escapeHtml(event.description || '')}</p>
              </div>
            `;
            events.appendChild(item);
          });
          timeline.appendChild(events);
          return timeline;
        }
        renderContactCard(props) {
          const card = document.createElement('div');
          card.className = 'a2ui-contact-card';
          const header = document.createElement('h3');
          header.className = 'a2ui-contact-title';
          header.textContent = props.title || '';
          card.appendChild(header);
          const contacts = document.createElement('div');
          contacts.className = 'a2ui-contact-items';
          (props.contacts || []).forEach((contact) => {
            const item = document.createElement('div');
            item.className = 'a2ui-contact-item';
            const icon = this.getContactIcon(contact.type || 'info');
            item.innerHTML = `
              <span class="a2ui-contact-icon">${icon}</span>
              <div class="a2ui-contact-info">
                <span class="a2ui-contact-value">${this.escapeHtml(contact.value || '')}</span>
                ${contact.description ? `<span class="a2ui-contact-desc">${this.escapeHtml(contact.description)}</span>` : ''}
              </div>
            `;
            contacts.appendChild(item);
          });
          card.appendChild(contacts);
          return card;
        }
        renderComparisonChart(props) {
          const chart = document.createElement('div');
          chart.className = 'a2ui-comparison-chart';
          const header = document.createElement('h3');
          header.className = 'a2ui-comparison-title';
          header.textContent = props.title || '';
          chart.appendChild(header);
          const table = document.createElement('div');
          table.className = 'a2ui-comparison-table';
          (props.items || []).forEach((item) => {
            const column = document.createElement('div');
            column.className = 'a2ui-comparison-column';
            if (item.recommended) column.classList.add('a2ui-recommended');
            let featuresHtml = '';
            (item.features || []).forEach((f) => {
              featuresHtml += `
                <div class="a2ui-comparison-row">
                  <span class="a2ui-feature-name">${this.escapeHtml(f.feature || '')}</span>
                  <span class="a2ui-feature-value">${this.escapeHtml(f.value || '')}</span>
                </div>
              `;
            });
            column.innerHTML = `
              <div class="a2ui-comparison-header">
                <h4>${this.escapeHtml(item.name || '')}</h4>
                ${item.recommended ? '<span class="a2ui-badge">Recommended</span>' : ''}
              </div>
              <div class="a2ui-comparison-features">${featuresHtml}</div>
            `;
            table.appendChild(column);
          });
          chart.appendChild(table);
          return chart;
        }
        renderStatsFlowLayout(props) {
          const layout = document.createElement('div');
          layout.className = 'a2ui-stats-flow';
          const header = document.createElement('h3');
          header.className = 'a2ui-stats-title';
          header.textContent = props.title || '';
          layout.appendChild(header);
          if (props.topStats && props.topStats.length) {
            const topSection = document.createElement('div');
            topSection.className = 'a2ui-stats-row a2ui-stats-top';
            props.topStats.forEach((stat) => {
              const statCard = document.createElement('div');
              statCard.className = 'a2ui-stat-card';
              statCard.innerHTML = `
                <span class="a2ui-stat-value">${this.escapeHtml(stat.value || '')}</span>
                <span class="a2ui-stat-label">${this.escapeHtml(stat.label || '')}</span>
              `;
              topSection.appendChild(statCard);
            });
            layout.appendChild(topSection);
          }
          if (props.bottomStats && props.bottomStats.length) {
            const bottomSection = document.createElement('div');
            bottomSection.className = 'a2ui-stats-row a2ui-stats-bottom';
            props.bottomStats.forEach((stat) => {
              const statCard = document.createElement('div');
              statCard.className = 'a2ui-stat-card';
              statCard.innerHTML = `
                <span class="a2ui-stat-value">${this.escapeHtml(stat.value || '')}</span>
                <span class="a2ui-stat-label">${this.escapeHtml(stat.label || '')}</span>
              `;
              bottomSection.appendChild(statCard);
            });
            layout.appendChild(bottomSection);
          }
          return layout;
        }
        renderTeamFlipCards(props) {
          const container = document.createElement('div');
          container.className = 'a2ui-team-cards';
          const header = document.createElement('h3');
          header.className = 'a2ui-team-title';
          header.textContent = props.title || '';
          container.appendChild(header);
          const cards = document.createElement('div');
          cards.className = 'a2ui-team-grid';
          (props.members || []).forEach((member) => {
            const card = document.createElement('div');
            card.className = 'a2ui-team-card';
            card.innerHTML = `
              <div class="a2ui-team-front">
                <div class="a2ui-team-avatar">${(member.name || '?').charAt(0)}</div>
                <h4 class="a2ui-team-name">${this.escapeHtml(member.name || '')}</h4>
                <span class="a2ui-team-role">${this.escapeHtml(member.role || '')}</span>
              </div>
              <div class="a2ui-team-back">
                <p class="a2ui-team-bio">${this.escapeHtml(member.bio || '')}</p>
              </div>
            `;
            card.addEventListener('click', () => { card.classList.toggle('flipped'); });
            cards.appendChild(card);
          });
          container.appendChild(cards);
          return container;
        }
        renderServiceHoverReveal(props) {
          const container = document.createElement('div');
          container.className = 'a2ui-services';
          const header = document.createElement('h3');
          header.className = 'a2ui-services-title';
          header.textContent = props.title || '';
          container.appendChild(header);
          const list = document.createElement('div');
          list.className = 'a2ui-services-list';
          (props.services || []).forEach((service) => {
            const item = document.createElement('div');
            item.className = 'a2ui-service-item';
            item.innerHTML = `
              <div class="a2ui-service-header">
                <h4 class="a2ui-service-name">${this.escapeHtml(service.name || '')}</h4>
              </div>
              <div class="a2ui-service-reveal">
                <p>${this.escapeHtml(service.description || '')}</p>
              </div>
            `;
            list.appendChild(item);
          });
          container.appendChild(list);
          return container;
        }
        renderMagazineHero(props) {
          const hero = document.createElement('div');
          hero.className = 'a2ui-magazine-hero';
          hero.innerHTML = `
            <div class="a2ui-hero-header">
              <h2 class="a2ui-hero-title">${this.escapeHtml(props.title || '')}</h2>
              ${props.subtitle ? `<p class="a2ui-hero-subtitle">${this.escapeHtml(props.subtitle)}</p>` : ''}
            </div>
            ${props.pullQuote ? `<blockquote class="a2ui-hero-quote">"${this.escapeHtml(props.pullQuote)}"</blockquote>` : ''}
            <div class="a2ui-hero-content">
              <p>${this.escapeHtml(props.content || '')}</p>
            </div>
            ${props.tags && props.tags.length ? `
              <div class="a2ui-hero-tags">
                ${props.tags.map(tag => `<span class="a2ui-tag">${this.escapeHtml(tag)}</span>`).join('')}
              </div>
            ` : ''}
          `;
          return hero;
        }
        renderFAQAccordion(props) {
          const container = document.createElement('div');
          container.className = 'a2ui-faq-accordion';
          const header = document.createElement('h3');
          header.className = 'a2ui-faq-title';
          header.textContent = props.title || '';
          container.appendChild(header);
          const list = document.createElement('div');
          list.className = 'a2ui-faq-list';
          (props.faqs || []).forEach((faq, idx) => {
            const item = document.createElement('div');
            item.className = 'a2ui-faq-item';
            if (idx === 0) item.classList.add('open');
            item.innerHTML = `
              <div class="a2ui-faq-question">
                <span>${this.escapeHtml(faq.question || '')}</span>
                <span class="a2ui-faq-icon">+</span>
              </div>
              <div class="a2ui-faq-answer">
                <p>${this.escapeHtml(faq.answer || '')}</p>
              </div>
            `;
            const questionEl = item.querySelector('.a2ui-faq-question');
            questionEl && questionEl.addEventListener('click', () => {
              item.classList.toggle('open');
            });
            list.appendChild(item);
          });
          container.appendChild(list);
          return container;
        }
        renderImageGallery(props) {
          const gallery = document.createElement('div');
          gallery.className = 'a2ui-image-gallery';
          const header = document.createElement('h3');
          header.className = 'a2ui-gallery-title';
          header.textContent = props.title || '';
          gallery.appendChild(header);
          const grid = document.createElement('div');
          grid.className = 'a2ui-gallery-grid';
          (props.images || []).forEach((img) => {
            const item = document.createElement('div');
            item.className = 'a2ui-gallery-item';
            item.innerHTML = `
              <img src="${this.escapeHtml(img.url || '')}" alt="${this.escapeHtml(img.alt || '')}" loading="lazy" />
              ${img.caption ? `<span class="a2ui-gallery-caption">${this.escapeHtml(img.caption)}</span>` : ''}
            `;
            grid.appendChild(item);
          });
          gallery.appendChild(grid);
          return gallery;
        }
        renderVideoGallery(props) {
          const gallery = document.createElement('div');
          gallery.className = 'a2ui-video-gallery';
          const header = document.createElement('h3');
          header.className = 'a2ui-gallery-title';
          header.textContent = props.title || '';
          gallery.appendChild(header);
          const grid = document.createElement('div');
          grid.className = 'a2ui-video-grid';
          (props.videos || []).forEach((video) => {
            const item = document.createElement('div');
            item.className = 'a2ui-video-item';
            const youtubeId = this.extractYouTubeId(video.url || '');
            if (youtubeId) {
              item.innerHTML = `
                <div class="a2ui-video-embed">
                  <iframe src="https://www.youtube.com/embed/${youtubeId}"
                          frameborder="0" allowfullscreen loading="lazy"></iframe>
                </div>
                <h4 class="a2ui-video-title">${this.escapeHtml(video.title || '')}</h4>
              `;
            } else {
              item.innerHTML = `
                <video controls>
                  <source src="${this.escapeHtml(video.url || '')}" type="video/mp4">
                </video>
                <h4 class="a2ui-video-title">${this.escapeHtml(video.title || '')}</h4>
              `;
            }
            grid.appendChild(item);
          });
          gallery.appendChild(grid);
          return gallery;
        }
        renderFallback(props) {
          const card = document.createElement('div');
          card.className = 'a2ui-simple-card a2ui-fallback';
          card.innerHTML = `
            <div class="a2ui-card-header">
              <span class="a2ui-icon">${this.getIcon('info')}</span>
              <h3 class="a2ui-card-title">${this.escapeHtml(props.title || 'Information')}</h3>
            </div>
            <div class="a2ui-card-content">
              <p>${this.escapeHtml(JSON.stringify(props, null, 2))}</p>
            </div>
          `;
          return card;
        }
        escapeHtml(text) {
          if (!text) return '';
          const div = document.createElement('div');
          div.textContent = text;
          return div.innerHTML;
        }
        getIcon(name) {
          const icons = {
            info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
            check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
            star: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
          };
          return icons[name] || icons.info;
        }
        getContactIcon(type) {
          const icons = {
            email: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><path d="M22 6l-10 7L2 6"/></svg>',
            phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>',
            address: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>',
            website: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>',
            info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
          };
          return icons[type] || icons.info;
        }
        extractYouTubeId(url) {
          const match = url.match(/(?:youtube\\.com\\/(?:[^\\/]+\\/.+\\/|(?:v|e(?:mbed)?)\\/|.*[?&]v=)|youtu\\.be\\/)([^\"&?\\/\\s]{11})/);
          return match ? match[1] : null;
        }
      }

      const renderer = new A2UIRenderer('a2ui-container');
      async function runQuery() {
        const query = document.getElementById('query').value.trim();
        if (!query) return;
        document.getElementById('text').textContent = 'Loading...';
        document.getElementById('a2ui').textContent = 'Loading...';
        document.getElementById('a2ui-status').textContent = 'RENDERING';
        const res = await fetch('/a2ui/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });
        const data = await res.json();
        document.getElementById('text').textContent = data.text || '';
        document.getElementById('a2ui').textContent = JSON.stringify(data.a2ui || {}, null, 2);
        if (data.a2ui) {
          renderer.render(data.a2ui);
          document.getElementById('a2ui-status').textContent = 'READY';
        } else {
          document.getElementById('a2ui-container').innerHTML = '<div class="a2ui-empty">No A2UI generated</div>';
          document.getElementById('a2ui-status').textContent = 'NO A2UI';
        }
      }
    </script>
  </body>
</html>
"""


@router.post("/a2ui/test")
async def a2ui_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run a test query and return text + A2UI JSON."""
    if not A2UI_AVAILABLE:
        raise HTTPException(status_code=500, detail="A2UI system not available")

    query = (payload or {}).get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query'")

    config = get_assistant_config()
    rag_service = create_rag_service(config.get("rag", {}))
    a2ui_config = config.get("a2ui", {}).get("config", {})
    tier_mode = a2ui_config.get("tier_mode", "auto")
    min_confidence = a2ui_config.get("min_confidence", 0.5)

    a2ui_service = get_a2ui_rag_service(
        rag_service=rag_service,
        enabled=True,
        tier_mode=tier_mode,
        min_confidence=min_confidence,
    )

    result = await a2ui_service.query(query=query, force_text_only=False)
    return {
        "text": result.text,
        "a2ui": result.a2ui,
        "tier": result.tier,
        "template_type": result.template_type,
    }


@router.get("/a2ui/styles.css")
async def a2ui_styles() -> FileResponse:
    """Serve A2UI component styles for the tester page."""
    css_path = BASE_DIR / "client" / "src" / "components" / "a2ui" / "a2ui-styles.css"
    return FileResponse(css_path)


@router.get("/a2ui/app.css")
async def a2ui_app_styles() -> FileResponse:
    """Serve main app styles for the tester page."""
    css_path = BASE_DIR / "client" / "src" / "style.css"
    return FileResponse(css_path)


@router.post("/graph/keywords")
async def extract_graph_keywords(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Select relevant knowledge graph nodes and extract topic based on query and answer.

    This endpoint uses LLM to select which graph nodes are relevant to highlight
    based on both the user query and the bot's answer. It also extracts the
    conversation topic and determines its relationship to previous topics.

    Request body:
        query (str): User query text
        answer (str, optional): Bot's answer text (improves node selection)
        previousTopics (list, optional): List of previous conversation topics

    Returns:
        Dict containing:
            - matched: List of node IDs to highlight in the graph
            - graph_node_count: Total nodes in graph
            - topic: Extracted conversation topic
            - topicType: "new", "continuation", or "branch"
            - parentTopic: Parent topic if branching (optional)
    """
    if not GRAPH_KEYWORDS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Graph keyword extraction not available")

    query = (payload or {}).get("query", "").strip()
    answer = (payload or {}).get("answer", "").strip()
    previous_topics = (payload or {}).get("previousTopics", [])

    if not query and not answer:
        raise HTTPException(status_code=400, detail="Missing 'query' or 'answer'")

    try:
        extractor = get_graph_keyword_extractor()
        result = await extractor.get_matching_keywords(query, answer, previous_topics)
        return result
    except Exception as e:
        logger.error(f"Graph keyword extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
