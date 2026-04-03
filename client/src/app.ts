/**
 * Voice AI - Voice Intelligence
 *
 * A sci-fi themed voice assistant with scanner interface and emotion visualization.
 * States: idle | listening | thinking | speaking
 *
 * Features:
 * - Scanner frame with animated scan line
 * - Circular audio visualizer
 * - Waveform visualization
 * - Emotion metrics panel
 * - Terminal system messages
 * - Floating particles
 */

import {
  RTVIClient,
  RTVIClientOptions,
  RTVIEvent,
} from '@pipecat-ai/client-js';
import {
  WebSocketTransport
} from "@pipecat-ai/websocket-transport";

// A2UI imports
import { A2UIRenderer } from './components/a2ui/A2UIRenderer';
import { A2UIDocument, isA2UIUpdate } from './types/a2ui';

// Emotion Chart import
import { EmotionChart } from './components/EmotionChart';
// Topic Timeline import
import { TopicTimeline } from './components/TopicTimeline';
// Synchronized Analysis (Topic Flow + Emotion)
import { extractTopicsFromMessages, layoutTopics } from './components/SynchronizedAnalysisWidget/topicExtraction';
import type { Message, Topic } from './components/SynchronizedAnalysisWidget/topicExtraction';
// Wave Visualization Config
import { waveConfig } from './config/waveVisualization';
import { Loader } from './components/Loader';

type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

class VoiceScannerApp {
  private rtviClient: RTVIClient | null = null;
  private transport: WebSocketTransport | null = null;
  private botPlayerAnalyser: AnalyserNode | null = null;
  private botPlayerDataArray: Uint8Array | null = null;
  private botPlayerContext: AudioContext | null = null;

  // UI Elements
  private scannerFrame: HTMLElement | null = null;
  private orbContainer: HTMLElement | null = null;
  private orbStatus: HTMLElement | null = null;
  private liquidBlob: HTMLElement | null = null;
  private orbInnerGlow: HTMLElement | null = null;
  private welcomeMessage: HTMLElement | null = null;
  private transcriptList: HTMLElement | null = null;
  private transcriptStatus: HTMLElement | null = null;
  private debugPanel: HTMLElement | null = null;
  private debugLog: HTMLElement | null = null;
  private debugToggle: HTMLElement | null = null;
  private debugClose: HTMLElement | null = null;
  private mainLayout: HTMLElement | null = null;
  private emotionPanel: HTMLElement | null = null;
  private emotionToggle: HTMLElement | null = null;
  private emotionLabel: HTMLElement | null = null;
  private emotionEmoji: HTMLElement | null = null;
  private emotionConfidence: HTMLElement | null = null;
  private toneLabel: HTMLElement | null = null;
  private arousalBar: HTMLElement | null = null;
  private arousalValue: HTMLElement | null = null;
  private dominanceValue: HTMLElement | null = null;
  private valenceValue: HTMLElement | null = null;
  private emotionTimeline: HTMLElement | null = null;
  private emotionChart: EmotionChart | null = null;
  private topicTimeline: TopicTimeline | null = null;
  private statusIndicator: HTMLElement | null = null;
  private loadingOverlay: HTMLElement | null = null;
  private loader: Loader | null = null;
  private terminalContent: HTMLElement | null = null;
  private terminalStatus: HTMLElement | null = null;
  private typingLine: HTMLElement | null = null;
  private timestampElement: HTMLElement | null = null;
  private notification: HTMLElement | null = null;

  // Canvas elements
  private waveformCanvas: HTMLCanvasElement | null = null;
  private circularCanvas: HTMLCanvasElement | null = null;
  private preloaderCanvas: HTMLCanvasElement | null = null;
  private geminiWaveCanvas: HTMLCanvasElement | null = null;
  private waveformCtx: CanvasRenderingContext2D | null = null;
  private circularCtx: CanvasRenderingContext2D | null = null;
  private preloaderCtx: CanvasRenderingContext2D | null = null;
  private geminiWaveCtx: CanvasRenderingContext2D | null = null;

  // Audio analysis - Dual source for Gemini-style visualization
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;  // Output (bot) audio
  private inputAnalyser: AnalyserNode | null = null;  // Input (mic) audio
  private dataArray: Uint8Array | null = null;
  private inputDataArray: Uint8Array | null = null;
  private animationFrame: number | null = null;

  // Gemini blob animation state
  private blobTime: number = 0;
  private blobPhase: number = 0;
  private smoothedAmplitude: number = 0;
  private targetAmplitude: number = 0;

  // Audio-driven wave state - stores smoothed frequency data for organic transitions
  private smoothedFrequencyData: number[] = new Array(64).fill(0);
  private waveHistory: number[][] = []; // Store recent wave frames for trail effect

  // Bot audio level from RTVI RemoteAudioLevel event
  private botAudioLevel: number = 0;
  private smoothedBotAudioLevel: number = 0;

  // Safari/iOS: ctx.filter blur is broken; use separate canvases + CSS blur
  private _waveBlurFallback: boolean | null = null;
  private _safariWaveLayers: { wrapper: HTMLDivElement; canvas: HTMLCanvasElement; ctx: CanvasRenderingContext2D }[] | null = null;

  // Audio
  private botAudio!: HTMLAudioElement;

  // State
  private voiceState: VoiceState = 'idle';
  private isConnected: boolean = false;
  private isConnecting: boolean = false;
  private isNoiseCancellation: boolean = true; // NC on by default (tight VAD)
  private preloaderAngle: number = 0;

  // Streaming transcript state
  private streamingBubble: HTMLElement | null = null;
  private currentUtteranceId: string | null = null;
  private streamingWords: string[] = [];
  private streamingTextActiveForSubtitle: boolean = false;  // Track if streaming_text is handling subtitle
  /** Skip the next onBotTranscript add (same content as the streaming bubble we just finalized). */
  private skipNextBotTranscriptAdd: boolean = false;

  // Subtitle timing: buffer words and release them synced with audio playback
  private subtitleWordBuffer: Array<{ word: string; seq: number; ptsOffset: number }> = [];
  private subtitleAudioStartTime: number = 0;  // performance.now() when BotStartedSpeaking fires
  private subtitleDisplayTimers: ReturnType<typeof setTimeout>[] = [];
  private subtitleDisplayedWords: string[] = [];  // words currently shown in subtitle
  private subtitleBufferFlushTimer: ReturnType<typeof setTimeout> | null = null;  // safety flush

  // Typewriter effect state for bot transcripts
  private currentBotBubble: HTMLElement | null = null;
  private typewriterQueue: string[] = [];
  private isTypewriting: boolean = false;
  private typewriterSpeed: number = 30; // ms per word

  // Live subtitle above wave (single line, current speaker only)
  private liveSubtitle: HTMLElement | null = null;
  private liveSubtitleText: HTMLElement | null = null;
  private subtitleClearTimeout: ReturnType<typeof setTimeout> | null = null;
  private botIsSpeaking: boolean = false;
  private subtitleWordCount: number = 0;
  private subtitleClearOnNextSentence: boolean = false;

  /** Max characters per subtitle line (wrap at word boundary). Desktop. */
  private static readonly MAX_SUBTITLE_LINE_CHARS = 42;
  /** Max characters per subtitle line on mobile (viewport width ≤ 640px). */
  private static readonly MAX_SUBTITLE_LINE_CHARS_MOBILE = 35;
  /** Viewport width below which mobile subtitle line length is used (match CSS breakpoint). */
  private static readonly SUBTITLE_MOBILE_BREAKPOINT_PX = 640;
  /** Delay in ms between revealing each subtitle line. Desktop. */
  private static readonly SUBTITLE_LINE_REVEAL_DELAY_MS = 2000;
  /** Delay in ms between revealing each subtitle line on mobile (viewport ≤ SUBTITLE_MOBILE_BREAKPOINT_PX). */
  private static readonly SUBTITLE_LINE_REVEAL_DELAY_MS_MOBILE = 1500;
  /** Max subtitle lines visible at once; when a new line appears, the oldest is hidden. */
  private static readonly MAX_SUBTITLE_LINES_VISIBLE = 2;
  /** Duration in ms for the subtitle scroll-up animation (then first line is removed). Match container enter/exit (500ms ease-in-out). */
  private static readonly SUBTITLE_SCROLL_DURATION_MS = 500;
  /** Timeouts for sequential line reveal; cleared when a new render starts. */
  private subtitleRevealTimeouts: ReturnType<typeof setTimeout>[] = [];
  /** Lines we've already scheduled (so we only append new lines, don't reset on every word). */
  private lastScheduledSubtitleLines: string[] = [];

  // Media control bar: speaker/mic icon toggle (slash = muted)
  private speakerMuted: boolean = false;
  private micMuted: boolean = false;
  private localAudioTrack: MediaStreamTrack | null = null;

  // Visual cards state
  private activeVisualCard: HTMLElement | null = null;
  private visualCardsContainer: HTMLElement | null = null;

  // A2UI state
  private a2uiRenderer: A2UIRenderer | null = null;
  private a2uiPanel: HTMLElement | null = null;
  private a2uiStatus: HTMLElement | null = null;
  private a2uiHasContent: boolean = false;

  // Emotion-reactive UI state
  private lastEmotionUpdate: number = 0;
  private emotionUpdateDebounceMs: number = 100;

  // Conversation messages for SynchronizedAnalysis (Topic Flow + Emotion)
  private conversationMessages: Message[] = [];
  private messageIdCounter: number = 0;

  // EmotionAnalysis widget: accumulated emotion data points from backend
  private emotionTopicNodes: { id: string; timestamp: Date; sentiment: 'positive' | 'neutral' | 'negative'; sentimentLabel: string; intensity: number }[] = [];
  private emotionNodeCounter: number = 0;

  // Persona selection
  private selectedPersonaId: string = '';
  private personaSelectionScreen: HTMLElement | null = null;
  private sessionStartTime: number = 0;

  // Dashboard stats tracking
  private mcStatMessageCount: number = 0;
  private mcStatEmotionShifts: number = 0;
  private mcStatLastEmotion: string = 'neutral';
  private mcStatLastBotResponseStart: number = 0;
  private mcStatLastResponseTime: string = '--';

  constructor() {  

    this.botAudio = document.createElement('audio');
    this.botAudio.autoplay = true;
    document.body.appendChild(this.botAudio);

    this.setupDOMElements();
    this.setupEventListeners();
    this.initializeCanvases();
    this.startTimestampUpdate();
    this.createFloatingParticles();
    this.showLoadingOverlay();
    this.setVoiceState('idle');

    // Hide loading after initialization, then show persona selection
    setTimeout(() => {
      this.hideLoadingOverlay();
      this.showPersonaSelection();
    }, 2500);

    // Expose test methods for debugging (no log spam on load)
    (window as any).testVisualCard = () => this.handleVisualHint({
      hint_type: 'project_card', content_type: 'projects',
      content: { mentioned: true }, confidence: 0.9,
      trigger_text: 'Test trigger', timestamp: Date.now() / 1000
    });
    (window as any).testEmotionTimeline = () => {
      ['happy', 'neutral', 'excited', 'sad', 'calm'].forEach((emotion, i) => {
        setTimeout(() => this.addEmotionToTimeline(emotion), i * 500);
      });
    };
  }

  // Carousel state
  private carouselOrder: number[] = [];
  private carouselPersonas: { id: string; name: string; role: string; description: string; avatar: string; tags: string[]; color?: string }[] = [];

  // Agent accent colors
  private static AGENT_COLORS: Record<string, string> = {
    receptionist: '#00d4aa',
    customer_support: '#ff8c42',
    indian_support: '#ff4da6',
    sales: '#ffc107',
    technical: '#4da6ff',
  };

  /**
   * Fetch personas from backend and render the 3D carousel selection screen
   */
  private async showPersonaSelection(): Promise<void> {
    this.personaSelectionScreen = document.getElementById('persona-selection-screen');
    const carousel = document.getElementById('persona-carousel');
    if (!this.personaSelectionScreen || !carousel) {
      this.handleConnect();
      return;
    }

    this.personaSelectionScreen.classList.remove('hidden');

    // Fallback persona data
    const fallbackPersonas = [
      { id: 'receptionist', name: 'Brooke', role: 'Receptionist', description: 'Confident and conversational front-desk assistant', avatar: '/personas/receptionist.webp', tags: ['English', 'Female', 'Professional'] },
      { id: 'customer_support', name: 'Blake', role: 'Customer Support', description: 'Energetic and engaging support specialist', avatar: '/personas/customer-support.webp', tags: ['English', 'Male', 'Support'] },
      { id: 'indian_support', name: 'Arushi', role: 'Hinglish Support', description: 'Warm and helpful Hinglish-speaking support agent', avatar: '/personas/indian-support.webp', tags: ['Hinglish', 'Female', 'India'] },
      { id: 'sales', name: 'Morgan', role: 'Sales Consultant', description: 'Polished and professional sales advisor', avatar: '/personas/sales.webp', tags: ['English', 'Female', 'Sales'] },
      { id: 'technical', name: 'Daniel', role: 'Technical Advisor', description: 'Clear and crisp technical expert in AI and voice systems', avatar: '/personas/technical.webp', tags: ['English', 'Male', 'Technical'] },
    ];

    let personas = fallbackPersonas;
    try {
      const backendUrl = this.getBackendUrl();
      const res = await fetch(`${backendUrl}/personas`);
      const data = await res.json();
      if (data.personas && data.personas.length > 0) {
        personas = data.personas;
      }
    } catch (err) {
      this.log(`Backend unreachable for personas, using fallback: ${err}`);
    }

    this.carouselPersonas = personas;

    // Build cards
    carousel.innerHTML = '';
    personas.forEach((persona, idx) => {
      const color = VoiceScannerApp.AGENT_COLORS[persona.id] || '#4da6ff';
      const card = document.createElement('div');
      card.className = 'persona-card';
      card.dataset.personaId = persona.id;
      card.style.setProperty('--agent-color', color);
      card.style.setProperty('--agent-glow', color + '26');
      card.style.setProperty('--agent-border', color + '4d');

      const initial = (persona.name || '?').charAt(0).toUpperCase();
      const avatarContent = persona.avatar
        ? `<img src="${persona.avatar}" alt="${persona.name}" onerror="this.parentElement.querySelector('.persona-avatar-ring')?.remove(); this.outerHTML='<div class=\\'persona-avatar-fallback\\'>${initial}</div>'" />`
        : `<div class="persona-avatar-fallback">${initial}</div>`;

      card.innerHTML = `
        <div class="persona-avatar-wrap">
          <div class="persona-avatar-ring" style="border-color: ${color}"></div>
          ${avatarContent}
        </div>
        <p class="persona-card-name">${persona.name}</p>
        <p class="persona-card-role" style="color: ${color}">${persona.role}</p>
        <p class="persona-card-desc">${persona.description}</p>
      `;

      // Click on card → rotate it to center
      card.addEventListener('click', () => {
        const currentPos = parseInt(card.getAttribute('data-pos') || '0');
        if (currentPos === 0) {
          // Already centered — select it
          this.selectPersona(persona.id);
        } else {
          // Rotate carousel to bring this card to center
          for (let i = 0; i < Math.abs(currentPos); i++) {
            if (currentPos > 0) this.carouselNext();
            else this.carouselPrev();
          }
        }
      });

      carousel.appendChild(card);
    });

    // Initialize carousel order: center the first card (receptionist)
    this.carouselOrder = personas.map((_, i) => {
      // Position cards: 0 = center, -1 = left, 1 = right, etc.
      const half = Math.floor(personas.length / 2);
      let pos = i;
      if (pos > half) pos = pos - personas.length;
      return pos;
    });
    this.updateCarousel();

    // Navigation buttons
    document.getElementById('persona-prev')?.addEventListener('click', () => this.carouselPrev());
    document.getElementById('persona-next')?.addEventListener('click', () => this.carouselNext());

    // Keyboard navigation
    this._carouselKeyHandler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') this.carouselNext();
      if (e.key === 'ArrowLeft') this.carouselPrev();
      if (e.key === 'Enter') {
        const cards = document.querySelectorAll('.persona-card');
        cards.forEach(c => {
          if (c.getAttribute('data-pos') === '0') {
            const pid = (c as HTMLElement).dataset.personaId;
            if (pid) this.selectPersona(pid);
          }
        });
      }
    };
    window.addEventListener('keydown', this._carouselKeyHandler);

    // CTA button
    document.getElementById('persona-cta')?.addEventListener('click', () => {
      const cards = document.querySelectorAll('.persona-card');
      cards.forEach(c => {
        if (c.getAttribute('data-pos') === '0') {
          const pid = (c as HTMLElement).dataset.personaId;
          if (pid) this.selectPersona(pid);
        }
      });
    });

    // Spawn background particles
    this.spawnParticles();
  }

  private _carouselKeyHandler: ((e: KeyboardEvent) => void) | null = null;

  private carouselNext(): void {
    // Shift left: first element goes to end
    const first = this.carouselOrder.shift()!;
    this.carouselOrder.push(first);
    this.updateCarousel();
  }

  private carouselPrev(): void {
    // Shift right: last element goes to start
    const last = this.carouselOrder.pop()!;
    this.carouselOrder.unshift(last);
    this.updateCarousel();
  }

  private updateCarousel(): void {
    const cards = document.querySelectorAll('.persona-card') as NodeListOf<HTMLElement>;
    const ctaBtn = document.getElementById('persona-cta') as HTMLElement | null;

    cards.forEach((card, index) => {
      const pos = this.carouselOrder[index];
      card.setAttribute('data-pos', String(pos));

      // Update CTA color based on front card
      if (pos === 0 && ctaBtn) {
        const color = VoiceScannerApp.AGENT_COLORS[card.dataset.personaId || ''] || '#4da6ff';
        ctaBtn.style.backgroundColor = color;
        ctaBtn.style.boxShadow = `0 0 25px ${color}4d`;
        ctaBtn.style.setProperty('--cta-glow', `${color}66`);
      }
    });
  }

  private spawnParticles(): void {
    const container = document.getElementById('persona-particles');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < 30; i++) {
      const p = document.createElement('div');
      p.className = 'persona-particle';
      const size = Math.random() * 3 + 1;
      p.style.width = `${size}px`;
      p.style.height = `${size}px`;
      p.style.left = `${Math.random() * 100}%`;
      p.style.top = `${Math.random() * 100}%`;
      p.style.animationDelay = `${Math.random() * 5}s`;
      p.style.animationDuration = `${Math.random() * 10 + 10}s`;
      container.appendChild(p);
    }
  }

  /**
   * Handle persona card click: store selection, hide screen, connect
   */
  // Map agent accent colors to RGB for CSS variables
  private static AGENT_COLORS_RGB: Record<string, string> = {
    receptionist: '0, 212, 170',
    customer_support: '255, 140, 66',
    indian_support: '255, 77, 166',
    sales: '255, 193, 7',
    technical: '77, 166, 255',
  };

  /** Convert hex color to "r, g, b" string for use in rgba() CSS vars */
  private static hexToRgb(hex: string): string {
    const h = hex.replace('#', '');
    const r = parseInt(h.substring(0, 2), 16);
    const g = parseInt(h.substring(2, 4), 16);
    const b = parseInt(h.substring(4, 6), 16);
    return `${r}, ${g}, ${b}`;
  }

  /** Darken a hex color by mixing with black (amount 0-1) */
  private static darkenHex(hex: string, amount: number): string {
    const h = hex.replace('#', '');
    const r = Math.round(parseInt(h.substring(0, 2), 16) * (1 - amount));
    const g = Math.round(parseInt(h.substring(2, 4), 16) * (1 - amount));
    const b = Math.round(parseInt(h.substring(4, 6), 16) * (1 - amount));
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  private selectPersona(personaId: string): void {
    this.selectedPersonaId = personaId;
    this.log(`Selected persona: ${personaId}`);

    // Apply agent accent color to CSS variables globally
    const color = VoiceScannerApp.AGENT_COLORS[personaId] || '#ff4da6';
    const colorRgb = VoiceScannerApp.AGENT_COLORS_RGB[personaId] || '255, 77, 166';
    document.documentElement.style.setProperty('--accent-hero', color);
    document.documentElement.style.setProperty('--accent-hero-rgb', colorRgb);

    // Set orb colors to match persona — primary is the accent, secondary is a darker shade
    const orbPrimary = color;
    const orbSecondary = VoiceScannerApp.darkenHex(color, 0.4);
    document.documentElement.style.setProperty('--orb-primary', orbPrimary);
    document.documentElement.style.setProperty('--orb-primary-rgb', VoiceScannerApp.hexToRgb(orbPrimary));
    document.documentElement.style.setProperty('--orb-secondary', orbSecondary);
    document.documentElement.style.setProperty('--orb-secondary-rgb', VoiceScannerApp.hexToRgb(orbSecondary));

    // Update agent identity on the talking page
    const persona = this.carouselPersonas.find(p => p.id === personaId);
    if (persona) {
      const agentName = document.getElementById('agent-name');
      const agentAvatar = document.getElementById('agent-avatar-img') as HTMLImageElement | null;
      const agentStatus = document.getElementById('agent-status');
      if (agentName) agentName.textContent = persona.name;
      if (agentAvatar && persona.avatar) agentAvatar.src = persona.avatar;
      if (agentStatus) agentStatus.textContent = 'Connecting...';

      // Sync Mission Control header
      const mcName = document.getElementById('mc-agent-name');
      if (mcName) mcName.textContent = persona.name;

      // Tint MC mini orb with agent color
      const mcOrbGlow = document.querySelector('.mc-orb-glow') as HTMLElement | null;
      if (mcOrbGlow) mcOrbGlow.style.background = `linear-gradient(135deg, ${color}, #7c3aed)`;
      const mcOrbCore = document.querySelector('.mc-orb-core') as HTMLElement | null;
      if (mcOrbCore) mcOrbCore.style.background = `linear-gradient(135deg, ${color}, #818cf8)`;
    }

    // Update orb gradient with agent color and cache element refs
    this.liquidBlob = document.getElementById('liquid-blob');
    this.orbInnerGlow = document.querySelector('.orb-inner-glow');
    if (this.liquidBlob) {
      this.liquidBlob.style.background = `linear-gradient(135deg, ${color} 0%, #2563eb 50%, #ffffff 100%)`;
    }

    // Remove keyboard listener
    if (this._carouselKeyHandler) {
      window.removeEventListener('keydown', this._carouselKeyHandler);
      this._carouselKeyHandler = null;
    }

    if (this.personaSelectionScreen) {
      this.personaSelectionScreen.classList.add('hidden');
    }

    // Start session timer
    this.sessionStartTime = Date.now();

    setTimeout(() => {
      this.handleConnect();
    }, 500);
  }

  private setupDOMElements(): void {
    // Legacy elements (hidden but kept for compatibility)
    this.scannerFrame = document.getElementById('scanner-frame');
    this.orbContainer = document.getElementById('voice-orb-container');
    this.orbStatus = document.getElementById('orb-status');

    // Main UI elements
    this.welcomeMessage = document.getElementById('welcome-message');
    this.transcriptList = document.getElementById('transcript-list');
    this.transcriptStatus = document.getElementById('transcript-status');
    this.liveSubtitle = document.getElementById('live-subtitle');
    this.liveSubtitleText = document.getElementById('live-subtitle-text');
    this.debugPanel = document.getElementById('debug-panel');
    this.debugLog = document.getElementById('debug-log');
    this.debugToggle = document.getElementById('debug-toggle');
    this.debugClose = document.getElementById('debug-close');
    this.mainLayout = document.querySelector('.main-layout');
    this.emotionPanel = document.getElementById('emotion-panel');
    this.emotionToggle = document.getElementById('emotion-toggle');
    this.emotionLabel = document.getElementById('emotion-label');
    this.emotionEmoji = document.getElementById('emotion-emoji');
    this.emotionConfidence = document.getElementById('emotion-confidence');
    this.toneLabel = document.getElementById('tone-label');
    this.arousalBar = document.getElementById('arousal-bar');
    this.arousalValue = document.getElementById('arousal-value');
    this.dominanceValue = document.getElementById('dominance-value');
    this.valenceValue = document.getElementById('valence-value');
    this.emotionTimeline = document.getElementById('emotion-timeline');
    this.statusIndicator = document.getElementById('status-indicator');
    this.loadingOverlay = document.getElementById('loading-overlay');

    // Initialize Loader (text configurable via loader.setText())
    const loadingTextEl = document.getElementById('loading-text');
    if (loadingTextEl) {
      this.loader = new Loader({
        container: loadingTextEl,
        text: 'Intitializing...',
      });
    }

    // Initialize Emotion Chart
    try {
      this.emotionChart = new EmotionChart('emotion-chart-canvas');
      // Expose for testing
      (window as any).testEmotionChart = () => {
        if (this.emotionChart) {
          this.emotionChart.addDataPoint(0.7, 0.6, 0.8);
          setTimeout(() => this.emotionChart?.addDataPoint(0.5, 0.4, 0.3), 500);
          setTimeout(() => this.emotionChart?.addDataPoint(0.8, 0.7, 0.6), 1000);
          setTimeout(() => this.emotionChart?.addDataPoint(0.4, 0.5, 0.7), 1500);
        }
      };
    } catch (e) {
      console.warn('[EmotionChart] Failed to initialize:', e);
    }

    // Initialize Topic Timeline
    try {
      this.topicTimeline = new TopicTimeline('topic-timeline-canvas');
    } catch (e) {
      console.warn('[TopicTimeline] Failed to initialize:', e);
    }

    this.terminalContent = document.getElementById('terminal-content');
    this.terminalStatus = document.getElementById('terminal-status');
    this.typingLine = document.getElementById('typing-line');
    this.timestampElement = document.getElementById('timestamp');
    this.notification = document.getElementById('notification');

    // Canvas elements
    this.waveformCanvas = document.getElementById('waveform-canvas') as HTMLCanvasElement;
    this.circularCanvas = document.getElementById('circular-canvas') as HTMLCanvasElement;
    this.preloaderCanvas = document.getElementById('preloader-canvas') as HTMLCanvasElement;
    this.geminiWaveCanvas = document.getElementById('gemini-wave-canvas') as HTMLCanvasElement;

    // A2UI elements
    this.a2uiPanel = document.getElementById('a2ui-panel');
    this.a2uiStatus = document.getElementById('a2ui-status');

    // Initialize A2UI renderer
    this.initializeA2UIRenderer();
  }

  private setupEventListeners(): void {
    // New connect/disconnect buttons
    const connectBtn = document.getElementById('connect-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');

    connectBtn?.addEventListener('click', () => this.handleConnect());
    disconnectBtn?.addEventListener('click', () => this.handleDisconnect());

    // Legacy scanner frame click (if still exists)
    this.scannerFrame?.addEventListener('click', () => this.handleOrbClick());

    // Debug panel
    this.debugToggle?.addEventListener('click', () => this.toggleDebugPanel());
    this.debugClose?.addEventListener('click', () => this.hideDebugPanel());

    document.getElementById('control-peak')?.addEventListener('click', () => this.toggleSidePanels());
    document.getElementById('control-close')?.addEventListener('click', () => {
      this.hideA2UIPanel();
      this.showCloseOptions(); // Switch bar to Restart | Peek so user can restart or peek
      this.handleDisconnect();
    });
    document.getElementById('control-speaker')?.addEventListener('click', () => this.toggleSpeakerIcon());
    document.getElementById('control-mic')?.addEventListener('click', () => this.toggleMicIcon());
    document.getElementById('control-nc')?.addEventListener('click', () => this.toggleNoiseCancellation());

    document.getElementById('close-option-restart')?.addEventListener('click', () => this.onRestartOption());
    document.getElementById('close-option-peak')?.addEventListener('click', () => this.onPeakOption());

    // Expanded Emotion Analysis: click card to show modal, click backdrop or press Esc to close
    const emotionCard = document.getElementById('dashboard-card-4');
    const emotionOverlay = document.getElementById('emotion-expanded-overlay');
    console.log('[EmotionExpanded] emotionCard:', emotionCard, 'overlay:', emotionOverlay);
    emotionCard?.addEventListener('click', (e) => {
      e.stopPropagation();
      console.log('[EmotionExpanded] Card clicked, showExpanded:', typeof (window as any).EmotionAnalysis?.showExpanded);
      const overlay = document.getElementById('emotion-expanded-overlay');
      if (overlay) {
        // Direct DOM approach as fallback
        overlay.classList.add('visible');
      }
      (window as any).EmotionAnalysis?.showExpanded?.();
    });
    emotionOverlay?.addEventListener('click', (e) => {
      // Close when clicking the backdrop (not the modal itself)
      if (e.target === emotionOverlay) {
        emotionOverlay.classList.remove('visible');
        (window as any).EmotionAnalysis?.hideExpanded?.();
      }
    });
    document.addEventListener('keydown', (e) => {
      const overlay = document.getElementById('emotion-expanded-overlay');
      if (e.key === 'Escape' && overlay?.classList.contains('visible')) {
        overlay.classList.remove('visible');
      }
    });

    document.getElementById('a2ui-close')?.addEventListener('click', () => this.hideA2UIPanel());

    this.updatePeakButtonState();

    // Emotion panel toggle
    this.emotionToggle?.addEventListener('click', () => this.toggleEmotionPanel());

  }

  /**
   * Handle connect button click
   */
  private handleConnect(): void {
    // Show connecting state immediately
    const connectBtn = document.getElementById('connect-btn');
    connectBtn?.classList.add('connecting');
    this.connect();
  }

  /**
   * Show Restart/Peak options: bar animates from bottom to center, buttons swap (when Close is clicked)
   */
  private showCloseOptions(): void {
    const mediaBar = document.getElementById('media-control-bar');
    const connectArea = document.getElementById('connect-area');
    mediaBar?.classList.add('close-mode');
    connectArea?.classList.add('hidden');
  }

  /**
   * Restart: hide cards if visible, reset all card data, hide options bar, disconnect, then connect (same flow as connect-btn)
   */
  private async onRestartOption(): Promise<void> {
    this.hideCloseOptions();
    // Hide all dashboard cards if they are visible (peek was open)
    if (this.mainLayout && !this.mainLayout.classList.contains('panels-hidden')) {
      this.mainLayout.classList.add('panels-hidden');
      this.updatePeakButtonState();
    }
    this.resetAllCardsData();
    await this.disconnect();
    // Show persona selection again so user can pick a different agent
    this.selectedPersonaId = '';
    this.showPersonaSelection();
  }

  /**
   * Reset all dashboard card data for a new conversation (SynchronizedAnalysis, Emotion, VisitorIntent, ToneModulator, KnowledgeGraph, Transcript).
   */
  private resetAllCardsData(): void {
    this.conversationMessages = [];
    this.emotionTopicNodes = [];
    this.emotionNodeCounter = 0;
    this.previousTopics = [];
    if (this.topicTimeline) this.topicTimeline.clear();
    this.refreshSynchronizedAnalysis();
    (window as any).EmotionAnalysis?.updateTopics?.([]);
    this.updateVisitorIntent([]);
    (window as any).ToneModulator?.update?.({ detectedEmotion: 'neutral', nesterResponse: 'calm' });
    (window as any).KnowledgeGraph?.stopCycle?.();
    (window as any).KnowledgeGraph?.clear?.();

    // Clear transcript DOM and show welcome message
    if (this.transcriptList && this.welcomeMessage) {
      this.transcriptList.innerHTML = '';
      this.transcriptList.appendChild(this.welcomeMessage);
      this.welcomeMessage.classList.remove('hidden');
    }
    this.currentBotBubble = null;
    this.streamingBubble = null;
    this.currentUtteranceId = null;
    this.skipNextBotTranscriptAdd = false;
    this.typewriterQueue = [];
    this.isTypewriting = false;
    this.accumulatedBotAnswer = '';
    if (this.subtitleClearTimeout) {
      clearTimeout(this.subtitleClearTimeout);
      this.subtitleClearTimeout = null;
    }
    this.botIsSpeaking = false;
    this.subtitleWordCount = 0;
    this.subtitleClearOnNextSentence = false;
    for (const t of this.subtitleRevealTimeouts) clearTimeout(t);
    this.subtitleRevealTimeouts = [];
    this.lastScheduledSubtitleLines = [];
    if (this.liveSubtitleText) this.liveSubtitleText.textContent = '';

    // Reset dashboard stats
    this.mcStatMessageCount = 0;
    this.mcStatEmotionShifts = 0;
    this.mcStatLastEmotion = 'neutral';
    this.mcStatLastBotResponseStart = 0;
    this.mcStatLastResponseTime = '--';
    this.updateMcStats();
  }

  /**
   * Peak: toggle side panels and show media bar again
   */
  private onPeakOption(): void {
    this.toggleSidePanels();
  }

  /**
   * Hide Restart/Peak options: bar animates back to bottom, buttons swap back
   */
  private hideCloseOptions(): void {
    const mediaBar = document.getElementById('media-control-bar');
    const connectArea = document.getElementById('connect-area');
    mediaBar?.classList.remove('close-mode');
    connectArea?.classList.remove('hidden');
  }

  /**
   * Handle disconnect button click
   */
  private handleDisconnect(): void {
    this.disconnect();
  }

  /**
   * Enable or disable the control-close button. Disabled while WebSocket is connecting.
   */
  private setCloseButtonEnabled(enabled: boolean): void {
    const closeBtn = document.getElementById('control-close');
    if (!closeBtn) return;
    (closeBtn as HTMLButtonElement).disabled = !enabled;
    closeBtn.setAttribute('aria-disabled', String(!enabled));
    if (enabled) {
      closeBtn.style.opacity = '1';
      closeBtn.style.pointerEvents = 'auto';
    } else {
      closeBtn.style.opacity = '0.3';
      closeBtn.style.pointerEvents = 'none';
    }
  }

  /**
   * Update UI for connection state
   */
  private updateConnectionUI(connected: boolean): void {
    const connectArea = document.getElementById('connect-area');
    const connectBtn = document.getElementById('connect-btn');
    const statusDisplay = document.getElementById('status-display');
    const connectionStatus = document.getElementById('connection-status');

    if (connected) {
      // Remove connecting state, add shrinking animation
      connectBtn?.classList.remove('connecting');
      connectBtn?.classList.add('shrinking');

      // After animation, hide connect area (disconnect is via control-close in media bar)
      setTimeout(() => {
        connectArea?.classList.add('hidden');
        connectBtn?.classList.remove('shrinking');
      }, 400);

      statusDisplay?.classList.remove('hidden');
      connectionStatus?.classList.add('online');
      if (connectionStatus) connectionStatus.textContent = 'ONLINE';
    } else {
      connectBtn?.classList.remove('connecting');
      connectBtn?.classList.remove('shrinking');
      this.setCloseButtonEnabled(true); // Ensure close is enabled when not connected
      // Don't show connect-area when bar is in close-mode (Restart serves that purpose)
      const mediaBar = document.getElementById('media-control-bar');
      if (!mediaBar?.classList.contains('close-mode')) {
        connectArea?.classList.remove('hidden');
      }
      statusDisplay?.classList.add('hidden');
      connectionStatus?.classList.remove('online');
      if (connectionStatus) connectionStatus.textContent = 'OFFLINE';
    }
  }

  /**
   * Play a premium crystal chime sound on connection using Web Audio API.
   * Creates a layered bell-like tone with harmonics and reverb tail.
   */
  private playCrystalChime(): void {
    try {
      const ctx = this.audioContext || new AudioContext();
      this.audioContext = ctx;
      const now = ctx.currentTime;

      // Master gain for the chime
      const master = ctx.createGain();
      master.gain.setValueAtTime(0, now);
      master.gain.linearRampToValueAtTime(0.25, now + 0.02);
      master.gain.exponentialRampToValueAtTime(0.001, now + 2.8);
      master.connect(ctx.destination);

      // Convolver for subtle shimmer/reverb
      const convolver = ctx.createConvolver();
      const reverbLen = ctx.sampleRate * 2;
      const reverbBuf = ctx.createBuffer(2, reverbLen, ctx.sampleRate);
      for (let ch = 0; ch < 2; ch++) {
        const data = reverbBuf.getChannelData(ch);
        for (let i = 0; i < reverbLen; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / reverbLen, 3);
        }
      }
      convolver.buffer = reverbBuf;
      const reverbGain = ctx.createGain();
      reverbGain.gain.value = 0.15;
      convolver.connect(reverbGain);
      reverbGain.connect(master);

      // Crystal bell harmonics — layered sine tones
      const harmonics = [
        { freq: 1318.5, gain: 0.35, decay: 2.2 },  // E6 - bright top
        { freq: 987.8,  gain: 0.45, decay: 2.5 },   // B5 - main tone
        { freq: 659.3,  gain: 0.3,  decay: 2.0 },   // E5 - body
        { freq: 1975.5, gain: 0.12, decay: 1.2 },   // B6 - sparkle
        { freq: 2637,   gain: 0.06, decay: 0.8 },   // E7 - air
      ];

      harmonics.forEach((h, i) => {
        const osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = h.freq;

        const gain = ctx.createGain();
        const onset = now + i * 0.04; // stagger each harmonic slightly
        gain.gain.setValueAtTime(0, onset);
        gain.gain.linearRampToValueAtTime(h.gain, onset + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.001, onset + h.decay);

        osc.connect(gain);
        gain.connect(master);
        gain.connect(convolver); // feed into reverb

        osc.start(onset);
        osc.stop(onset + h.decay + 0.1);
      });

      // High shimmer — subtle filtered noise burst
      const noiseLen = ctx.sampleRate * 0.15;
      const noiseBuf = ctx.createBuffer(1, noiseLen, ctx.sampleRate);
      const noiseData = noiseBuf.getChannelData(0);
      for (let i = 0; i < noiseLen; i++) {
        noiseData[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / noiseLen, 2);
      }
      const noiseSrc = ctx.createBufferSource();
      noiseSrc.buffer = noiseBuf;
      const hpf = ctx.createBiquadFilter();
      hpf.type = 'highpass';
      hpf.frequency.value = 6000;
      const noiseGain = ctx.createGain();
      noiseGain.gain.setValueAtTime(0.08, now);
      noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
      noiseSrc.connect(hpf);
      hpf.connect(noiseGain);
      noiseGain.connect(master);
      noiseSrc.start(now);
    } catch (e) {
      // Silently fail — sound is non-critical
    }
  }

  /**
   * Trigger premium orb bloom animation on connection.
   * Expands the orb with a radiant blue light burst.
   */
  private triggerConnectionBloom(): void {
    const orb = document.getElementById('ai-orb');
    const blob = document.getElementById('liquid-blob');
    if (!orb || !blob) return;

    // Add the bloom class that triggers the CSS animation
    orb.classList.add('connection-bloom');

    // Create a temporary radial light burst element
    const burst = document.createElement('div');
    burst.className = 'orb-light-burst';
    orb.appendChild(burst);

    // Clean up after animation completes
    setTimeout(() => {
      orb.classList.remove('connection-bloom');
      burst.remove();
    }, 2500);
  }

  /**
   * Update status display based on voice state
   */
  private updateStatusDisplay(): void {
    const statusDisplay = document.getElementById('status-display');
    const statusText = document.getElementById('status-text');

    if (!statusDisplay) return;

    // Remove all state classes
    statusDisplay.classList.remove('idle', 'listening', 'speaking', 'thinking');

    // Add current state class
    statusDisplay.classList.add(this.voiceState);

    // Update status text
    const stateTexts: Record<string, string> = {
      idle: 'READY',
      listening: 'LISTENING',
      speaking: 'SPEAKING',
      thinking: 'PROCESSING'
    };

    if (statusText) {
      statusText.textContent = stateTexts[this.voiceState] || 'READY';
    }
  }

  /**
   * Initialize canvas elements for visualizations
   */
  private initializeCanvases(): void {
    // Waveform canvas
    if (this.waveformCanvas) {
      this.waveformCanvas.width = this.waveformCanvas.offsetWidth * 2;
      this.waveformCanvas.height = this.waveformCanvas.offsetHeight * 2;
      this.waveformCtx = this.waveformCanvas.getContext('2d');
      this.drawIdleWaveform();
    }

    // Old circular canvas (kept for compatibility but hidden)
    if (this.circularCanvas) {
      const container = this.circularCanvas.parentElement;
      if (container) {
        const size = Math.max(container.offsetWidth, container.offsetHeight) + 100;
        this.circularCanvas.width = size;
        this.circularCanvas.height = size;
      }
      this.circularCtx = this.circularCanvas.getContext('2d');
    }

    // Gemini-style bottom wave visualizer canvas
    if (this.geminiWaveCanvas) {
      const container = this.geminiWaveCanvas.parentElement;
      if (container) {
        // Safari/iOS: ctx.filter blur is broken; use separate canvases + CSS blur
        if (this._waveBlurFallback === null && typeof navigator !== 'undefined') {
          const ua = navigator.userAgent;
          this._waveBlurFallback = (
            (/Safari\//.test(ua) && !/Chrome|Chromium/.test(ua)) ||
            /iPhone|iPad|iPod/.test(ua)
          );
        }
        if (this._waveBlurFallback === true) {
          this.ensureSafariWaveLayerDOM(container);
        } else {
          this.geminiWaveCanvas.width = container.offsetWidth * 2;  // 2x for retina
          this.geminiWaveCanvas.height = container.offsetHeight * 2;
        }
        this.geminiWaveCtx = this.geminiWaveCanvas.getContext('2d');

        // Start the Gemini wave animation
        this.startIdleBlobAnimation();
      }
    }

    // Preloader canvas
    if (this.preloaderCanvas) {
      this.preloaderCtx = this.preloaderCanvas.getContext('2d');
      this.animatePreloader();
    }
  }

  /**
   * Safari/iOS: Create separate canvases per layer with CSS blur wrapper.
   * ctx.filter blur is broken in Safari; this fallback uses CSS filter: blur() instead.
   */
  private ensureSafariWaveLayerDOM(container: HTMLElement): void {
    if (this._safariWaveLayers) return; // Already created

    const { layers } = waveConfig;
    const w = container.offsetWidth * 2;  // Retina
    const h = container.offsetHeight * 2;

    // Hide the main canvas; we'll use layer canvases instead
    if (this.geminiWaveCanvas) {
      this.geminiWaveCanvas.style.display = 'none';
    }

    const safariWrapper = document.createElement('div');
    safariWrapper.className = 'safari-wave-layers';
    safariWrapper.style.cssText = 'position:absolute;inset:0;pointer-events:none;';

    this._safariWaveLayers = [];
    for (let i = layers.length - 1; i >= 0; i--) {
      const layerConfig = layers[i];
      const layerBlur = layerConfig.blur;

      const layerDiv = document.createElement('div');
      layerDiv.style.cssText = `position:absolute;inset:0;overflow:hidden;filter:blur(${layerBlur}px);`;
      layerDiv.className = 'safari-wave-layer';

      const canvas = document.createElement('canvas');
      canvas.className = 'wave-canvas';
      canvas.width = w;
      canvas.height = h;
      canvas.style.cssText = 'width:100%;height:100%;';

      const ctx = canvas.getContext('2d');
      if (!ctx) continue;

      layerDiv.appendChild(canvas);
      safariWrapper.appendChild(layerDiv);
      this._safariWaveLayers.push({ wrapper: layerDiv, canvas, ctx });
    }

    container.appendChild(safariWrapper);
  }

  /**
   * Draw idle waveform (flat line with subtle noise)
   */
  private drawIdleWaveform(): void {
    if (!this.waveformCtx || !this.waveformCanvas) return;

    const ctx = this.waveformCtx;
    const width = this.waveformCanvas.width;
    const height = this.waveformCanvas.height;
    const centerY = height / 2;

    ctx.clearRect(0, 0, width, height);

    // Draw center line with gradient
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, 'rgba(55, 182, 255, 0.3)');
    gradient.addColorStop(0.5, 'rgba(55, 182, 255, 0.8)');
    gradient.addColorStop(1, 'rgba(55, 182, 255, 0.3)');

    ctx.strokeStyle = gradient;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, centerY);

    // Subtle idle movement
    for (let x = 0; x < width; x += 4) {
      const noise = Math.sin(x * 0.02 + Date.now() * 0.002) * 3;
      ctx.lineTo(x, centerY + noise);
    }

    ctx.stroke();
  }

  /**
   * Animate preloader spinner
   */
  private animatePreloader(): void {
    if (!this.preloaderCtx || !this.preloaderCanvas) return;

    const ctx = this.preloaderCtx;
    const width = this.preloaderCanvas.width;
    const height = this.preloaderCanvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 15;

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw arc segments
      const segments = 12;
      for (let i = 0; i < segments; i++) {
        const angle = (i / segments) * Math.PI * 2 + this.preloaderAngle;
        const alpha = 0.2 + (i / segments) * 0.8;

        ctx.strokeStyle = `rgba(55, 182, 255, ${alpha})`;
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, angle, angle + 0.3);
        ctx.stroke();
      }

      this.preloaderAngle += 0.05;

      if (this.loadingOverlay && !this.loadingOverlay.classList.contains('hidden')) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }

  /**
   * Show loading overlay
   */
  private showLoadingOverlay(): void {
    if (this.loadingOverlay) {
      this.loadingOverlay.classList.remove('hidden');
      this.animatePreloader();
      this.setCloseButtonEnabled(false);
    }
  }

   /**
   * Update loader text (e.g. "Planning next moves", "INITIALIZING")
   */
   setLoaderText(text: string): void {
    this.loader?.setText(text);
  }

  /**
   * Hide loading overlay
   */
  private hideLoadingOverlay(): void {
    if (this.loadingOverlay) {
      this.loadingOverlay.classList.add('hidden');
      this.setCloseButtonEnabled(true);
      this.addTerminalMessage('Voice scanner ready. Awaiting user input.', 'regular');
      // Dispatch event for components waiting for page ready
      window.dispatchEvent(new CustomEvent('nesterPageReady'));
    }
  }

  /**
   * Start timestamp update
   */
  private startTimestampUpdate(): void {
    const sessionTimer = document.getElementById('session-timer');
    const updateTime = () => {
      // Session timer (mm:ss from session start)
      if (sessionTimer && this.sessionStartTime > 0) {
        const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        const timeStr = `${mins}:${secs}`;
        sessionTimer.textContent = timeStr;
        // Sync to dashboard stats duration
        const mcDuration = document.getElementById('mc-stat-duration');
        if (mcDuration) mcDuration.textContent = timeStr;
      }
      // Legacy timestamp element
      if (this.timestampElement) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
        this.timestampElement.textContent = `TIME: ${timeStr}`;
      }
    };

    updateTime();
    setInterval(updateTime, 1000);
  }

  /**
   * Update mission control stats bar values
   */
  private updateMcStats(): void {
    const msgEl = document.getElementById('mc-stat-messages');
    if (msgEl) msgEl.textContent = String(this.mcStatMessageCount);
    const rtEl = document.getElementById('mc-stat-response-time');
    if (rtEl) rtEl.textContent = this.mcStatLastResponseTime;
    const esEl = document.getElementById('mc-stat-emotion-shifts');
    if (esEl) esEl.textContent = String(this.mcStatEmotionShifts);
  }

  /**
   * Create floating particles
   */
  private createFloatingParticles(): void {
    const container = document.getElementById('floating-particles');
    if (!container) return;

    const particleCount = 30;

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.cssText = `
        position: absolute;
        width: ${2 + Math.random() * 4}px;
        height: ${2 + Math.random() * 4}px;
        background: rgba(55, 182, 255, ${0.2 + Math.random() * 0.4});
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        animation: floatParticle ${10 + Math.random() * 20}s linear infinite;
        animation-delay: ${-Math.random() * 20}s;
      `;
      container.appendChild(particle);
    }
  }

  /**
   * Add message to terminal
   */
  private addTerminalMessage(message: string, type: 'command' | 'regular' | 'error' | 'success' = 'regular'): void {
    if (!this.terminalContent || !this.typingLine) return;

    const line = document.createElement('div');
    line.className = `terminal-line ${type}-line`;

    if (type === 'command') {
      line.textContent = `> ${message}`;
    } else if (type === 'error') {
      line.innerHTML = `<span style="color: #ef4444;">[ERROR]</span> ${message}`;
    } else if (type === 'success') {
      line.innerHTML = `<span style="color: #4ade80;">[OK]</span> ${message}`;
    } else {
      line.textContent = message;
    }

    // Insert before the typing line
    this.terminalContent.insertBefore(line, this.typingLine);

    // Keep only last 20 lines
    const lines = this.terminalContent.querySelectorAll('.terminal-line:not(.typing)');
    if (lines.length > 20) {
      lines[0].remove();
    }

    // Scroll to bottom
    this.terminalContent.scrollTop = this.terminalContent.scrollHeight;
  }

  /**
   * Show notification banner
   */
  private showNotification(message: string): void {
    if (!this.notification) return;

    this.notification.textContent = message;
    this.notification.classList.add('visible');

    setTimeout(() => {
      this.notification?.classList.remove('visible');
    }, 3000);
  }

  /**
   * Handle orb click - connect or disconnect
   */
  private async handleOrbClick(): Promise<void> {
    if (this.isConnecting) return;

    if (this.isConnected) {
      await this.disconnect();
    } else {
      await this.connect();
    }
  }

  /**
   * Set voice state and update UI
   */
  private setVoiceState(state: VoiceState): void {
    this.voiceState = state;

    // Update new status display UI
    this.updateStatusDisplay();

    // Update liquid blob orb state
    const orbEl = document.getElementById('ai-orb');
    if (orbEl) {
      orbEl.classList.remove('idle', 'listening', 'thinking', 'speaking');
      orbEl.classList.add(state);
    }

    // Update agent status text
    const agentStatus = document.getElementById('agent-status');
    if (agentStatus) {
      const statusTexts: Record<VoiceState, string> = {
        'idle': 'Ready',
        'listening': 'Listening...',
        'thinking': 'Thinking...',
        'speaking': 'Speaking...'
      };
      agentStatus.textContent = statusTexts[state];
    }

    // Legacy scanner frame updates (hidden but kept for compatibility)
    if (this.scannerFrame && this.orbContainer) {
      this.scannerFrame.classList.remove('idle', 'listening', 'thinking', 'speaking', 'connected');
      this.orbContainer.classList.remove('idle', 'listening', 'thinking', 'speaking', 'connected');
      this.scannerFrame.classList.add(state);
      this.orbContainer.classList.add(state);

      if (this.isConnected) {
        this.scannerFrame.classList.add('connected');
        this.orbContainer.classList.add('connected');
      }
    }

    // Update legacy status text
    if (this.orbStatus) {
      const statusTexts: Record<VoiceState, string> = {
        'idle': this.isConnected ? 'TAP TO TERMINATE' : 'TAP TO INITIALIZE',
        'listening': 'SCANNING VOICE INPUT...',
        'thinking': 'PROCESSING SIGNAL...',
        'speaking': 'TRANSMITTING RESPONSE...'
      };
      this.orbStatus.textContent = statusTexts[state];
    }

    // Update status indicator
    if (this.statusIndicator) {
      this.statusIndicator.className = this.isConnected ? 'live-dot active' : 'live-dot';
    }

    // Update transcript status
    if (this.transcriptStatus) {
      this.transcriptStatus.textContent = this.isConnected ? 'ACTIVE' : 'READY';
    }

    // Update terminal status
    if (this.terminalStatus) {
      this.terminalStatus.textContent = this.isConnected ? 'CONNECTED' : 'ONLINE';
    }

    // Update signal status
    const signalStatus = document.getElementById('signal-status');
    if (signalStatus) {
      const signalTexts: Record<VoiceState, string> = {
        'idle': 'STANDBY',
        'listening': 'RECEIVING',
        'thinking': 'PROCESSING',
        'speaking': 'TRANSMITTING'
      };
      signalStatus.textContent = signalTexts[state];
    }
  }

  /**
   * Log message to debug panel
   */
  private log(message: string): void {
    if (!this.debugLog) return;

    const entry = document.createElement('div');
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    entry.textContent = `[${time}] ${message}`;

    // Color coding
    if (message.startsWith('You:')) {
      entry.style.color = '#37b6ff';
    } else if (message.startsWith('Bot:')) {
      entry.style.color = '#9747ff';
    } else if (message.includes('Error')) {
      entry.style.color = '#ef4444';
    } else if (message.includes('Connected')) {
      entry.style.color = '#4ade80';
    }

    this.debugLog.appendChild(entry);
    this.debugLog.scrollTop = this.debugLog.scrollHeight;
  }

  /**
   * Refresh SynchronizedAnalysis widget with current conversation messages
   */
  private refreshSynchronizedAnalysis(): void {
    try {
      const topics = extractTopicsFromMessages(this.conversationMessages);
      const topicNodes = layoutTopics(topics);
      const categories = [...new Set(topics.map(t => t.category))];
      (window as any).SynchronizedAnalysis?.updateTopics?.(topicNodes);
      // Note: EmotionAnalysis widget is fed separately via pushEmotionToWidget()
      // from live emotion detection data — do not overwrite with topic nodes.
      this.updateVisitorIntent(topics);
    } catch (e) {
      console.warn('[Widget:ConversationAnalysis] Failed to refresh:', e);
    }
  }

  /**
   * Update Visitor Intent widget from extracted conversation topics.
   * Derives intent description, confidence, issue category, urgency, and tech level.
   */
  private updateVisitorIntent(topics: Topic[]): void {
    const descEl = document.getElementById('visitor-intent-desc');
    const confFill = document.getElementById('visitor-intent-confidence-fill');
    const languageEl = document.getElementById('visitor-language');
    const issueEl = document.getElementById('visitor-issue');
    const platformEl = document.getElementById('visitor-platform');
    const techLevelEl = document.getElementById('visitor-tech-level');
    const urgencyEl = document.getElementById('visitor-urgency');
    const priorContactEl = document.getElementById('visitor-prior-contact');

    if (topics.length === 0) {
      if (descEl) descEl.textContent = 'Visitor intent will appear here as you speak';
      if (confFill) confFill.style.width = '10%';
      if (languageEl) languageEl.textContent = 'English';
      if (issueEl) issueEl.textContent = 'N/A';
      if (platformEl) platformEl.textContent = 'Web';
      if (techLevelEl) techLevelEl.textContent = 'N/A';
      if (urgencyEl) urgencyEl.textContent = 'N/A';
      if (priorContactEl) priorContactEl.textContent = 'N/A';
      return;
    }

    // Intent = latest topic name + category
    const latest = topics[topics.length - 1];
    const uniqueCategories = [...new Set(topics.map(t => t.category))];
    const intentDesc = uniqueCategories.length > 1
      ? `Discussing ${latest.name} (${uniqueCategories.join(', ')})`
      : `Exploring ${latest.name} in ${latest.category}`;

    // Confidence: more topics with keywords = higher confidence (cap at 95%)
    const confidence = Math.min(95, 30 + topics.length * 15);

    // Issue: primary category from the most recent topic
    const issue = latest.category;

    // Tech level: if Technology topics detected, infer higher tech level
    const techTopicCount = topics.filter(t => t.category === 'Technology').length;
    let techLevel = 'Beginner';
    if (techTopicCount >= 3) techLevel = 'Advanced';
    else if (techTopicCount >= 1) techLevel = 'Intermediate';

    // Urgency: derive from latest sentiment
    let urgency = 'Medium';
    if (latest.sentiment === 'negative') urgency = 'High';
    else if (latest.sentimentLabel === 'Excited') urgency = 'High';
    else if (latest.sentiment === 'positive') urgency = 'Low';

    if (descEl) descEl.textContent = intentDesc;
    if (confFill) confFill.style.width = `${confidence}%`;
    if (languageEl) languageEl.textContent = 'English';
    if (issueEl) issueEl.textContent = issue;
    if (platformEl) platformEl.textContent = 'Web';
    if (techLevelEl) techLevelEl.textContent = techLevel;
    if (urgencyEl) urgencyEl.textContent = urgency;
    if (priorContactEl) priorContactEl.textContent = 'N/A';
  }

  /**
   * Format timestamp for transcript log (HH:mm:ss)
   */
  private formatTranscriptTime(date: Date = new Date()): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  }

  /**
   * Add transcript line to conversation (log style: timestamp + speaker + message)
   */
  private addTranscript(text: string, isUser: boolean): void {
    if (!this.transcriptList) return;

    // Hide welcome message
    this.welcomeMessage?.classList.add('hidden');

    // Track message count and response time for stats bar
    this.mcStatMessageCount++;
    if (isUser) {
      this.mcStatLastBotResponseStart = Date.now();
    } else if (this.mcStatLastBotResponseStart > 0) {
      const responseMs = Date.now() - this.mcStatLastBotResponseStart;
      this.mcStatLastResponseTime = responseMs < 1000 ? `${responseMs}ms` : `${(responseMs / 1000).toFixed(1)}s`;
      this.mcStatLastBotResponseStart = 0;
    }
    this.updateMcStats();

    // Push to conversation messages for SynchronizedAnalysis (before accumulatingBotAnswer is cleared)
    if (isUser) {
      if (this.accumulatedBotAnswer.trim()) {
        this.conversationMessages.push({
          id: `msg-${this.messageIdCounter++}`,
          text: this.accumulatedBotAnswer.trim(),
          timestamp: new Date(),
          isFinal: true,
          speaker: 'ai',
        });
      }
      this.conversationMessages.push({
        id: `msg-${this.messageIdCounter++}`,
        text,
        timestamp: new Date(),
        isFinal: true,
        speaker: 'user',
      });
      this.refreshSynchronizedAnalysis();
    }

    // Only show bot text in live subtitle, not user speech
    if (!isUser) {
      this.updateLiveSubtitle('bot', text);
    }

    const line = document.createElement('div');
    line.className = `transcript-line ${isUser ? 'transcript-line-user' : 'transcript-line-bot'}`;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'transcript-time';
    timeSpan.textContent = this.formatTranscriptTime() + ' ';

    const messageSpan = document.createElement('span');
    messageSpan.className = 'transcript-message';
    messageSpan.textContent = text;

    line.appendChild(timeSpan);
    line.appendChild(messageSpan);

    this.transcriptList.appendChild(line);

    // Scroll to bottom
    this.transcriptList.scrollTop = this.transcriptList.scrollHeight;
  }

  /**
   * Split text into lines of at most maxChars characters, wrapping at word boundaries.
   * Words longer than maxChars are broken mid-word.
   */
  private textToLines(text: string, maxChars: number): string[] {
    if (!text.trim()) return [];
    const words = text.trim().split(/\s+/).filter(w => w.length > 0);
    const lines: string[] = [];
    let current = '';
    for (const w of words) {
      const candidate = current ? current + ' ' + w : w;
      if (candidate.length <= maxChars) {
        current = candidate;
      } else {
        if (current) {
          lines.push(current);
          current = '';
        }
        let rest = w;
        while (rest.length > maxChars) {
          lines.push(rest.slice(0, maxChars));
          rest = rest.slice(maxChars);
        }
        if (rest.length > 0) current = rest;
      }
    }
    if (current) lines.push(current);
    return lines;
  }

  /**
   * Render subtitle as separate lines (max 42 chars per line).
   * Reveals lines sequentially with SUBTITLE_LINE_REVEAL_DELAY_MS between each.
   * When the 3rd line appears, the 1st is hidden (rolling window of 2 lines).
   * Only appends new lines when transcript grows (no reset on every word) so the delay is visible.
   */
  private renderSubtitleLines(lines: string[]): void {
    if (!this.liveSubtitleText) return;

    const isMobile = window.innerWidth <= VoiceScannerApp.SUBTITLE_MOBILE_BREAKPOINT_PX;
    const delayMs = isMobile
      ? VoiceScannerApp.SUBTITLE_LINE_REVEAL_DELAY_MS_MOBILE
      : VoiceScannerApp.SUBTITLE_LINE_REVEAL_DELAY_MS;
    const maxVisible = VoiceScannerApp.MAX_SUBTITLE_LINES_VISIBLE;

    const shouldReset =
      lines.length === 0 ||
      this.lastScheduledSubtitleLines.length === 0 ||
      lines[0] !== this.lastScheduledSubtitleLines[0] ||
      lines.length <= this.lastScheduledSubtitleLines.length;

    const isAppending =
      !shouldReset &&
      lines.length > this.lastScheduledSubtitleLines.length &&
      this.lastScheduledSubtitleLines.every((l, j) => lines[j] === l);

    if (shouldReset) {
      for (const t of this.subtitleRevealTimeouts) clearTimeout(t);
      this.subtitleRevealTimeouts = [];
      this.liveSubtitleText.innerHTML = '';
      this.lastScheduledSubtitleLines = [];
      if (lines.length === 0) return;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]!;
        const idx = i;
        const timeout = setTimeout(() => {
          if (!this.liveSubtitleText) return;
          this.clearSubtitleLinePromoted();
          const el = document.createElement('span');
          el.className = 'subtitle-line';
          el.textContent = line;
          this.liveSubtitleText.appendChild(el);
          if (idx >= maxVisible) {
            this.scrollSubtitleAndRemoveFirst();
          }
          // When this is the last line and we have 2+ lines, after one reveal-delay promote 2nd to 1st (no new line coming).
          if (idx === lines.length - 1 && lines.length >= 2) {
            const promoteTimeout = setTimeout(() => {
              if (!this.liveSubtitleText) return;
              if (this.liveSubtitleText.children.length >= 2) {
                this.scrollSubtitleAndRemoveFirst();
              }
            }, delayMs);
            this.subtitleRevealTimeouts.push(promoteTimeout);
          }
        }, idx * delayMs);
        this.subtitleRevealTimeouts.push(timeout);
      }
      this.lastScheduledSubtitleLines = [...lines];
      return;
    }

    if (isAppending) {
      const start = this.lastScheduledSubtitleLines.length;
      for (let i = start; i < lines.length; i++) {
        const line = lines[i]!;
        const idx = i;
        const delayFromNow = (i - start + 1) * delayMs;
        const timeout = setTimeout(() => {
          if (!this.liveSubtitleText) return;
          this.clearSubtitleLinePromoted();
          const el = document.createElement('span');
          el.className = 'subtitle-line';
          el.textContent = line;
          this.liveSubtitleText.appendChild(el);
          if (idx >= maxVisible) {
            this.scrollSubtitleAndRemoveFirst();
          }
          // When this is the last line and we have 2+ lines, after one reveal-delay promote 2nd to 1st (no new line coming).
          if (idx === lines.length - 1 && lines.length >= 2) {
            const promoteTimeout = setTimeout(() => {
              if (!this.liveSubtitleText) return;
              if (this.liveSubtitleText.children.length >= 2) {
                this.scrollSubtitleAndRemoveFirst();
              }
            }, delayMs);
            this.subtitleRevealTimeouts.push(promoteTimeout);
          }
        }, delayFromNow);
        this.subtitleRevealTimeouts.push(timeout);
      }
      this.lastScheduledSubtitleLines = [...lines];
    }
  }

  /** Remove promoted class from all subtitle lines so nth-child(2) correctly gets 30% opacity. */
  private clearSubtitleLinePromoted(): void {
    this.liveSubtitleText?.querySelectorAll('.subtitle-line-promoted').forEach((el) => {
      el.classList.remove('subtitle-line-promoted');
    });
  }

  /**
   * Scrolls the subtitle viewport up by one line (smooth), then removes the first line and resets scroll.
   * Call after appending a new line when we're at max visible lines (scroll-up-then-remove effect).
   */
  private scrollSubtitleAndRemoveFirst(): void {
    const container = this.liveSubtitleText;
    if (!container) return;
    const first = container.firstElementChild as HTMLElement | null;
    const second = first?.nextElementSibling as HTMLElement | null;
    if (!first) return;
    const gap = 2;
    const scrollAmount = first.offsetHeight + gap;
    const durationMs = VoiceScannerApp.SUBTITLE_SCROLL_DURATION_MS;
    const startTop = container.scrollTop;
    const easeInOutCubic = (t: number) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const opacityStartMs = 50;
    const opacityEndMs = 250;
    let startTime: number | null = null;
    const tick = (now: number) => {
      if (startTime === null) {
        startTime = now;
        if (second) second.classList.add('subtitle-line-promoted');
      }
      const elapsed = now - startTime;
      const t = Math.min(elapsed / durationMs, 1);
      container.scrollTop = startTop + (scrollAmount - startTop) * easeInOutCubic(t);
      if (second) {
        if (elapsed < opacityStartMs) {
          second.style.opacity = '0.3';
        } else if (elapsed >= opacityEndMs) {
          second.style.opacity = '1';
        } else {
          const u = (elapsed - opacityStartMs) / (opacityEndMs - opacityStartMs);
          const e = easeInOutCubic(u);
          second.style.opacity = String(0.3 + 0.7 * e);
        }
      }
      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        if (second) second.style.removeProperty('opacity');
        if (container.firstElementChild) {
          container.firstElementChild.remove();
          container.scrollTop = 0;
        }
      }
    };
    requestAnimationFrame(tick);
  }

  /**
   * Update the live subtitle above the wave visualizer (2 lines: user + bot, synced with voice).
   * Wraps text to 42 characters per line.
   */
  private updateLiveSubtitle(role: 'user' | 'bot', text: string): void {
    if (!this.liveSubtitle || !this.liveSubtitleText) return;
    if (!text) return;

    // Reset auto-clear timer
    if (this.subtitleClearTimeout) {
      clearTimeout(this.subtitleClearTimeout);
    }

    // Role class on container for .user / .bot text styling
    this.liveSubtitle.classList.remove('user', 'bot');
    this.liveSubtitle.classList.add(role);

    // User speech: prefix with "- " so we can identify user vs bot at a glance
    const displayText = role === 'user' ? `- ${text}` : text;

    const maxChars = window.innerWidth <= VoiceScannerApp.SUBTITLE_MOBILE_BREAKPOINT_PX
      ? VoiceScannerApp.MAX_SUBTITLE_LINE_CHARS_MOBILE
      : VoiceScannerApp.MAX_SUBTITLE_LINE_CHARS;
    const lines = this.textToLines(displayText, maxChars);
    this.renderSubtitleLines(lines);

    // Show the subtitle
    this.liveSubtitle.classList.add('visible');

    // For user transcripts: always auto-hide after 4s
    // For bot role when speaking: BotStoppedSpeaking handles the hide
    if (role === 'user' || !this.botIsSpeaking) {
      this.subtitleClearTimeout = setTimeout(() => {
        this.liveSubtitle?.classList.remove('visible');
      }, 4000);
    }
  }

  /**
   * Update bot live subtitle with full text as it comes from transcript (no typewriter effect, no delay).
   */
  private setBotSubtitleFromText(fullText: string): void {
    if (!fullText.trim()) return;
    this.updateLiveSubtitle('bot', fullText.trim());
  }

  /**
   * Add bot transcript with typewriter effect (word by word) - log style
   */
  private addBotTranscriptWithTypewriter(text: string): void {
    if (!this.transcriptList) return;

    // Hide welcome message
    this.welcomeMessage?.classList.add('hidden');

    // Create new line if none exists (log style: timestamp + Nester AI + message)
    if (!this.currentBotBubble) {
      this.currentBotBubble = document.createElement('div');
      this.currentBotBubble.className = 'transcript-line transcript-line-bot typewriter';

      const timeSpan = document.createElement('span');
      timeSpan.className = 'transcript-time';
      timeSpan.textContent = this.formatTranscriptTime() + ' ';

      const textSpan = document.createElement('span');
      textSpan.className = 'transcript-message typewriter-text';

      this.currentBotBubble.appendChild(timeSpan);
      this.currentBotBubble.appendChild(textSpan);
      this.transcriptList.appendChild(this.currentBotBubble);

      // Clear subtitle ONLY if streaming_text is not already active for this response
      // (prevents clearing subtitle when bot-transcript arrives after streaming_text has started)
      if (this.liveSubtitleText && !this.streamingBubble) {
        this.liveSubtitleText.innerHTML = '';
      } else if (this.streamingBubble) {
      }
    }

    // Split text into words and add to queue
    const words = text.split(/\s+/).filter(w => w.length > 0);
    // Mark subtitle to clear on next word ONLY if streaming_text is not active
    // (prevents clearing subtitle when bot-transcript arrives while streaming_text is handling it)
    if (this.liveSubtitleText && this.liveSubtitleText.childNodes.length > 0 && !this.streamingBubble) {
      this.subtitleClearOnNextSentence = true;
    }
    this.typewriterQueue.push(...words);

    // Start typewriter if not already running
    if (!this.isTypewriting) {
      this.processTypewriterQueue();
    }
  }

  /**
   * Process the typewriter queue word by word
   */
  private processTypewriterQueue(): void {
    if (this.typewriterQueue.length === 0) {
      this.isTypewriting = false;
      return;
    }

    this.isTypewriting = true;
    const word = this.typewriterQueue.shift()!;

    if (this.currentBotBubble) {
      const textSpan = this.currentBotBubble.querySelector('.transcript-message.typewriter-text');
      if (textSpan) {
        // Same as live subtitle: first word = start of line
        const isFirstWord = textSpan.childNodes.length === 0;

        // Add word with animation (same as transcript bubble)
        const wordSpan = document.createElement('span');
        wordSpan.className = 'typewriter-word';
        wordSpan.textContent = word + ' ';
        textSpan.appendChild(wordSpan);

        // Live subtitle: show full text as it comes (no typewriter effect)
        if (!this.streamingTextActiveForSubtitle) {
          this.setBotSubtitleFromText((textSpan.textContent || '').trim());
        }

        // Scroll to bottom
        if (this.transcriptList) {
          this.transcriptList.scrollTop = this.transcriptList.scrollHeight;
        }
      }
    }

    // Schedule next word
    setTimeout(() => this.processTypewriterQueue(), this.typewriterSpeed);
  }

  /**
   * Finalize the current bot bubble (called when user starts speaking)
   */
  private finalizeBotBubble(): void {
    if (this.currentBotBubble) {
      const textSpan = this.currentBotBubble.querySelector('.transcript-message.typewriter-text');
      if (textSpan) {
        this.updateLiveSubtitle('bot', (textSpan.textContent || '').trim());
      }
      this.currentBotBubble.classList.remove('typewriter');
      this.currentBotBubble.classList.add('finalized');

      // Convert animated words to static text for performance
      if (textSpan) {
        const fullText = textSpan.textContent || '';
        textSpan.innerHTML = '';
        textSpan.textContent = fullText;
      }
    }
    this.currentBotBubble = null;
    this.typewriterQueue = [];
    this.isTypewriting = false;
  }

  // Store last user query and accumulated bot answer for graph highlighting
  private lastUserQuery: string = '';
  private accumulatedBotAnswer: string = '';
  private graphHighlightTimeout: ReturnType<typeof setTimeout> | null = null;

  // Track previous topics for context (last 10 topics)
  private previousTopics: string[] = [];

  /**
   * Highlight relevant graph nodes based on query and answer
   * LLM selects nodes from the actual graph that match the conversation
   * Also returns the conversation topic for the timeline
   */
  private async highlightGraphKeywords(query: string, answer: string = ''): Promise<void> {
    if ((!query || query.trim().length < 3) && (!answer || answer.trim().length < 3)) return;

    const backendUrl = this.getBackendUrl();

    try {
      const response = await fetch(`${backendUrl}/graph/keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          answer,
          // Send previous topics for LLM context to determine topic relationships
          previousTopics: this.previousTopics,
        }),
      });

      if (!response.ok) {
        console.warn('[KnowledgeGraph] Node selection failed:', response.status);
        return;
      }

      const data = await response.json();

      // Highlight matched nodes in the graph with cycling animation
      if (data.matched && data.matched.length > 0 && (window as any).KnowledgeGraph) {
        (window as any).KnowledgeGraph.highlightWithCycle(data.matched);
      }

      // Add topic to timeline - topic and type come from backend LLM call
      if (this.topicTimeline && data.topic) {
        const keywords = data.matched || [];
        this.topicTimeline.addTopic(data.topic, keywords, data.topicType, data.parentTopic);

        // Track this topic for future context (keep last 10)
        this.previousTopics.push(data.topic);
        if (this.previousTopics.length > 10) {
          this.previousTopics.shift();
        }
      }
    } catch (error) {
      console.warn('[KnowledgeGraph] Failed to select nodes:', error);
    }
  }

  /**
   * Toggle debug panel
   */
  private toggleDebugPanel(): void {
    this.debugPanel?.classList.toggle('visible');
  }

  /**
   * Toggle left and right side panels visibility
   */
  private toggleSidePanels(): void {
    this.mainLayout?.classList.toggle('panels-hidden');
    this.updatePeakButtonState();

    const isHomeScreen = this.mainLayout?.classList.contains('panels-hidden') ?? true;
    if (isHomeScreen) {
      // Returning to home — restore A2UI panel if it has content
      if (this.a2uiHasContent && this.a2uiPanel) {
        this.a2uiPanel.classList.add('visible');
        document.body.classList.add('a2ui-panel-visible');
      }
    } else {
      // Switching to dashboard — hide A2UI panel (keep content flag)
      this.a2uiPanel?.classList.remove('visible');
      document.body.classList.remove('a2ui-panel-visible');
      // Force widget refresh after dashboard cards become visible (ResizeObserver needs layout)
      setTimeout(() => this.refreshSynchronizedAnalysis(), 100);
    }
  }

  /**
   * Update Peek button icon and text based on cards visibility (like speaker/mic)
   * Cards hidden → Eye + "Peek"; Cards showing → EyeClosed + "Hide"
   */
  private updatePeakButtonState(): void {
    const cardsShowing = this.mainLayout && !this.mainLayout.classList.contains('panels-hidden');
    const label = cardsShowing ? 'Hide' : 'Peek';

    const controlPeak = document.getElementById('control-peak');
    const controlPeakLabel = controlPeak?.querySelector('.pill-btn-label');
    if (controlPeakLabel) controlPeakLabel.textContent = label;
    controlPeak?.setAttribute('aria-label', cardsShowing ? 'Hide dashboard' : 'Peek view');
    controlPeak?.classList.toggle('peek-active', !!cardsShowing);

    const closeOptionPeak = document.getElementById('close-option-peak');
    const closeOptionPeakLabel = closeOptionPeak?.querySelector('.pill-btn-label');
    if (closeOptionPeakLabel) closeOptionPeakLabel.textContent = label;
    closeOptionPeak?.setAttribute('aria-label', cardsShowing ? 'Hide' : 'Peek');
    closeOptionPeak?.classList.toggle('peek-active', !!cardsShowing);
  }

  /**
   * Toggle speaker mute (SVG icon toggles via CSS class)
   */
  private toggleSpeakerIcon(): void {
    this.speakerMuted = !this.speakerMuted;
    if (this.botPlayerContext) {
      if (this.speakerMuted) {
        this.botPlayerContext.suspend();
      } else {
        this.botPlayerContext.resume();
      }
    }
    const btn = document.getElementById('control-speaker');
    if (btn) {
      btn.classList.toggle('muted', this.speakerMuted);
    }
    btn?.setAttribute('aria-label', this.speakerMuted ? 'Sound muted' : 'Sound');
  }

  /**
   * Toggle mic mute (SVG icon toggles via CSS class)
   */
  private toggleMicIcon(): void {
    this.micMuted = !this.micMuted;
    if (this.localAudioTrack) {
      this.localAudioTrack.enabled = !this.micMuted;
    }
    const btn = document.getElementById('control-mic');
    if (btn) {
      btn.classList.toggle('muted', this.micMuted);
      btn.classList.toggle('pill-btn-mic-active', !this.micMuted);
    }
    btn?.setAttribute('aria-label', this.micMuted ? 'Microphone muted' : 'Microphone');
  }

  /**
   * Toggle noise cancellation (tight vs relaxed VAD params)
   */
  private async toggleNoiseCancellation(): Promise<void> {
    this.isNoiseCancellation = !this.isNoiseCancellation;
    const mode = this.isNoiseCancellation ? 'tight' : 'relaxed';

    const btn = document.getElementById('control-nc');
    if (btn) {
      btn.classList.toggle('pill-btn-nc-active', this.isNoiseCancellation);
      btn.classList.toggle('pill-btn-nc-off', !this.isNoiseCancellation);
      btn.title = this.isNoiseCancellation
        ? 'Noise Cancellation: ON (tight VAD)'
        : 'Noise Cancellation: OFF (relaxed VAD)';
      // Toggle slash line on the icon
      const slashLine = btn.querySelector('.nc-slash-line') as HTMLElement;
      if (slashLine) slashLine.style.display = this.isNoiseCancellation ? 'none' : '';
    }

    // Call backend to update VAD params if connected
    if (this.isConnected) {
      try {
        const backendUrl = this.getBackendUrl();
        await fetch(`${backendUrl}/vad-mode`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode }),
        });
        this.log(`Noise cancellation: ${mode}`);
      } catch (e) {
        console.warn('[NC] Failed to update VAD mode:', e);
      }
    }
  }

  /**
   * Hide debug panel
   */
  private hideDebugPanel(): void {
    this.debugPanel?.classList.remove('visible');
  }

  /**
   * Toggle emotion panel visibility
   */
  private toggleEmotionPanel(): void {
    this.emotionPanel?.classList.toggle('visible');
  }

  /**
   * Chatterbox EMOTION_TO_PARAMS lookup (mirrors backend chatterbox_tts.py).
   * Maps detected emotion → {exaggeration, cfg_weight} used for TTS voice control.
   * ToneModulator clarity = 1 - cfg_weight (lower CFG = more assertive)
   * ToneModulator intensity = exaggeration (higher = more expressive)
   */
  private static readonly EMOTION_TO_PARAMS: Record<string, { exaggeration: number; cfg_weight: number }> = {
    neutral: { exaggeration: 0.4, cfg_weight: 0.5 },
    sad: { exaggeration: 0.6, cfg_weight: 0.4 },
    frustrated: { exaggeration: 0.5, cfg_weight: 0.5 },
    excited: { exaggeration: 0.9, cfg_weight: 0.3 },
    happy: { exaggeration: 0.8, cfg_weight: 0.35 },
    angry: { exaggeration: 0.7, cfg_weight: 0.4 },
  };

  /**
   * Update ToneModulator widget using Chatterbox CFG/exaggeration lookup.
   */
  private updateToneModulatorFromEmotion(detectedEmotion: string, nesterResponse?: string): void {
    const params = VoiceScannerApp.EMOTION_TO_PARAMS[detectedEmotion] || VoiceScannerApp.EMOTION_TO_PARAMS['neutral'];
    const clarity = 1 - params.cfg_weight;
    const intensity = params.exaggeration;
    (window as any).ToneModulator?.update?.({
      detectedEmotion,
      nesterResponse: nesterResponse ?? undefined,
      clarity,
      intensity,
    });
  }

  /**
   * Push a new emotion data point to the EmotionAnalysis widget.
   * Maps backend emotion string to sentiment/label for the chart.
   */
  private pushEmotionToWidget(emotion: string, arousal: number, valence: number): void {
    // Map emotion to sentiment
    const posEmotions = ['happy', 'excited', 'content', 'calm'];
    const negEmotions = ['sad', 'angry', 'frustrated', 'worried', 'fear'];
    let sentiment: 'positive' | 'neutral' | 'negative' = 'neutral';
    if (posEmotions.includes(emotion)) sentiment = 'positive';
    else if (negEmotions.includes(emotion)) sentiment = 'negative';

    // Map emotion to sentimentLabel (what the chart displays)
    const labelMap: Record<string, string> = {
      'excited': 'Excited', 'happy': 'Positive', 'content': 'Positive',
      'calm': 'Calm', 'neutral': 'Neutral',
      'sad': 'Concerned', 'angry': 'Concerned', 'frustrated': 'Concerned',
      'worried': 'Concerned', 'fear': 'Concerned',
    };

    this.emotionTopicNodes.push({
      id: `emo-${this.emotionNodeCounter++}`,
      timestamp: new Date(),
      sentiment,
      sentimentLabel: labelMap[emotion] || 'Neutral',
      intensity: Math.max(0, Math.min(1, (arousal + 1) / 2)), // normalize -1..1 to 0..1
    });

    // Keep last 30 points to avoid unbounded growth
    if (this.emotionTopicNodes.length > 30) {
      this.emotionTopicNodes = this.emotionTopicNodes.slice(-30);
    }

    const latest = this.emotionTopicNodes[this.emotionTopicNodes.length - 1];
    (window as any).EmotionAnalysis?.updateTopics?.(this.emotionTopicNodes);
  }

  /**
   * Update emotion display with detected emotion data
   */
  private updateEmotionDisplay(data: {
    arousal: number;
    dominance: number;
    valence: number;
    emotion: string;
    tone: string;
    confidence: number;
    timestamp: number;
  }): void {
    // Update emotion label and emoji
    const emotionEmojis: Record<string, string> = {
      'neutral': '😊',
      'happy': '😄',
      'excited': '🤩',
      'sad': '😢',
      'angry': '😠',
      'frustrated': '😤',
      'fear': '😨',
      'worried': '😟',
      'calm': '😌',
      'content': '😊',
    };

    const emoji = emotionEmojis[data.emotion] || '😊';
    const emotionName = data.emotion.toUpperCase();

    if (this.emotionEmoji) this.emotionEmoji.textContent = emoji;
    if (this.emotionLabel) this.emotionLabel.textContent = emotionName;
    if (this.emotionConfidence) {
      this.emotionConfidence.textContent = `${Math.round(data.confidence * 100)}%`;
    }

    // Update emotion chart with new data point
    if (this.emotionChart) {
      this.emotionChart.addDataPoint(data.arousal, data.dominance, data.valence);
    }

    // Add terminal message
    this.addTerminalMessage(`emotion.detect({type: '${data.emotion}', conf: ${(data.confidence * 100).toFixed(0)}%});`, 'command');

    this.log(`Emotion detected: ${emotionName} (${Math.round(data.confidence * 100)}%)`);

    // Tone Modulator: use Chatterbox CFG/exaggeration lookup for clarity/intensity
    this.updateToneModulatorFromEmotion(data.emotion, data.tone);

    // EmotionAnalysis widget: push live data point
    this.pushEmotionToWidget(data.emotion, data.arousal, data.valence);
  }

  /**
   * Update emotion display with HYBRID emotion data (audio + text)
   */
  private updateHybridEmotionDisplay(data: {
    primary_emotion: string;
    secondary_emotion?: string;
    arousal: number;
    dominance: number;
    valence: number;
    confidence: number;
    audio_emotion: string;
    text_emotion: string;
    audio_weight: number;
    text_weight: number;
    mismatch_detected: boolean;
    interpretation?: string;
    tokens_used: number;
    timestamp: number;
  }): void {
    // Update emotion label and emoji
    const emotionEmojis: Record<string, string> = {
      'neutral': '😊',
      'happy': '😄',
      'excited': '🤩',
      'sad': '😢',
      'angry': '😠',
      'frustrated': '😤',
      'fear': '😨',
      'worried': '😟',
      'calm': '😌',
      'content': '😊',
    };

    const emoji = emotionEmojis[data.primary_emotion] || '😊';
    const emotionName = data.primary_emotion.toUpperCase();

    if (this.emotionEmoji) this.emotionEmoji.textContent = emoji;
    if (this.emotionLabel) this.emotionLabel.textContent = emotionName;
    if (this.emotionConfidence) {
      this.emotionConfidence.textContent = `${Math.round(data.confidence * 100)}%`;
    }

    // Update emotion chart with new data point
    if (this.emotionChart) {
      this.emotionChart.addDataPoint(data.arousal, data.dominance, data.valence);
    }

    // Add hybrid-specific terminal message with audio/text breakdown
    const audioPercent = Math.round(data.audio_weight * 100);
    const textPercent = Math.round(data.text_weight * 100);

    let terminalMsg = `🔄 hybrid.emotion({primary: '${data.primary_emotion}', conf: ${(data.confidence * 100).toFixed(0)}%, audio: ${audioPercent}%, text: ${textPercent}%})`;

    if (data.mismatch_detected && data.interpretation) {
      terminalMsg += `\n⚠️  ${data.interpretation}`;
    }

    this.addTerminalMessage(terminalMsg, 'command');

    this.log(`🔄 Hybrid Emotion: ${emotionName} (${Math.round(data.confidence * 100)}%) | Audio: ${data.audio_emotion} ${audioPercent}% | Text: ${data.text_emotion} ${textPercent}%`);

    // Tone Modulator: use Chatterbox CFG/exaggeration lookup for clarity/intensity
    this.updateToneModulatorFromEmotion(data.primary_emotion);

    // EmotionAnalysis widget: push live data point
    this.pushEmotionToWidget(data.primary_emotion, data.arousal, data.valence);
  }

  /**
   * Update tone display when voice tone is switched
   */
  private updateToneDisplay(tone: string): void {
    const toneDisplayNames: Record<string, string> = {
      'neutral': 'NEUTRAL',
      'excited': 'ENERGETIC',
      'sad': 'EMPATHETIC',
      'frustrated': 'CALM',
      'happy': 'WARM',
      'angry': 'CONTROLLED',
      'fear': 'GENTLE',
      'content': 'RELAXED',
    };

    const displayName = toneDisplayNames[tone] || 'NEUTRAL';

    if (this.toneLabel) {
      this.toneLabel.textContent = displayName;
    }

    // Tone Modulator: Nester response tone
    if (typeof window !== 'undefined' && (window as unknown as { ToneModulator?: { update: (u: unknown) => void } }).ToneModulator?.update) {
      (window as unknown as { ToneModulator: { update: (u: { nesterResponse?: string }) => void } }).ToneModulator.update({ nesterResponse: tone });
    }

    this.addTerminalMessage(`voice.tone.switch('${tone}');`, 'command');
    this.log(`Voice tone switched to: ${displayName}`);
  }

  /**
   * Add emotion dot to timeline
   */
  private addEmotionToTimeline(emotion: string, _emoji?: string): void {
    if (!this.emotionTimeline) {
      return;
    }

    const emotionColors: Record<string, string> = {
      'neutral': '#7D7D7D',
      'happy': '#10b981',
      'excited': '#8b5cf6',
      'sad': '#3b82f6',
      'angry': '#ef4444',
      'frustrated': '#f59e0b',
      'fear': '#ec4899',
      'worried': '#f59e0b',
      'calm': '#10b981',
      'content': '#10b981',
    };

    const dot = document.createElement('div');
    dot.className = 'timeline-dot';
    dot.style.backgroundColor = emotionColors[emotion] || '#7D7D7D';
    dot.title = `${emotion.charAt(0).toUpperCase() + emotion.slice(1)}`;

    // Keep only last 15 emotions
    if (this.emotionTimeline.children.length >= 15) {
      this.emotionTimeline.removeChild(this.emotionTimeline.firstChild!);
    }

    this.emotionTimeline.appendChild(dot);

    // Animate dot entrance
    setTimeout(() => dot.classList.add('visible'), 10);
  }

  /**
   * Start audio visualization
   * The actual animation loop is in startIdleBlobAnimation which handles all states
   */
  private startAudioVisualization(): void {
    // Animation loop is already running from startIdleBlobAnimation
  }

  /**
   * Draw audio waveform
   */
  private drawWaveform(): void {
    if (!this.waveformCtx || !this.waveformCanvas || !this.dataArray) return;

    const ctx = this.waveformCtx;
    const width = this.waveformCanvas.width;
    const height = this.waveformCanvas.height;
    const centerY = height / 2;

    ctx.clearRect(0, 0, width, height);

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, 'rgba(55, 182, 255, 0.3)');
    gradient.addColorStop(0.3, 'rgba(55, 182, 255, 0.8)');
    gradient.addColorStop(0.5, 'rgba(151, 71, 255, 0.9)');
    gradient.addColorStop(0.7, 'rgba(55, 182, 255, 0.8)');
    gradient.addColorStop(1, 'rgba(55, 182, 255, 0.3)');

    ctx.strokeStyle = gradient;
    ctx.lineWidth = 2;
    ctx.beginPath();

    const sliceWidth = width / this.dataArray.length;
    let x = 0;

    for (let i = 0; i < this.dataArray.length; i++) {
      const v = this.dataArray[i] / 128.0;
      const y = centerY + (v - 1) * (height / 3);

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }

      x += sliceWidth;
    }

    ctx.stroke();

    // Draw glow effect
    ctx.strokeStyle = 'rgba(55, 182, 255, 0.3)';
    ctx.lineWidth = 6;
    ctx.stroke();
  }

  /**
   * Draw audio-driven wave visualizer at bottom of screen
   */
  private drawGeminiBlob(): void {
    const useSafariFallback = this._waveBlurFallback === true && this._safariWaveLayers && this._safariWaveLayers.length > 0;
    const ctx = useSafariFallback ? null : this.geminiWaveCtx;
    const canvas = useSafariFallback ? this._safariWaveLayers![0].canvas : this.geminiWaveCanvas;

    if (!canvas || (!useSafariFallback && !ctx)) return;

    const width = canvas.width;
    const height = canvas.height;

    // Safety check for valid dimensions
    if (width <= 0 || height <= 0) return;

    if (useSafariFallback) {
      for (const layer of this._safariWaveLayers!) {
        layer.ctx.clearRect(0, 0, width, height);
      }
    } else {
      ctx!.clearRect(0, 0, width, height);
    }

    // Update animation time
    this.blobTime += 0.02;
    this.blobPhase += 0.015;

    // Get active audio data based on state
    const activeDataArray = this.voiceState === 'speaking'
      ? this.dataArray
      : (this.voiceState === 'listening' ? this.inputDataArray : null);

    const numBars = this.smoothedFrequencyData.length;

    // Update smoothed frequency data from actual audio OR simulated audio
    if (this.voiceState === 'listening' && activeDataArray && activeDataArray.length > 0) {
      // User's turn (listening state) - mic input with base resting height
      for (let i = 0; i < numBars; i++) {
        const dataIndex = Math.floor((i / numBars) * activeDataArray.length * 0.8);
        const rawValue = (activeDataArray[dataIndex] || 0) / 255;

        // Apply noise gate threshold to filter out background noise
        const noiseThreshold = 0.08;
        const gatedValue = rawValue > noiseThreshold ? (rawValue - noiseThreshold) / (1 - noiseThreshold) : 0;

        // Base resting height + audio reactive component
        const baseHeight = 0.22 + Math.sin(this.blobPhase + i * 0.1) * 0.06;
        const audioComponent = Math.pow(gatedValue, 0.8) * 0.8;
        const targetValue = baseHeight + audioComponent;

        // Smooth transition (moderate attack, slower decay)
        if (targetValue > this.smoothedFrequencyData[i]) {
          this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.5;
        } else {
          this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.15;
        }
      }
    } else if (this.voiceState === 'speaking') {
      // Bot's turn (speaking state) - try to use real frequency data from bot audio analyser
      // Priority: botPlayerDataArray (WavStreamPlayer) > dataArray (TrackStarted) > simulated

      // Determine which data array to use
      let activeFreqArray: Uint8Array | null = null;

      // First, try the new bot player analyser (WavStreamPlayer from transport)
      if (this.botPlayerDataArray && this.botPlayerDataArray.length > 0) {
        for (let i = 0; i < this.botPlayerDataArray.length; i++) {
          if (this.botPlayerDataArray[i] > 5) {
            activeFreqArray = this.botPlayerDataArray;
            break;
          }
        }
      }

      // Fall back to old analyser (from TrackStarted event) if no bot player data
      if (!activeFreqArray && this.dataArray && this.dataArray.length > 0) {
        for (let i = 0; i < this.dataArray.length; i++) {
          if (this.dataArray[i] > 5) {
            activeFreqArray = this.dataArray;
            break;
          }
        }
      }

      if (activeFreqArray) {
        // Use REAL frequency data from bot audio analyser (IDENTICAL to user input processing)
        for (let i = 0; i < numBars; i++) {
          const dataIndex = Math.floor((i / numBars) * activeFreqArray.length * 0.8);
          const rawValue = (activeFreqArray[dataIndex] || 0) / 255;

          // Apply noise gate threshold (same as user input)
          const noiseThreshold = 0.08;
          const gatedValue = rawValue > noiseThreshold ? (rawValue - noiseThreshold) / (1 - noiseThreshold) : 0;

          // Base resting height + audio reactive component (same as user input)
          const baseHeight = 0.22 + Math.sin(this.blobPhase + i * 0.1) * 0.06;
          const audioComponent = Math.pow(gatedValue, 0.8) * 0.8;
          const targetValue = baseHeight + audioComponent;

          // Smooth transition (same as user input)
          if (targetValue > this.smoothedFrequencyData[i]) {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.5;
          } else {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.15;
          }
        }
      } else {
        // Fallback: Simulate frequency bands using single audio level
        this.smoothedBotAudioLevel += (this.botAudioLevel - this.smoothedBotAudioLevel) * 0.3;

        for (let i = 0; i < numBars; i++) {
          const baseHeight = 0.22 + Math.sin(this.blobPhase + i * 0.1) * 0.06;
          const pos = i / numBars;

          // Multiple frequency band simulation
          const band1 = Math.sin(this.blobTime * 4.5 + i * 0.3) * 0.5 + 0.5;
          const band2 = Math.sin(this.blobTime * 6.2 + i * 0.5) * 0.5 + 0.5;
          const band3 = Math.sin(this.blobTime * 8.1 + i * 0.7) * 0.5 + 0.5;
          const band4 = Math.sin(this.blobTime * 5.3 + i * 0.4) * 0.5 + 0.5;

          const lowWeight = Math.exp(-Math.pow((pos - 0.2) * 3, 2));
          const midWeight = Math.exp(-Math.pow((pos - 0.45) * 3, 2));
          const highWeight = Math.exp(-Math.pow((pos - 0.7) * 3, 2));
          const extraWeight = Math.exp(-Math.pow((pos - 0.35) * 4, 2));

          const combinedBands = (band1 * lowWeight + band2 * midWeight + band3 * highWeight + band4 * extraWeight) / 2;
          const audioComponent = this.smoothedBotAudioLevel * combinedBands * 1.2;

          const targetValue = baseHeight + audioComponent;

          if (targetValue > this.smoothedFrequencyData[i]) {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.5;
          } else {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.15;
          }
        }
      }
    } else {
      // Idle/thinking animation
      for (let i = 0; i < numBars; i++) {
        let targetValue: number;
        if (this.voiceState === 'thinking') {
          targetValue = 0.25 + Math.sin(this.blobTime * 2 + i * 0.2) * 0.1;
        } else {
          // Idle resting position - taller base wave
          targetValue = 0.35 + Math.sin(this.blobPhase + i * 0.25) * 0.07;
        }
        this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.1;
      }
    }

    // Calculate overall amplitude
    let totalAmplitude = 0;
    for (let i = 0; i < numBars; i++) {
      totalAmplitude += this.smoothedFrequencyData[i];
    }
    this.smoothedAmplitude = totalAmplitude / numBars;

    // State-based colors
    let primaryColor: string;
    let glowAlpha: number;

    switch (this.voiceState) {
      case 'idle':
        primaryColor = '#ef3339';
        glowAlpha = 0.15;
        break;
      case 'listening':
        primaryColor = '#22c55e';
        glowAlpha = 0.6;
        break;
      case 'thinking':
        primaryColor = '#f97316';
        glowAlpha = 0.4;
        break;
      case 'speaking':
        primaryColor = '#ef3339';
        glowAlpha = 0.7;
        break;
      default:
        primaryColor = '#ef3339';
        glowAlpha = 0.15;
    }

    // Wave parameters from configuration
    const { numPoints, maxWaveHeightRatio, layers, layerTimeOffset, layerSpeedIncrement, edgeFadePower, organicWaveAmplitude } = waveConfig;
    const baseY = height; // Start from bottom
    const maxWaveHeight = height * maxWaveHeightRatio;
    const numLayers = layers.length;

    // Get interpolated value from frequency data with smoothing
    const getAudioValue = (position: number): number => {
      const idx = Math.max(0, Math.min(position, 1)) * (numBars - 1);
      const i0 = Math.floor(idx);
      const i1 = Math.min(i0 + 1, numBars - 1);
      const t = idx - i0;
      const v0 = this.smoothedFrequencyData[i0] || 0;
      const v1 = this.smoothedFrequencyData[i1] || 0;
      return v0 * (1 - t) + v1 * t;
    };

    // Draw multiple layered waves from back to front
    for (let layer = numLayers - 1; layer >= 0; layer--) {
      const layerConfig = layers[layer];
      const layerScale = layerConfig.heightScale;
      const layerBlur = layerConfig.blur;
      const layerOffset = layer * layerTimeOffset;
      const layerSpeed = 1 + layer * layerSpeedIncrement;

      const layerCtx = useSafariFallback
        ? this._safariWaveLayers![numLayers - 1 - layer].ctx
        : ctx!;

      // Apply blur filter for this layer (Safari: skip - CSS blur on wrapper handles it)
      if (!useSafariFallback) {
        layerCtx.filter = layerBlur > 0 ? `blur(${layerBlur}px)` : 'none';
      }

      layerCtx.beginPath();
      layerCtx.moveTo(0, baseY);

      // Draw the wave curve
      for (let i = 0; i <= numPoints; i++) {
        const x = (i / numPoints) * width;
        const normalizedX = i / numPoints;

        // Mirror frequency data from center for symmetric wave
        const dataPosition = normalizedX <= 0.5 ? normalizedX * 2 : (1 - normalizedX) * 2;

        // Get audio value and add organic movement
        const audioValue = getAudioValue(dataPosition);
        const organicWave = Math.sin(normalizedX * Math.PI * 3 + this.blobTime * layerSpeed + layerOffset) * organicWaveAmplitude;

        // Calculate wave height - rises from bottom
        const waveIntensity = (audioValue + organicWave) * layerScale;
        const waveHeight = Math.max(0, waveIntensity) * maxWaveHeight;

        // Edge fade for smooth tapering at sides
        const edgeFade = Math.pow(Math.sin(normalizedX * Math.PI), edgeFadePower);

        const y = baseY - waveHeight * edgeFade;
        layerCtx.lineTo(x, y);
      }

      // Complete the shape by going to bottom corners
      layerCtx.lineTo(width, baseY);
      layerCtx.lineTo(0, baseY);
      layerCtx.closePath();

      // Fill with solid color from config
      layerCtx.fillStyle = layerConfig.color;
      layerCtx.fill();

      if (!useSafariFallback) {
        layerCtx.filter = 'none';
      }
    }

  }

  /**
   * Update peak frequency display
   */
  private updatePeakFrequency(): void {
    if (!this.dataArray) return;

    let maxVal = 0;
    let maxIndex = 0;

    for (let i = 0; i < this.dataArray.length; i++) {
      if (this.dataArray[i] > maxVal) {
        maxVal = this.dataArray[i];
        maxIndex = i;
      }
    }

    // Approximate frequency (assuming 44100 sample rate)
    const frequency = Math.round((maxIndex * 44100) / (this.dataArray.length * 2));

    const peakValue = document.getElementById('peak-value');
    if (peakValue && maxVal > 10) {
      peakValue.textContent = `${frequency} HZ`;
    }

    // Update amplitude
    const amplitudeValue = document.getElementById('amplitude-value');
    if (amplitudeValue) {
      const amplitude = (maxVal / 255).toFixed(2);
      amplitudeValue.textContent = amplitude;
    }
  }

  /**
   * Stop audio visualization
   */
  private stopAudioVisualization(): void {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }

    // Reset displays
    this.drawIdleWaveform();

    // Draw one final idle blob frame
    this.smoothedAmplitude = 0;
    this.drawGeminiBlob();

    const peakValue = document.getElementById('peak-value');
    if (peakValue) peakValue.textContent = '-- HZ';

    const amplitudeValue = document.getElementById('amplitude-value');
    if (amplitudeValue) amplitudeValue.textContent = '0.00';
  }

  /**
   * Drive the liquid blob orb visuals from real bot audio amplitude per frame.
   * Only reacts when bot is speaking — full ballooning vibration driven by real audio.
   */
  private updateOrbFromAudio(): void {
    if (!this.liquidBlob) return;

    const t = performance.now() / 1000;

    if (this.voiceState === 'speaking') {
      // --- Bot speaking: full aggressive audio-reactive vibration ---
      const amp = Math.min(this.smoothedAmplitude, 1.0);

      // Scale: base 1.0, max ~1.25 at full amplitude — full ballooning
      const scale = 1.0 + amp * 0.25;

      // Organic morph from 4 frequency bands — ±20% deformation
      const len = this.smoothedFrequencyData.length;
      const f0 = this.smoothedFrequencyData[0] || 0;
      const f1 = this.smoothedFrequencyData[Math.floor(len * 0.25)] || 0;
      const f2 = this.smoothedFrequencyData[Math.floor(len * 0.5)] || 0;
      const f3 = this.smoothedFrequencyData[Math.floor(len * 0.75)] || 0;

      // Map frequency bands to border-radius deformations (30-70% range)
      const r1 = 50 + (f0 - 0.3) * 20 + Math.sin(t * 2.1) * 3;
      const r2 = 50 + (f1 - 0.3) * 20 + Math.sin(t * 2.7) * 3;
      const r3 = 50 + (f2 - 0.3) * 20 + Math.sin(t * 3.2) * 3;
      const r4 = 50 + (f3 - 0.3) * 20 + Math.sin(t * 1.8) * 3;
      const r5 = 50 + (f1 - 0.3) * 15 + Math.sin(t * 2.4) * 3;
      const r6 = 50 + (f2 - 0.3) * 15 + Math.sin(t * 3.0) * 3;
      const r7 = 50 + (f3 - 0.3) * 15 + Math.sin(t * 1.5) * 3;
      const r8 = 50 + (f0 - 0.3) * 15 + Math.sin(t * 2.0) * 3;

      // Rotation wobble from amplitude
      const rotate = Math.sin(t * 3.5) * amp * 4;

      this.liquidBlob.style.transform = `scale(${scale}) rotate(${rotate}deg)`;
      this.liquidBlob.style.borderRadius = `${r1}% ${r2}% ${r3}% ${r4}% / ${r5}% ${r6}% ${r7}% ${r8}%`;

      // Glow intensity scales with amplitude — massive spread
      const glowIntensity = 0.4 + amp * 0.6;
      const glowSpread = 100 + amp * 120;
      const outerGlow = 60 + amp * 80;
      const farGlow = 40 + amp * 60;
      this.liquidBlob.style.boxShadow = `
        inset 0 0 ${50 + amp * 40}px rgba(255, 255, 255, ${0.35 + amp * 0.35}),
        0 0 ${glowSpread}px rgba(37, 99, 235, ${glowIntensity}),
        0 0 ${glowSpread + outerGlow}px rgba(37, 99, 235, ${glowIntensity * 0.5}),
        0 0 ${glowSpread + outerGlow + farGlow}px rgba(108, 60, 224, ${glowIntensity * 0.3})
      `;

      // Override CSS animation — JS drives everything
      this.liquidBlob.style.animation = 'none';

      // Inner glow pulses hard with audio
      if (this.orbInnerGlow) {
        const glowScale = 1.0 + amp * 0.5;
        const glowOpacity = 0.4 + amp * 0.4;
        (this.orbInnerGlow as HTMLElement).style.transform = `scale(${glowScale})`;
        (this.orbInnerGlow as HTMLElement).style.opacity = `${glowOpacity}`;
      }
    } else if (this.voiceState === 'thinking') {
      // Pulsing rotation, no audio data
      const pulse = 0.5 + Math.sin(t * 3) * 0.5;
      const scale = 1.0 + pulse * 0.05;
      const rotate = Math.sin(t * 2) * 3;
      this.liquidBlob.style.transform = `scale(${scale}) rotate(${rotate}deg)`;
      this.liquidBlob.style.borderRadius = `${45 + Math.sin(t * 2.5) * 5}% ${55 - Math.sin(t * 2.5) * 5}% ${50 + Math.sin(t * 3) * 5}% ${50 - Math.sin(t * 3) * 5}% / ${55 - Math.sin(t * 2) * 5}% ${45 + Math.sin(t * 2) * 5}% ${50 - Math.sin(t * 2.8) * 5}% ${50 + Math.sin(t * 2.8) * 5}%`;
      this.liquidBlob.style.boxShadow = `
        inset 0 0 40px rgba(255, 255, 255, ${0.3 + pulse * 0.15}),
        0 0 60px rgba(37, 99, 235, ${0.2 + pulse * 0.15}),
        0 0 90px rgba(108, 60, 224, ${0.08 + pulse * 0.07})
      `;
      this.liquidBlob.style.animation = 'none';
    } else {
      // Idle / listening — restore CSS animations, clear JS overrides
      if (this.liquidBlob.style.animation === 'none') {
        this.liquidBlob.style.animation = '';
        this.liquidBlob.style.transform = '';
        this.liquidBlob.style.borderRadius = '';
        this.liquidBlob.style.boxShadow = '';
        if (this.orbInnerGlow) {
          (this.orbInnerGlow as HTMLElement).style.transform = '';
          (this.orbInnerGlow as HTMLElement).style.opacity = '';
        }
      }
    }
  }

  /**
   * Process audio frequency data into smoothedFrequencyData and smoothedAmplitude.
   * Runs every frame regardless of whether the canvas is visible.
   */
  private processAudioData(): void {
    this.blobTime += 0.02;
    this.blobPhase += 0.015;

    const numBars = this.smoothedFrequencyData.length;

    if (this.voiceState === 'speaking') {
      // Determine which bot audio data array to use
      let activeFreqArray: Uint8Array | null = null;

      if (this.botPlayerDataArray && this.botPlayerDataArray.length > 0) {
        for (let i = 0; i < this.botPlayerDataArray.length; i++) {
          if (this.botPlayerDataArray[i] > 5) {
            activeFreqArray = this.botPlayerDataArray;
            break;
          }
        }
      }

      if (!activeFreqArray && this.dataArray && this.dataArray.length > 0) {
        for (let i = 0; i < this.dataArray.length; i++) {
          if (this.dataArray[i] > 5) {
            activeFreqArray = this.dataArray;
            break;
          }
        }
      }

      if (activeFreqArray) {
        for (let i = 0; i < numBars; i++) {
          const dataIndex = Math.floor((i / numBars) * activeFreqArray.length * 0.8);
          const rawValue = (activeFreqArray[dataIndex] || 0) / 255;
          const noiseThreshold = 0.08;
          const gatedValue = rawValue > noiseThreshold ? (rawValue - noiseThreshold) / (1 - noiseThreshold) : 0;
          const baseHeight = 0.22 + Math.sin(this.blobPhase + i * 0.1) * 0.06;
          const audioComponent = Math.pow(gatedValue, 0.8) * 0.8;
          const targetValue = baseHeight + audioComponent;

          if (targetValue > this.smoothedFrequencyData[i]) {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.5;
          } else {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.15;
          }
        }
      } else {
        // Fallback: simulate from single audio level
        this.smoothedBotAudioLevel += (this.botAudioLevel - this.smoothedBotAudioLevel) * 0.3;
        for (let i = 0; i < numBars; i++) {
          const baseHeight = 0.22 + Math.sin(this.blobPhase + i * 0.1) * 0.06;
          const pos = i / numBars;
          const band1 = Math.sin(this.blobTime * 4.5 + i * 0.3) * 0.5 + 0.5;
          const band2 = Math.sin(this.blobTime * 6.2 + i * 0.5) * 0.5 + 0.5;
          const band3 = Math.sin(this.blobTime * 8.1 + i * 0.7) * 0.5 + 0.5;
          const band4 = Math.sin(this.blobTime * 5.3 + i * 0.4) * 0.5 + 0.5;
          const lowWeight = Math.exp(-Math.pow((pos - 0.2) * 3, 2));
          const midWeight = Math.exp(-Math.pow((pos - 0.45) * 3, 2));
          const highWeight = Math.exp(-Math.pow((pos - 0.7) * 3, 2));
          const extraWeight = Math.exp(-Math.pow((pos - 0.35) * 4, 2));
          const combinedBands = (band1 * lowWeight + band2 * midWeight + band3 * highWeight + band4 * extraWeight) / 2;
          const audioComponent = this.smoothedBotAudioLevel * combinedBands * 1.2;
          const targetValue = baseHeight + audioComponent;

          if (targetValue > this.smoothedFrequencyData[i]) {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.5;
          } else {
            this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.15;
          }
        }
      }
    } else if (this.voiceState === 'listening' && this.inputDataArray && this.inputDataArray.length > 0) {
      for (let i = 0; i < numBars; i++) {
        const dataIndex = Math.floor((i / numBars) * this.inputDataArray.length * 0.8);
        const rawValue = (this.inputDataArray[dataIndex] || 0) / 255;
        const noiseThreshold = 0.08;
        const gatedValue = rawValue > noiseThreshold ? (rawValue - noiseThreshold) / (1 - noiseThreshold) : 0;
        const baseHeight = 0.22 + Math.sin(this.blobPhase + i * 0.1) * 0.06;
        const audioComponent = Math.pow(gatedValue, 0.8) * 0.8;
        const targetValue = baseHeight + audioComponent;

        if (targetValue > this.smoothedFrequencyData[i]) {
          this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.5;
        } else {
          this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.15;
        }
      }
    } else {
      // Idle/thinking
      for (let i = 0; i < numBars; i++) {
        let targetValue: number;
        if (this.voiceState === 'thinking') {
          targetValue = 0.25 + Math.sin(this.blobTime * 2 + i * 0.2) * 0.1;
        } else {
          targetValue = 0.35 + Math.sin(this.blobPhase + i * 0.25) * 0.07;
        }
        this.smoothedFrequencyData[i] += (targetValue - this.smoothedFrequencyData[i]) * 0.1;
      }
    }

    // Calculate overall amplitude
    let totalAmplitude = 0;
    for (let i = 0; i < numBars; i++) {
      totalAmplitude += this.smoothedFrequencyData[i];
    }
    this.smoothedAmplitude = totalAmplitude / numBars;
  }

  /**
   * Start idle blob animation (runs even when not connected)
   */
  private startIdleBlobAnimation(): void {
    if (this.animationFrame) return;

    const animate = () => {
      // Read mic audio frequency data when user is speaking
      if (this.voiceState === 'listening' && this.inputAnalyser && this.inputDataArray) {
        this.inputAnalyser.getByteFrequencyData(this.inputDataArray as Uint8Array<ArrayBuffer>);
      }

      // Read bot audio frequency data when AI is speaking
      // Prefer botPlayerAnalyser (from transport's WavStreamPlayer) over the old analyser
      if (this.voiceState === 'speaking') {
        if (this.botPlayerAnalyser && this.botPlayerDataArray) {
          this.botPlayerAnalyser.getByteFrequencyData(this.botPlayerDataArray as Uint8Array<ArrayBuffer>);
        } else if (this.analyser && this.dataArray) {
          this.analyser.getByteFrequencyData(this.dataArray as Uint8Array<ArrayBuffer>);
        }
      }

      // Process audio data into smoothedFrequencyData/smoothedAmplitude (always runs)
      this.processAudioData();

      // Draw the main wave visualizer (may skip if canvas hidden)
      this.drawGeminiBlob();

      // Drive liquid blob orb from processed audio data
      this.updateOrbFromAudio();

      // When connected, also update other visualizations
      if (this.isConnected) {
        this.drawWaveform();
        this.updatePeakFrequency();
      }

      this.animationFrame = requestAnimationFrame(animate);
    };
    animate();
  }

  /**
   * Set up output audio track (bot voice) with visualization
   */
  private botAnalyserSetup = false;

  private setupAudioTrack(track: MediaStreamTrack): void {
    this.log('Bot audio track connected');

    const stream = new MediaStream([track]);
    this.botAudio.srcObject = stream;

    // Set up audio analysis for visualization
    try {
      if (!this.audioContext) {
        this.audioContext = new AudioContext();
      }

      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      // Only set up analyser once
      if (!this.botAnalyserSetup) {
        // Method 1: Try to capture stream from the audio element (works best for playback)
        if ('captureStream' in this.botAudio) {
          this.botAudio.onplay = () => {
            if (this.botAnalyserSetup) return;
            try {
              const capturedStream = (this.botAudio as any).captureStream();
              const source = this.audioContext!.createMediaStreamSource(capturedStream);
              this.analyser = this.audioContext!.createAnalyser();
              this.analyser.fftSize = 256;
              this.analyser.smoothingTimeConstant = 0.5;
              source.connect(this.analyser);
              this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
              this.botAnalyserSetup = true;
            } catch (e) {
            }
          };
        }

        // Method 2: Also try direct MediaStreamSource as backup
        const source = this.audioContext.createMediaStreamSource(stream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.analyser.smoothingTimeConstant = 0.5;
        source.connect(this.analyser);
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      }

      this.startAudioVisualization();
    } catch (e) {
      console.warn('Could not set up output audio visualization:', e);
    }
  }

  /**
   * Set up input audio track (user microphone) with visualization
   */
  private setupInputAudioTrack(track: MediaStreamTrack): void {
    this.log('Microphone audio track connected for visualization');

    try {
      if (!this.audioContext) {
        this.audioContext = new AudioContext();
      }

      const stream = new MediaStream([track]);
      const source = this.audioContext.createMediaStreamSource(stream);
      this.inputAnalyser = this.audioContext.createAnalyser();
      this.inputAnalyser.fftSize = 256;
      this.inputAnalyser.smoothingTimeConstant = 0.7;
      source.connect(this.inputAnalyser);
      this.inputDataArray = new Uint8Array(this.inputAnalyser.frequencyBinCount);

      this.log('Microphone analyser ready for Gemini-style visualization');
    } catch (e) {
      console.warn('Could not set up input audio visualization:', e);
    }
  }

  /**
   * Set up bot player analyser from transport's internal WavStreamPlayer
   * This gives us real frequency data for bot audio visualization
   */
  private setupBotPlayerAnalyser(): void {
    try {
      if (!this.transport) return;
      const mediaManager = (this.transport as any)._mediaManager;
      if (!mediaManager) return;
      const wavPlayer = mediaManager._wavStreamPlayer;
      if (!wavPlayer) return;

      if (wavPlayer.context) {
        this.botPlayerContext = wavPlayer.context as AudioContext;
      }

      if (wavPlayer.analyser) {
        this.botPlayerAnalyser = wavPlayer.analyser as AnalyserNode;
        this.botPlayerDataArray = new Uint8Array(this.botPlayerAnalyser.frequencyBinCount);
      } else {
        // Retry after delay — player might connect later
        setTimeout(() => {
          if (wavPlayer.analyser && !this.botPlayerAnalyser) {
            this.botPlayerAnalyser = wavPlayer.analyser as AnalyserNode;
            this.botPlayerDataArray = new Uint8Array(this.botPlayerAnalyser.frequencyBinCount);
          }
        }, 1000);
      }
    } catch (e) {
      console.warn('[BOT AUDIO] Setup failed:', e);
    }
  }

  /**
   * Set up media tracks
   */
  private setupMediaTracks(): void {
    if (!this.rtviClient) return;
    const tracks = this.rtviClient.tracks();

    // Set up bot output audio
    if (tracks.bot?.audio) {
      this.setupAudioTrack(tracks.bot.audio);
    }

    // Set up local microphone input for visualization
    if (tracks.local?.audio) {
      this.localAudioTrack = tracks.local.audio;
      this.setupInputAudioTrack(tracks.local.audio);
    }
  }

  /**
   * Set up event listeners for RTVI
   */
  private setupTrackListeners(): void {
    if (!this.rtviClient) return;

    // Track events
    this.rtviClient.on(RTVIEvent.TrackStarted, (track, participant) => {
      if (track.kind === 'audio') {
        if (participant?.local) {
          // Local microphone track - for user voice visualization
          this.localAudioTrack = track;
          this.setupInputAudioTrack(track);
        } else {
          // Remote bot track - for AI voice visualization
          this.setupAudioTrack(track);
        }
      }
    });

    // Bot speech events
    this.rtviClient.on(RTVIEvent.BotStartedSpeaking, () => {
      this.log('Bot started speaking');
      // Note: Bot audio visualization uses simulated data since RTVI doesn't expose bot audio track
      this.botIsSpeaking = true;
      if (this.subtitleClearTimeout) {
        clearTimeout(this.subtitleClearTimeout);
        this.subtitleClearTimeout = null;
      }
      this.setVoiceState('speaking');

      // Audio is now playing — schedule buffered subtitle words based on PTS timing
      this.subtitleAudioStartTime = performance.now();
      if (this.subtitleBufferFlushTimer) {
        clearTimeout(this.subtitleBufferFlushTimer);
        this.subtitleBufferFlushTimer = null;
      }
      this.flushSubtitleWordBuffer();
    });

    this.rtviClient.on(RTVIEvent.BotStoppedSpeaking, () => {
      this.log('Bot stopped speaking');
      this.botIsSpeaking = false;
      // If subtitle display timers are still running, don't hide yet —
      // schedule hide after remaining timers would have completed.
      // Use a generous delay to ensure all PTS-timed words have been shown.
      const pendingTimers = this.subtitleDisplayTimers.length > 0;
      const hideDelay = pendingTimers ? 5000 : Math.min(Math.max(this.subtitleWordCount * 80, 1500), 4000);
      this.subtitleWordCount = 0;
      if (this.subtitleClearTimeout) {
        clearTimeout(this.subtitleClearTimeout);
      }
      this.subtitleClearTimeout = setTimeout(() => {
        this.liveSubtitle?.classList.remove('visible');
      }, hideDelay);
      if (this.isConnected) {
        this.setVoiceState('listening');
      }
    });

    // User speech events
    this.rtviClient.on(RTVIEvent.UserStartedSpeaking, () => {
      this.log('User started speaking');
      this.setVoiceState('listening');
      this.showNotification('VOICE DETECTED');

      // Stop bot subtitle words from continuing to appear after interruption
      this.clearSubtitleDisplayTimers();
      this.subtitleWordBuffer = [];
      this.subtitleDisplayedWords = [];
      this.subtitleAudioStartTime = 0;

      // Hide bot subtitle so user transcript can take over
      this.liveSubtitle?.classList.remove('visible');
      if (this.subtitleClearTimeout) {
        clearTimeout(this.subtitleClearTimeout);
        this.subtitleClearTimeout = null;
      }
    });

    this.rtviClient.on(RTVIEvent.UserStoppedSpeaking, () => {
      this.log('User stopped speaking');
      this.setVoiceState('thinking');
    });

    // Listen for bot audio levels - this gives us real-time audio level data for visualization
    this.rtviClient.on(RTVIEvent.RemoteAudioLevel, (level: number) => {
      this.botAudioLevel = level;
    });
  }

  /**
   * Get backend URL
   */
  private getBackendUrl(): string {
    // @ts-ignore
    if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) {
      // @ts-ignore
      return import.meta.env.VITE_BACKEND_URL;
    }
    if ((window as any).__BACKEND_URL__) {
      return (window as any).__BACKEND_URL__;
    }
    return 'http://localhost:7860';
  }

  /**
   * Get LightRAG URL for knowledge graph queries
   */
  private getLightRAGUrl(): string {
    // @ts-ignore
    if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_LIGHTRAG_URL) {
      // @ts-ignore
      return import.meta.env.VITE_LIGHTRAG_URL;
    }
    if ((window as any).__LIGHTRAG_URL__) {
      return (window as any).__LIGHTRAG_URL__;
    }
    return 'http://localhost:9621';
  }

  /**
   * Connect to voice server
   */
  public async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected) return;

    this.isConnecting = true;
    this.setVoiceState('thinking');
    this.setCloseButtonEnabled(false); // Disable close until WebSocket is connected (or fails)

    this.addTerminalMessage('voice.scanner.connect();', 'command');
    this.addTerminalMessage('Establishing secure connection...', 'regular');

    try {
      const backendUrl = this.getBackendUrl();
      this.log(`Connecting to ${backendUrl}...`);

      this.transport = new WebSocketTransport();
      const config: RTVIClientOptions = {
        transport: this.transport,
        params: {
          baseUrl: backendUrl,
          endpoints: { connect: '/connect' },
          requestData: {
            ...(this.selectedPersonaId ? { persona_id: this.selectedPersonaId } : {}),
          },
        },
        enableMic: true,
        enableCam: false,
        callbacks: {
          onConnected: () => {
            this.isConnecting = false;
            this.isConnected = true;
            this.setCloseButtonEnabled(true); // WebSocket connected; allow close
            this.log('Connected successfully!');
            this.setVoiceState('listening');
            this.updateConnectionUI(true);
            this.addTerminalMessage('Connection established. Voice active.', 'success');
            this.showNotification('CONNECTION ESTABLISHED');

            // Premium connection experience: crystal chime + orb bloom
            this.playCrystalChime();
            this.triggerConnectionBloom();

            // Set up bot player analyser after connection (with delay to ensure player is ready)
            setTimeout(() => {
              this.setupBotPlayerAnalyser();
            }, 500);
          },
          onDisconnected: () => {
            this.isConnecting = false;
            this.isConnected = false;
            this.rtviClient = null;
            this.setCloseButtonEnabled(true);
            this.log('Disconnected');
            this.setVoiceState('idle');
            // Stop all subtitle activity
            this.clearSubtitleDisplayTimers();
            this.subtitleWordBuffer = [];
            this.subtitleDisplayedWords = [];
            this.subtitleAudioStartTime = 0;
            if (this.subtitleClearTimeout) {
              clearTimeout(this.subtitleClearTimeout);
              this.subtitleClearTimeout = null;
            }
            this.liveSubtitle?.classList.remove('visible');
            // Do not clear close-mode here: when user clicked Close we keep Restart | Peek visible.
            // When server/error disconnects, we're not in close-mode so updateConnectionUI(false) will show connect area.
            this.updateConnectionUI(false);
            this.stopAudioVisualization();
            this.startIdleBlobAnimation(); // Keep wave animating in idle state
            this.addTerminalMessage('Connection terminated.', 'regular');
          },
          onBotReady: () => {
            this.log(`Bot ready`);
            this.setupMediaTracks();
            this.setupBotPlayerAnalyser(); // Set up real frequency analysis for bot audio
            this.addTerminalMessage('Voice AI initialized and ready.', 'success');
          },
          onUserTranscript: (data) => {
            if (data.final) {
              this.log(`You: ${data.text}`);
              // Finalize previous bot bubble before adding user message
              this.finalizeBotBubble();
              this.streamingTextActiveForSubtitle = false;  // Reset for next turn
              this.addTranscript(data.text, true);
              // Store query and reset accumulated answer for new turn
              this.lastUserQuery = data.text;
              this.accumulatedBotAnswer = '';
              // Clear A2UI from previous turn when new user query starts
              this.clearA2UI();
              this.hideA2UIPanel();
              // Stop any ongoing graph node cycling
              if ((window as any).KnowledgeGraph?.stopCycle) {
                (window as any).KnowledgeGraph.stopCycle();
              }
            }
          },
          onBotTranscript: (data) => {
            this.log(`Bot: ${data.text}`);
            // [SUBTITLE-SYNC] Disabled: subtitle & transcript now driven by streaming_text
            // from SubtitleSyncProcessor for audio-synced subtitles.
            // if (!this.streamingBubble && !this.skipNextBotTranscriptAdd) {
            //   this.addBotTranscriptWithTypewriter(data.text);
            // }
            // if (this.skipNextBotTranscriptAdd) this.skipNextBotTranscriptAdd = false;
            // Accumulate bot answer chunks (for graph highlight)
            this.accumulatedBotAnswer += ' ' + data.text;
            // Debounce highlight call - wait 500ms after last chunk
            if (this.graphHighlightTimeout) {
              clearTimeout(this.graphHighlightTimeout);
            }
            this.graphHighlightTimeout = setTimeout(() => {
              this.highlightGraphKeywords(this.lastUserQuery, this.accumulatedBotAnswer.trim());
            }, 500);
          },
          onError: (error) => {
            this.setCloseButtonEnabled(true); // Re-enable close on error
            const errorMsg = typeof error === 'object' ? JSON.stringify(error) : String(error);
            this.log(`Error: ${errorMsg}`);
            this.addTerminalMessage(errorMsg, 'error');
            console.error('RTVI Error:', error);
          },
          onServerMessage: (message) => {
            try {
              let messageData = null;
              let messageType = null;

              // Parse message structure (flexible - handles multiple formats)
              if (message && message.data) {
                messageType = message.data.message_type;
                messageData = message.data;
              } else if (message && message.message_type) {
                messageType = message.message_type;
                messageData = message;
              } else if (message && message.type === 'server-message' && message.data) {
                messageType = message.data.message_type;
                messageData = message.data;
              }

              // Handle different message types
              switch (messageType) {
                case 'hybrid_emotion_detected':
                  this.updateHybridEmotionDisplay(messageData);
                  this.updateEmotionReactiveUI(messageData);
                  break;
                case 'emotion_detected':
                  this.updateEmotionDisplay(messageData);
                  this.updateEmotionReactiveUI(messageData);
                  break;
                case 'tone_switched':
                  this.updateToneDisplay(messageData.new_tone);
                  break;
                case 'streaming_text':
                  this.handleStreamingText(messageData);
                  break;
                case 'subtitle_chunk':
                  this.handleSubtitleChunk(messageData);
                  break;
                case 'visual_hint':
                  this.handleVisualHint(messageData);
                  break;
                case 'a2ui_update':
                  if (isA2UIUpdate(messageData)) {
                    this.handleA2UIUpdate(messageData);
                  } else {
                    console.warn('[A2UI] Invalid update format');
                  }
                  break;
              }
            } catch (e) {
              console.error('[ServerMessage] Error:', e);
            }
          },
        },
      };

      this.rtviClient = new RTVIClient(config);
      this.setupTrackListeners();

      await this.rtviClient.initDevices();
      await this.rtviClient.connect();

    } catch (error) {
      this.isConnecting = false;
      this.setCloseButtonEnabled(true); // Re-enable close when connection fails
      this.log(`Connection failed: ${(error as Error).message}`);
      this.addTerminalMessage(`Connection failed: ${(error as Error).message}`, 'error');
      this.setVoiceState('idle');
      this.updateConnectionUI(false);

      if (this.rtviClient) {
        try {
          await this.rtviClient.disconnect();
        } catch (e) {}
        this.rtviClient = null;
      }
    }
  }

  /**
   * Disconnect from voice server
   */
  public async disconnect(): Promise<void> {
    if (!this.rtviClient && !this.isConnecting) return;

    this.log('Disconnecting...');
    this.addTerminalMessage('voice.scanner.disconnect();', 'command');

    try {
      if (this.rtviClient) {
        await this.rtviClient.disconnect();
        this.rtviClient = null;
      }

      // Clean up audio
      if (this.botAudio.srcObject && "getAudioTracks" in this.botAudio.srcObject) {
        this.botAudio.srcObject.getAudioTracks().forEach((track) => track.stop());
        this.botAudio.srcObject = null;
      }

      // Clean up audio context
      if (this.audioContext) {
        await this.audioContext.close();
        this.audioContext = null;
        this.analyser = null;
        this.inputAnalyser = null;
        this.dataArray = null;
        this.inputDataArray = null;
      }

      // Reset Gemini blob state
      this.smoothedAmplitude = 0;
      this.targetAmplitude = 0;

      this.stopAudioVisualization();
      this.startIdleBlobAnimation(); // Restart wave animation (idle) so it keeps running after close/restart

      // Clear A2UI display
      this.clearA2UI();

      // Reset subtitle state
      this.botIsSpeaking = false;
      this.subtitleWordCount = 0;
      this.subtitleClearOnNextSentence = false;

      // Do NOT clear card data on disconnect (X): keep conversation history visible in all cards.
      // Card data is only cleared when user clicks Restart (resetAllCardsData).

      this.isConnecting = false;
      this.isConnected = false;
      this.setVoiceState('idle');
      this.updateConnectionUI(false);
      this.log('Disconnected successfully');

    } catch (error) {
      this.log(`Disconnect error: ${(error as Error).message}`);
      this.isConnecting = false;
      this.isConnected = false;
      this.setVoiceState('idle');
      this.updateConnectionUI(false);
    }
  }

  // ===== STREAMING TRANSCRIPT METHODS =====

  /**
   * Handle streaming text events — buffer words with PTS timing, display synced with audio.
   *
   * Words arrive from SubtitleSyncProcessor as a burst BEFORE audio plays.
   * Each word includes pts_offset (seconds from first word in utterance).
   * Words are buffered and released when BotStartedSpeaking fires.
   */
  private handleStreamingText(data: {
    text: string;
    is_final: boolean;
    sequence_id: number;
    utterance_id: string;
    pts_offset?: number;
    timestamp: number;
  }): void {
    // Handle final marker
    if (data.is_final) {
      this.finalizeCurrentStreamingBubble();
      return;
    }

    // New utterance — reset state
    if (data.utterance_id !== this.currentUtteranceId) {
      if (this.streamingBubble) {
        this.finalizeCurrentStreamingBubble();
      }
      this.currentUtteranceId = data.utterance_id;
      this.streamingTextActiveForSubtitle = true;
      this.createStreamingBubble();

      // Reset subtitle timing state
      this.clearSubtitleDisplayTimers();
      this.subtitleWordBuffer = [];
      this.subtitleDisplayedWords = [];
      // If bot is already speaking (BotStartedSpeaking fired before first streaming_text),
      // keep audio start time so words schedule immediately instead of buffering forever.
      if (this.botIsSpeaking) {
        this.subtitleAudioStartTime = performance.now();
      } else {
        this.subtitleAudioStartTime = 0;
      }
    }

    if (!data.text || !data.text.trim()) return;
    const word = data.text.trim();
    const ptsOffset = data.pts_offset ?? 0;

    // Add word to transcript bubble immediately (transcript is a log, no timing needed)
    this.addWordToTranscriptBubble(word, data.sequence_id);

    // Buffer word for timed subtitle display
    if (this.subtitleAudioStartTime > 0) {
      // Audio already playing — schedule this word immediately
      this.scheduleSubtitleWord(word, ptsOffset);
    } else {
      // Audio not yet playing — buffer for later
      this.subtitleWordBuffer.push({ word, seq: data.sequence_id, ptsOffset });
      // Safety: if BotStartedSpeaking never fires (e.g. event lost), flush after 2s
      if (!this.subtitleBufferFlushTimer) {
        this.subtitleBufferFlushTimer = setTimeout(() => {
          this.subtitleBufferFlushTimer = null;
          if (this.subtitleWordBuffer.length > 0 && this.subtitleAudioStartTime === 0) {
            console.log('[ST] Safety flush: BotStartedSpeaking not received, flushing buffered words');
            this.subtitleAudioStartTime = performance.now();
            this.flushSubtitleWordBuffer();
          }
        }, 2000);
      }
    }
  }

  /**
   * Handle subtitle_chunk from Chatterbox TTS — full sentence with exact audio duration.
   * Words are revealed one-by-one timed to audio_duration / word_count.
   */
  private handleSubtitleChunk(data: {
    text: string;
    audio_duration: number;
    timestamp: number;
  }): void {
    if (!data.text || !data.text.trim()) return;
    const words = data.text.trim().split(/\s+/);
    if (words.length === 0) return;

    const interval = data.audio_duration / words.length;

    // Convert to buffered words with evenly-spaced PTS offsets
    for (let i = 0; i < words.length; i++) {
      const ptsOffset = i * interval;
      if (this.subtitleAudioStartTime > 0) {
        this.scheduleSubtitleWord(words[i], ptsOffset);
      } else {
        this.subtitleWordBuffer.push({ word: words[i], seq: i + 1, ptsOffset });
      }
    }

    // Add full text to transcript bubble
    if (!this.streamingBubble) {
      this.createStreamingBubble();
    }
    for (let i = 0; i < words.length; i++) {
      this.addWordToTranscriptBubble(words[i], i + 1);
    }

    // Safety flush if BotStartedSpeaking doesn't fire
    if (this.subtitleAudioStartTime === 0 && !this.subtitleBufferFlushTimer) {
      this.subtitleBufferFlushTimer = setTimeout(() => {
        this.subtitleBufferFlushTimer = null;
        if (this.subtitleWordBuffer.length > 0 && this.subtitleAudioStartTime === 0) {
          console.log('[ST] Safety flush: BotStartedSpeaking not received, flushing subtitle_chunk');
          this.subtitleAudioStartTime = performance.now();
          this.flushSubtitleWordBuffer();
        }
      }, 2000);
    }
  }

  /**
   * Flush buffered subtitle words — called when BotStartedSpeaking fires.
   * Schedules each word's display at its PTS offset from now.
   */
  private flushSubtitleWordBuffer(): void {
    for (const entry of this.subtitleWordBuffer) {
      this.scheduleSubtitleWord(entry.word, entry.ptsOffset);
    }
    this.subtitleWordBuffer = [];
  }

  /**
   * Schedule a single word to appear in the subtitle at its PTS time.
   */
  private scheduleSubtitleWord(word: string, ptsOffset: number): void {
    const elapsed = (performance.now() - this.subtitleAudioStartTime) / 1000;
    const delay = Math.max(0, ptsOffset - elapsed);

    if (delay < 0.05) {
      // Show immediately
      this.displaySubtitleWord(word);
    } else {
      const timer = setTimeout(() => {
        this.displaySubtitleWord(word);
      }, delay * 1000);
      this.subtitleDisplayTimers.push(timer);
    }
  }

  /**
   * Display a word in the live subtitle (append to rolling text).
   */
  private displaySubtitleWord(word: string): void {
    this.subtitleDisplayedWords.push(word);

    if (this.liveSubtitle && this.liveSubtitleText) {
      const fullText = this.subtitleDisplayedWords.join(' ');
      const maxChars = window.innerWidth <= VoiceScannerApp.SUBTITLE_MOBILE_BREAKPOINT_PX
        ? VoiceScannerApp.MAX_SUBTITLE_LINE_CHARS_MOBILE
        : VoiceScannerApp.MAX_SUBTITLE_LINE_CHARS;
      const lines = this.textToLines(fullText, maxChars);
      const maxVisible = VoiceScannerApp.MAX_SUBTITLE_LINES_VISIBLE;
      const visibleLines = lines.slice(-maxVisible);

      // Render each line with individual word spans; latest word gets glow
      this.liveSubtitleText.innerHTML = '';
      const totalWordCount = this.subtitleDisplayedWords.length;
      let wordIndex = 0;
      // Calculate how many words are in lines before the visible ones
      const allLines = this.textToLines(fullText, maxChars);
      const hiddenLines = allLines.slice(0, allLines.length - visibleLines.length);
      let hiddenWordCount = 0;
      for (const hl of hiddenLines) {
        hiddenWordCount += hl.split(/\s+/).filter(Boolean).length;
      }
      wordIndex = hiddenWordCount;

      for (const line of visibleLines) {
        const lineEl = document.createElement('span');
        lineEl.className = 'subtitle-line';
        const words = line.split(/\s+/).filter(Boolean);
        for (let i = 0; i < words.length; i++) {
          if (i > 0) lineEl.appendChild(document.createTextNode(' '));
          const wordSpan = document.createElement('span');
          wordSpan.className = 'subtitle-word';
          wordSpan.textContent = words[i];
          wordIndex++;
          if (wordIndex === totalWordCount) {
            // This is the latest word — give it the active glow
            wordSpan.classList.add('subtitle-word-active');
          }
          lineEl.appendChild(wordSpan);
        }
        this.liveSubtitleText.appendChild(lineEl);
      }

      this.liveSubtitle.classList.remove('user');
      this.liveSubtitle.classList.add('bot', 'visible');

      // Clear any pending hide timer while words are still being displayed
      if (this.subtitleClearTimeout) {
        clearTimeout(this.subtitleClearTimeout);
        this.subtitleClearTimeout = null;
      }
    }
  }

  /**
   * Clear all pending subtitle display timers.
   */
  private clearSubtitleDisplayTimers(): void {
    for (const t of this.subtitleDisplayTimers) clearTimeout(t);
    this.subtitleDisplayTimers = [];
    if (this.subtitleBufferFlushTimer) {
      clearTimeout(this.subtitleBufferFlushTimer);
      this.subtitleBufferFlushTimer = null;
    }
  }

  /**
   * Create a new streaming transcript bubble (log-style, no timing).
   */
  private createStreamingBubble(): void {
    if (!this.transcriptList) return;

    this.welcomeMessage?.classList.add('hidden');

    this.streamingWords = [];
    for (const t of this.subtitleRevealTimeouts) clearTimeout(t);
    this.subtitleRevealTimeouts = [];
    this.lastScheduledSubtitleLines = [];
    if (this.liveSubtitleText) {
      this.liveSubtitleText.textContent = '';
    }

    this.streamingBubble = document.createElement('div');
    this.streamingBubble.className = 'transcript-line transcript-line-bot streaming';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'transcript-time';
    timeSpan.textContent = this.formatTranscriptTime() + ' ';

    const textContainer = document.createElement('span');
    textContainer.className = 'transcript-message streaming-text';

    this.streamingBubble.appendChild(timeSpan);
    this.streamingBubble.appendChild(textContainer);
    this.transcriptList.appendChild(this.streamingBubble);
    this.transcriptList.scrollTop = this.transcriptList.scrollHeight;
  }

  /**
   * Add a word to the transcript bubble (immediate, no timing).
   */
  private addWordToTranscriptBubble(word: string, sequenceId: number): void {
    if (!this.streamingBubble) return;

    const textContainer = this.streamingBubble.querySelector('.transcript-message.streaming-text');
    if (!textContainer) return;

    const wordSpan = document.createElement('span');
    wordSpan.className = 'streaming-word';
    wordSpan.textContent = word + ' ';
    wordSpan.style.animationDelay = `${(sequenceId % 10) * 30}ms`;

    textContainer.appendChild(wordSpan);
    this.streamingWords.push(word);

    if (this.transcriptList) {
      this.transcriptList.scrollTop = this.transcriptList.scrollHeight;
    }
  }

  /**
   * Finalize the current streaming bubble.
   * Note: does NOT clear subtitle display timers — words may still be scheduled
   * for display (is_final arrives when TTS finishes generating, before audio ends).
   * Timers are only cleared when a new utterance starts.
   */
  private finalizeCurrentStreamingBubble(): void {
    if (this.streamingBubble) {
      this.streamingBubble.classList.remove('streaming');
      this.streamingBubble.classList.add('finalized');

      const textContainer = this.streamingBubble.querySelector('.transcript-message.streaming-text');
      if (textContainer && this.streamingWords.length > 0) {
        textContainer.innerHTML = '';
        textContainer.textContent = this.streamingWords.join(' ');
      }
    }
    this.streamingBubble = null;
    this.currentUtteranceId = null;
    this.streamingWords = [];
    this.subtitleWordBuffer = [];
    // Don't clear subtitleDisplayedWords or timers — words are still being displayed
    this.skipNextBotTranscriptAdd = true;
  }

  // ===== VISUAL CARD METHODS =====

  /**
   * Handle visual hint events to display dynamic cards
   */
  private handleVisualHint(data: {
    hint_type: string;
    content_type: string;
    content: any;
    confidence: number;
    trigger_text: string;
    timestamp: number;
  }): void {
    // Remove existing card if present
    this.dismissVisualCard();

    // Create appropriate card based on hint_type
    switch (data.hint_type) {
      case 'greeting_animation':
        this.showGreetingAnimation();
        break;
      case 'contact_card':
        this.showContactCard(data.content);
        break;
      case 'service_card':
        this.showServiceCard(data.content);
        break;
      case 'pricing_card':
        this.showPricingCard(data.content);
        break;
      case 'project_card':
        this.showProjectCard(data.content);
        break;
      case 'project_detail_visualizing_intelligence':
        this.showProjectDetailCard('visualizing_intelligence');
        break;
      case 'project_detail_natural_conversations':
        this.showProjectDetailCard('natural_conversations');
        break;
      case 'project_detail_agentic_intake':
        this.showProjectDetailCard('agentic_intake');
        break;
      case 'project_detail_ai_first_bank':
        this.showProjectDetailCard('ai_first_bank');
        break;
      case 'expertise_card':
        this.showExpertiseCard(data.content);
        break;
      case 'company_card':
        this.showCompanyCard(data.content);
        break;
      case 'next_steps_card':
        this.showNextStepsCard(data.content);
        break;
      case 'location_card':
        this.showLocationCard(data.content);
        break;
    }

    // Log to terminal
    this.addTerminalMessage(`visual.hint({ type: '${data.hint_type}' });`, 'command');
  }

  /**
   * Show greeting animation on orb and display welcome card
   */
  private showGreetingAnimation(): void {
    // Trigger greeting animation on the orb
    this.orbContainer?.classList.add('greeting-pulse');

    // Show welcome visual overlay
    const card = this.createVisualCard('greeting-card');
    card.innerHTML = `
      <div class="greeting-animation">
        <div class="greeting-wave">
          <span class="wave-emoji">👋</span>
        </div>
        <div class="greeting-text">WELCOME</div>
      </div>
    `;
    this.displayVisualCard(card, 3000); // Auto-dismiss after 3s

    setTimeout(() => {
      this.orbContainer?.classList.remove('greeting-pulse');
    }, 3000);
  }

  /**
   * Show contact information card with full details
   */
  private showContactCard(_content: { email?: string; phone?: string }): void {
    const card = this.createVisualCard('contact-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
          <polyline points="22,6 12,13 2,6"/>
        </svg>
        <span>GET IN TOUCH</span>
      </div>
      <div class="visual-card-content">
        <div class="contact-grid">
          <div class="contact-method">
            <div class="contact-icon">📧</div>
            <div class="contact-details">
              <div class="contact-label">EMAIL</div>
              <div class="contact-value">contact@yourcompany.com</div>
            </div>
          </div>
          <div class="contact-method">
            <div class="contact-icon">📞</div>
            <div class="contact-details">
              <div class="contact-label">PHONE</div>
              <div class="contact-value">+1 (000) 000-0000</div>
            </div>
          </div>
          <div class="contact-method">
            <div class="contact-icon">🌐</div>
            <div class="contact-details">
              <div class="contact-label">WEBSITE</div>
              <div class="contact-value">yourcompany.com</div>
            </div>
          </div>
          <div class="contact-method">
            <div class="contact-icon">💼</div>
            <div class="contact-details">
              <div class="contact-label">LINKEDIN</div>
              <div class="contact-value">@yourcompany</div>
            </div>
          </div>
        </div>
        <div class="contact-response-note">
          <span class="note-icon">⚡</span>
          <span>We respond within 24 business hours</span>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 12000);
  }

  /**
   * Show services card with detailed four service pillars
   */
  private showServiceCard(_content: { services?: string[]; description?: string }): void {
    const card = this.createVisualCard('service-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <polygon points="10,8 16,12 10,16 10,8"/>
        </svg>
        <span>OUR SERVICES</span>
      </div>
      <div class="visual-card-content">
        <div class="services-detailed">
          <div class="service-detail-item">
            <div class="service-detail-header">
              <span class="service-emoji">👤</span>
              <span class="service-title">HUMAN</span>
            </div>
            <div class="service-detail-desc">User research, product design, voice & emotion design, brand identity</div>
            <div class="service-detail-outcome">
              <span class="outcome-label">Outcome:</span> Coherent, emotionally resonant experiences
            </div>
          </div>
          <div class="service-detail-item">
            <div class="service-detail-header">
              <span class="service-emoji">🧠</span>
              <span class="service-title">INTELLIGENCE</span>
            </div>
            <div class="service-detail-desc">Agentic AI, NLP engines, AI synthesis pipelines, conversational systems</div>
            <div class="service-detail-outcome">
              <span class="outcome-label">Outcome:</span> Systems that understand intent & respond in context
            </div>
          </div>
          <div class="service-detail-item">
            <div class="service-detail-header">
              <span class="service-emoji">📚</span>
              <span class="service-title">MEMORY</span>
            </div>
            <div class="service-detail-desc">Knowledge graphs, RAG pipelines, conversation analysis, privacy guardrails</div>
            <div class="service-detail-outcome">
              <span class="outcome-label">Outcome:</span> Reliable memory layer with security & privacy
            </div>
          </div>
          <div class="service-detail-item">
            <div class="service-detail-header">
              <span class="service-emoji">☁️</span>
              <span class="service-title">CLOUD</span>
            </div>
            <div class="service-detail-desc">Infrastructure security, compliance, DevOps, CI/CD for AI workloads</div>
            <div class="service-detail-outcome">
              <span class="outcome-label">Outcome:</span> Ship fast while staying secure & compliant
            </div>
          </div>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 15000);
  }

  /**
   * Show pricing card with detailed engagement models
   */
  private showPricingCard(_content: { amounts?: string[] }): void {
    const card = this.createVisualCard('pricing-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="1" x2="12" y2="23"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
        <span>ENGAGEMENT MODELS</span>
      </div>
      <div class="visual-card-content">
        <div class="engagement-models">
          <div class="engagement-item">
            <div class="engagement-icon">🔍</div>
            <div class="engagement-info">
              <div class="engagement-name">DISCOVERY & STRATEGY</div>
              <div class="engagement-duration">2-4 weeks</div>
              <div class="engagement-desc">Understand problems & define clear path forward</div>
            </div>
          </div>
          <div class="engagement-item">
            <div class="engagement-icon">⚡</div>
            <div class="engagement-info">
              <div class="engagement-name">DESIGN SPRINTS</div>
              <div class="engagement-duration">1-2 weeks</div>
              <div class="engagement-desc">Solve specific problems or validate approaches</div>
            </div>
          </div>
          <div class="engagement-item">
            <div class="engagement-icon">🚀</div>
            <div class="engagement-info">
              <div class="engagement-name">PRODUCT DEVELOPMENT</div>
              <div class="engagement-duration">2-6 months+</div>
              <div class="engagement-desc">Design & build AI features, products, or platforms</div>
            </div>
          </div>
          <div class="engagement-item">
            <div class="engagement-icon">🔄</div>
            <div class="engagement-info">
              <div class="engagement-name">TIME & MATERIALS</div>
              <div class="engagement-duration">Flexible</div>
              <div class="engagement-desc">Scale up or down based on your priorities</div>
            </div>
          </div>
        </div>
        <div class="pricing-footer">
          <span class="footer-note">We work with startups to enterprises with realistic budgets</span>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 15000);
  }

  /**
   * Show project card with detailed case studies
   */
  private showProjectCard(_content: { mentioned?: boolean }): void {
    const card = this.createVisualCard('project-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span>CASE STUDIES</span>
      </div>
      <div class="visual-card-content">
        <div class="project-showcase">
          <div class="project-case">
            <div class="case-header">
              <span class="case-icon">🎨</span>
              <div class="case-title-wrap">
                <div class="case-title">Visualizing Intelligence</div>
                <div class="case-industry">AI & Technology Studio</div>
              </div>
            </div>
            <div class="case-challenge">Brand & web to communicate complex AI work</div>
            <div class="case-outcome">Cohesive identity enabling confident stakeholder conversations</div>
          </div>
          <div class="project-case">
            <div class="case-header">
              <span class="case-icon">💬</span>
              <div class="case-title-wrap">
                <div class="case-title">Natural Conversations</div>
                <div class="case-industry">Data Platforms & Analytics</div>
              </div>
            </div>
            <div class="case-challenge">Users struggling with dashboards & query languages</div>
            <div class="case-outcome">Plain language data queries → faster decision-making</div>
          </div>
          <div class="project-case">
            <div class="case-header">
              <span class="case-icon">🤖</span>
              <div class="case-title-wrap">
                <div class="case-title">Agentic Intake Coordinator</div>
                <div class="case-industry">Operations & Workflows</div>
              </div>
            </div>
            <div class="case-challenge">Manual back-and-forth intake processes</div>
            <div class="case-outcome">Voice AI streamlines intake with cleaner data</div>
          </div>
          <div class="project-case coming-soon">
            <div class="case-header">
              <span class="case-icon">🏦</span>
              <div class="case-title-wrap">
                <div class="case-title">AI First Bank</div>
                <div class="case-industry">Financial Services</div>
              </div>
            </div>
            <div class="case-challenge">Rigid, transactional banking experiences</div>
            <div class="case-badge">COMING SOON</div>
          </div>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 18000);
  }

  /**
   * Show detailed project card for a specific case study
   */
  private showProjectDetailCard(projectId: string): void {
    const projects: Record<string, {
      title: string;
      industry: string;
      badge?: string;
      challenge: string;
      solution: string;
      outcome: string;
      deliverables: string[];
      signals: string[];
      icon: string;
    }> = {
      visualizing_intelligence: {
        title: 'Visualizing Intelligence',
        industry: 'AI & Technology Studio',
        challenge: 'Communicate complex AI work in a way that feels inspiring, clear, and trustworthy.',
        solution: 'Strategy, visual identity, and a web experience that makes the story easy to grasp at a glance.',
        outcome: 'Cohesive brand and site that unlocks confident conversations with partners and stakeholders.',
        deliverables: ['Strategy', 'Identity System', 'Web Experience'],
        signals: ['Narrative Clarity', 'Trust & Credibility', 'Stakeholder Confidence'],
        icon: '🎨',
      },
      natural_conversations: {
        title: 'Natural Conversations with Data',
        industry: 'Data Platforms & Analytics',
        challenge: 'Users struggled with dashboards and query languages to access insights.',
        solution: 'Natural language interface with intent understanding, guided questions, and clear answer formats.',
        outcome: 'Faster decision-making and broader adoption by non-technical users.',
        deliverables: ['Conversational UI', 'Intent Mapping', 'Answer Cards'],
        signals: ['Plain Language', 'Guided Queries', 'Faster Insights'],
        icon: '💬',
      },
      agentic_intake: {
        title: 'Agentic Intake Coordinator',
        industry: 'Operations & Workflows',
        challenge: 'Manual back-and-forth intake created slow, inconsistent handoffs.',
        solution: 'Conversational AI that listens, clarifies, and structures inputs for downstream teams.',
        outcome: 'Faster intake, smoother user experience, and cleaner structured data.',
        deliverables: ['Voice Flow', 'Clarification Logic', 'Structured Output'],
        signals: ['Automation', 'Clarity', 'Structured Data'],
        icon: '🤖',
      },
      ai_first_bank: {
        title: 'AI First Bank',
        industry: 'Financial Services',
        badge: 'COMING SOON',
        challenge: 'Traditional banking feels rigid, transactional, and disconnected from real goals.',
        solution: 'Conversational finance experience with context, personalization, and proactive guidance.',
        outcome: 'A partner-like banking experience that sets a new bar for AI in finance.',
        deliverables: ['Conversational Journeys', 'Context Memory', 'Proactive Insights'],
        signals: ['Personalized', 'Proactive', 'Trusted'],
        icon: '🏦',
      },
    };

    const project = projects[projectId] ?? projects.visualizing_intelligence;
    const card = this.createVisualCard('project-detail-card');

    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span>PROJECT DETAILS</span>
      </div>
      <div class="visual-card-content">
        <div class="project-detail-hero">
          <div class="project-detail-icon">${project.icon}</div>
          <div class="project-detail-main">
            <div class="project-detail-title">${project.title}</div>
            <div class="project-detail-industry">${project.industry}</div>
          </div>
          ${project.badge ? `<div class="project-detail-badge">${project.badge}</div>` : ''}
        </div>

        <div class="project-detail-sections">
          <div class="detail-section">
            <div class="detail-label">Challenge</div>
            <div class="detail-text">${project.challenge}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Solution</div>
            <div class="detail-text">${project.solution}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Outcome</div>
            <div class="detail-text detail-outcome">${project.outcome}</div>
          </div>
        </div>

        <div class="project-detail-grid">
          <div class="detail-panel">
            <div class="panel-title">Deliverables</div>
            <div class="panel-list">
              ${project.deliverables.map((item) => `<span class="panel-pill">${item}</span>`).join('')}
            </div>
          </div>
          <div class="detail-panel">
            <div class="panel-title">Key Signals</div>
            <div class="panel-list">
              ${project.signals.map((item) => `<span class="panel-pill accent">${item}</span>`).join('')}
            </div>
          </div>
        </div>

        <div class="project-detail-flow">
          <div class="flow-step">Discovery</div>
          <div class="flow-line"></div>
          <div class="flow-step">Design</div>
          <div class="flow-line"></div>
          <div class="flow-step">Delivery</div>
        </div>
      </div>
    `;

    this.displayVisualCard(card, 20000);
  }

  /**
   * Show expertise card with technical capabilities
   */
  private showExpertiseCard(_content: Record<string, unknown>): void {
    const card = this.createVisualCard('expertise-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"/>
        </svg>
        <span>EXPERTISE AREAS</span>
      </div>
      <div class="visual-card-content">
        <div class="expertise-grid">
          <div class="expertise-item">
            <div class="expertise-icon">🎙️</div>
            <div class="expertise-name">Voice AI & Conversational</div>
            <div class="expertise-desc">Natural dialogues, voice tone, emotional awareness</div>
          </div>
          <div class="expertise-item">
            <div class="expertise-icon">🤖</div>
            <div class="expertise-name">Agentic AI & Orchestration</div>
            <div class="expertise-desc">Multi-capability systems for complex workflows</div>
          </div>
          <div class="expertise-item">
            <div class="expertise-icon">📊</div>
            <div class="expertise-name">RAG & Context Engineering</div>
            <div class="expertise-desc">Grounding AI in the right information at the right time</div>
          </div>
          <div class="expertise-item">
            <div class="expertise-icon">💭</div>
            <div class="expertise-name">Natural Language Processing</div>
            <div class="expertise-desc">Intent recognition & contextual response generation</div>
          </div>
          <div class="expertise-item">
            <div class="expertise-icon">✨</div>
            <div class="expertise-name">AI-First Product Design</div>
            <div class="expertise-desc">UX research & design for AI-native experiences</div>
          </div>
          <div class="expertise-item">
            <div class="expertise-icon">🔗</div>
            <div class="expertise-name">Knowledge Graphs & Memory</div>
            <div class="expertise-desc">Consistent info with privacy guardrails</div>
          </div>
        </div>
        <div class="expertise-footer">
          <span>85+ years combined team experience</span>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 15000);
  }

  /**
   * Show company overview card
   */
  private showCompanyCard(_content: Record<string, unknown>): void {
    const card = this.createVisualCard('company-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9,22 9,12 15,12 15,22"/>
        </svg>
        <span>ABOUT US</span>
      </div>
      <div class="visual-card-content">
        <div class="company-overview">
          <div class="company-tagline">AI-Accelerated Product Studio</div>
          <div class="company-desc">
            Reimagining intelligence through research, design, and technology. We help companies make advanced technologies usable, legible, and effective inside real products.
          </div>
          <div class="company-stats">
            <div class="stat-item">
              <div class="stat-value">85+</div>
              <div class="stat-label">Years Combined Experience</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">SF Bay</div>
              <div class="stat-label">Area Based</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">E2E</div>
              <div class="stat-label">Research to Deploy</div>
            </div>
          </div>
          <div class="company-clients">
            <span class="clients-label">Clients:</span> Early-stage startups to large enterprises
          </div>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 12000);
  }

  /**
   * Show next steps card for engagement flow
   */
  private showNextStepsCard(_content: Record<string, unknown>): void {
    const card = this.createVisualCard('next-steps-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9,18 15,12 9,6"/>
        </svg>
        <span>WHAT HAPPENS NEXT</span>
      </div>
      <div class="visual-card-content">
        <div class="steps-timeline">
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-info">
              <div class="step-title">Initial Response</div>
              <div class="step-desc">We respond within 1-2 business days</div>
            </div>
          </div>
          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-info">
              <div class="step-title">Discovery Call</div>
              <div class="step-desc">30-45 min to understand goals, constraints & timeline</div>
            </div>
          </div>
          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-info">
              <div class="step-title">Tailored Proposal</div>
              <div class="step-desc">Scope, approach, timeline & pricing</div>
            </div>
          </div>
          <div class="step-item">
            <div class="step-number">4</div>
            <div class="step-info">
              <div class="step-title">Kickoff</div>
              <div class="step-desc">Align on goals & start deep work within 1-2 weeks</div>
            </div>
          </div>
        </div>
        <div class="steps-cta">
          Ready to start? Let's talk!
        </div>
      </div>
    `;
    this.displayVisualCard(card, 15000);
  }

  /**
   * Show location card with office details
   */
  private showLocationCard(_content: Record<string, unknown>): void {
    const card = this.createVisualCard('location-card');
    card.innerHTML = `
      <div class="visual-card-header">
        <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
        <span>VISIT US</span>
      </div>
      <div class="visual-card-content">
        <div class="location-details">
          <div class="location-address">
            <div class="address-icon">🏢</div>
            <div class="address-text">
              <div class="address-line">Your Street Address</div>
              <div class="address-line">Your City, State ZIP</div>
            </div>
          </div>
          <div class="location-region">
            <span class="region-badge">SF Bay Area</span>
            <span class="region-note">Silicon Valley</span>
          </div>
          <div class="location-hours">
            <div class="hours-icon">🕐</div>
            <div class="hours-text">
              <div class="hours-label">Business Hours (PST)</div>
              <div class="hours-note">In-person meetings by appointment</div>
            </div>
          </div>
        </div>
      </div>
    `;
    this.displayVisualCard(card, 10000);
  }

  /**
   * Create a visual card element
   */
  private createVisualCard(className: string): HTMLElement {
    const card = document.createElement('div');
    card.className = `visual-card ${className}`;
    return card;
  }

  /**
   * Display a visual card with optional auto-dismiss
   */
  private displayVisualCard(card: HTMLElement, autoDismissMs?: number): void {
    // Get or create visual cards container
    if (!this.visualCardsContainer) {
      this.visualCardsContainer = document.getElementById('visual-cards-container');
      if (!this.visualCardsContainer) {
        this.visualCardsContainer = document.createElement('div');
        this.visualCardsContainer.id = 'visual-cards-container';
        document.querySelector('.interface-container')?.appendChild(this.visualCardsContainer);
      }
    }

    // Add close button to card (except greeting cards)
    if (!card.classList.contains('greeting-card')) {
      const closeBtn = document.createElement('button');
      closeBtn.className = 'card-close';
      closeBtn.innerHTML = '×';
      closeBtn.onclick = (e) => {
        e.stopPropagation();
        this.dismissVisualCard();
      };
      card.appendChild(closeBtn);
    }

    this.visualCardsContainer.appendChild(card);
    this.activeVisualCard = card;

    // Force a reflow before adding the visible class
    void card.offsetWidth;

    // Animate in with a small delay to ensure DOM is ready
    setTimeout(() => {
      card.classList.add('visible');
    }, 50);

    // Auto-dismiss if specified
    if (autoDismissMs) {
      setTimeout(() => this.dismissVisualCard(), autoDismissMs);
    }
  }

  /**
   * Dismiss the active visual card
   */
  private dismissVisualCard(): void {
    if (this.activeVisualCard) {
      this.activeVisualCard.classList.remove('visible');
      this.activeVisualCard.classList.add('dismissing');
      const card = this.activeVisualCard;
      setTimeout(() => {
        card.remove();
      }, 300);
      this.activeVisualCard = null;
    }
  }

  // ===== A2UI RENDERING METHODS =====

  /**
   * Initialize the A2UI renderer
   */
  private initializeA2UIRenderer(): void {
    try {
      this.a2uiRenderer = new A2UIRenderer('a2ui-container');
      this.log('A2UI renderer initialized');
      this.addTerminalMessage('a2ui.renderer.init();', 'command');
    } catch (error) {
      console.error('[A2UI] Init failed:', error);
      this.log('A2UI renderer initialization failed');
    }
  }

  /**
   * Handle A2UI update events from the backend
   */
  private handleA2UIUpdate(data: {
    a2ui: A2UIDocument;
    query?: string;
    tier?: string;
    template_type?: string;
    timestamp?: number;
  }): void {
    if (!this.a2uiRenderer || !data.a2ui) {
      console.warn('[A2UI] Renderer not available or no data');
      return;
    }

    const templateType = data.a2ui.root?.type || 'unknown';
    const tier = data.tier || data.a2ui._metadata?.tier || 'auto';

    if (this.a2uiStatus) {
      this.a2uiStatus.textContent = 'RENDERING';
      this.a2uiStatus.classList.add('active');
    }
    this.a2uiHasContent = true;
    const isHomeScreen = this.mainLayout?.classList.contains('panels-hidden') ?? true;
    if (this.a2uiPanel && isHomeScreen) {
      this.a2uiPanel.classList.add('visible');
      document.body.classList.add('a2ui-panel-visible');
    }

    try {
      this.a2uiRenderer.render(data.a2ui);
      this.addTerminalMessage(`a2ui.render({ type: '${templateType}', tier: '${tier}' });`, 'command');
      this.log(`A2UI rendered: ${templateType} (${tier})`);

      setTimeout(() => {
        if (this.a2uiStatus) {
          this.a2uiStatus.textContent = 'READY';
          this.a2uiStatus.classList.remove('active');
        }
      }, 500);

    } catch (error) {
      console.error('[A2UI] Render error:', error);
      this.addTerminalMessage(`a2ui.error: ${(error as Error).message}`, 'error');
      if (this.a2uiStatus) {
        this.a2uiStatus.textContent = 'ERROR';
        this.a2uiStatus.classList.remove('active');
      }
    }
  }

  /**
   * Clear the A2UI display
   */
  private clearA2UI(): void {
    this.a2uiHasContent = false;
    if (this.a2uiRenderer) {
      this.a2uiRenderer.clear();
    }
    if (this.a2uiStatus) {
      this.a2uiStatus.textContent = 'READY';
    }
  }

  /**
   * Hide the A2UI panel
   */
  private hideA2UIPanel(): void {
    this.a2uiHasContent = false;
    if (this.a2uiPanel) {
      this.a2uiPanel.classList.remove('visible');
    }
    document.body.classList.remove('a2ui-panel-visible');
  }

  /**
   * Show the A2UI panel
   */
  private showA2UIPanel(): void {
    if (this.a2uiPanel) {
      this.a2uiPanel.classList.add('visible');
      document.body.classList.add('a2ui-panel-visible');
    }
  }

  // ===== EMOTION-REACTIVE UI METHODS =====

  /**
   * Update UI colors and animations based on emotion state
   */
  private updateEmotionReactiveUI(data: {
    arousal?: number;
    valence?: number;
    primary_emotion?: string;
    emotion?: string;
  }): void {
    // Debounce updates
    const now = Date.now();
    if (now - this.lastEmotionUpdate < this.emotionUpdateDebounceMs) {
      return;
    }
    this.lastEmotionUpdate = now;

    const emotion = data.primary_emotion || data.emotion || 'neutral';
    const arousal = data.arousal ?? 0.5;
    const valence = data.valence ?? 0.5;

    // Track emotion shifts for stats bar
    if (emotion !== this.mcStatLastEmotion && emotion !== 'neutral') {
      this.mcStatEmotionShifts++;
      this.mcStatLastEmotion = emotion;
      this.updateMcStats();
    }

    // Update CSS custom properties for emotion colors
    const root = document.documentElement;

    const emotionColors: Record<string, { primary: string; secondary: string; glow: string }> = {
      'neutral': { primary: '#37b6ff', secondary: '#9747ff', glow: 'rgba(55, 182, 255, 0.4)' },
      'happy': { primary: '#10b981', secondary: '#34d399', glow: 'rgba(16, 185, 129, 0.4)' },
      'excited': { primary: '#f59e0b', secondary: '#fbbf24', glow: 'rgba(245, 158, 11, 0.4)' },
      'sad': { primary: '#3b82f6', secondary: '#60a5fa', glow: 'rgba(59, 130, 246, 0.4)' },
      'frustrated': { primary: '#ef4444', secondary: '#f87171', glow: 'rgba(239, 68, 68, 0.4)' },
      'calm': { primary: '#06b6d4', secondary: '#22d3ee', glow: 'rgba(6, 182, 212, 0.4)' },
    };

    const colors = emotionColors[emotion] || emotionColors['neutral'];

    // Apply emotion colors to orb and UI elements
    root.style.setProperty('--emotion-primary', colors.primary);
    root.style.setProperty('--emotion-secondary', colors.secondary);
    root.style.setProperty('--emotion-glow', colors.glow);

    // Adjust animation speed based on arousal (0.75x to 1.25x)
    const animationSpeed = 1 + (arousal - 0.5) * 0.5;
    root.style.setProperty('--emotion-animation-speed', `${animationSpeed}`);

    // Update orb container data attribute for CSS styling
    this.orbContainer?.setAttribute('data-emotion', emotion);

    // Update scanner frame border based on valence
    if (this.scannerFrame) {
      if (valence > 0.6) {
        this.scannerFrame.style.borderColor = colors.primary;
      } else if (valence < 0.4) {
        this.scannerFrame.style.borderColor = colors.secondary;
      } else {
        this.scannerFrame.style.borderColor = '';
      }
    }
  }
}

// Initialize when DOM is ready
declare global {
  interface Window {
    VoiceScannerApp: typeof VoiceScannerApp;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.VoiceScannerApp = VoiceScannerApp;
  const app = new VoiceScannerApp();
  (window as any).voiceScannerApp = app; // e.g. voiceScannerApp.setLoaderText('Planning next moves')
});

