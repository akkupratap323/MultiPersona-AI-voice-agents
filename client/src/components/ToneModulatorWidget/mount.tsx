/**
 * Tone Modulator Widget Mount Script
 *
 * Mounts the React-based Tone Modulator to the dashboard card 5
 * and exposes updateToneModulator for the main app (emotion_detected, tone_switched).
 */

import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { ToneModulator } from './ToneModulator';

const MAX_SERIES_LENGTH = 32;

let root: Root | null = null;
let state = {
  detectedEmotion: 'neutral',
  nesterResponse: 'calm',
  clarityData: [] as number[],
  intensityData: [] as number[],
  xAxisIntervalSec: 5,
};

function renderWidget(): void {
  if (!root) return;
  root.render(
    <ToneModulator
      detectedEmotion={state.detectedEmotion}
      nesterResponse={state.nesterResponse}
      clarityData={state.clarityData}
      intensityData={state.intensityData}
      xAxisIntervalSec={state.xAxisIntervalSec}
    />
  );
}

export function mountToneModulator(containerId: string = 'tone-modulator-root'): void {
  const container = document.getElementById(containerId);
  if (!container) {
    console.warn(`[ToneModulator] Container #${containerId} not found`);
    return;
  }

  if (root) {
    return;
  }

  root = createRoot(container);
  renderWidget();
}

export interface ToneModulatorUpdate {
  detectedEmotion?: string;
  nesterResponse?: string;
  clarity?: number;
  intensity?: number;
  /** X-axis grid interval in seconds (e.g. 5, 10) */
  xAxisIntervalSec?: number;
}

/**
 * Update Tone Modulator state. Call from app on emotion_detected / hybrid_emotion_detected / tone_switched.
 * clarity/intensity can be derived from valence/arousal; if omitted, we keep existing series.
 */
export function updateToneModulator(update: ToneModulatorUpdate): void {
  let changed = false;
  if (update.detectedEmotion !== undefined) {
    state.detectedEmotion = update.detectedEmotion;
    changed = true;
  }
  if (update.nesterResponse !== undefined) {
    state.nesterResponse = update.nesterResponse;
    changed = true;
  }
  if (update.clarity !== undefined) {
    state.clarityData = [...state.clarityData, update.clarity].slice(-MAX_SERIES_LENGTH);
    changed = true;
  }
  if (update.intensity !== undefined) {
    state.intensityData = [...state.intensityData, update.intensity].slice(-MAX_SERIES_LENGTH);
    changed = true;
  }
  if (update.xAxisIntervalSec !== undefined) {
    state.xAxisIntervalSec = update.xAxisIntervalSec;
    changed = true;
  }
  if (changed) renderWidget();
}

export function unmountToneModulator(): void {
  if (root) {
    root.unmount();
    root = null;
    state = { detectedEmotion: 'neutral', nesterResponse: 'calm', clarityData: [], intensityData: [], xAxisIntervalSec: 5 };
  }
}

declare global {
  interface Window {
    ToneModulator: {
      mount: typeof mountToneModulator;
      unmount: typeof unmountToneModulator;
      update: typeof updateToneModulator;
    };
  }
}

window.ToneModulator = {
  mount: mountToneModulator,
  unmount: unmountToneModulator,
  update: updateToneModulator,
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => mountToneModulator());
} else {
  setTimeout(() => mountToneModulator(), 100);
}

export default {
  mount: mountToneModulator,
  unmount: unmountToneModulator,
  update: updateToneModulator,
};
