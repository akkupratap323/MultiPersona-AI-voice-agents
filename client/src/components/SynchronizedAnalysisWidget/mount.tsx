/**
 * SynchronizedAnalysis Widget Mount Script
 *
 * Mounts the React-based SynchronizedAnalysis (Topic Flow + Emotion Analysis)
 * to the left panel and exposes methods for the main app to update topics.
 */

import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { SynchronizedAnalysis } from './SynchronizedAnalysis';
import { TopicNode } from './topicExtraction';

import './SynchronizedAnalysis.css';

let root: Root | null = null;
let currentTopics: TopicNode[] = [];

function renderWidget(): void {
  if (!root) return;
  root.render(<SynchronizedAnalysis topics={currentTopics} />);
}

/**
 * Initialize and mount the SynchronizedAnalysis widget
 */
export function mountSynchronizedAnalysis(containerId: string = 'synchronized-analysis-root'): void {
  const container = document.getElementById(containerId);
  if (!container) {
    console.warn(`[SynchronizedAnalysis] Container #${containerId} not found`);
    return;
  }

  if (root) {
    return;
  }

  root = createRoot(container);
  renderWidget();
}

/**
 * Update topics and re-render
 */
export function updateSynchronizedAnalysisTopics(topics: TopicNode[]): void {
  currentTopics = topics;
  renderWidget();
}

/**
 * Unmount the widget
 */
export function unmountSynchronizedAnalysis(): void {
  if (root) {
    root.unmount();
    root = null;
    currentTopics = [];
  }
}

declare global {
  interface Window {
    SynchronizedAnalysis: {
      mount: typeof mountSynchronizedAnalysis;
      unmount: typeof unmountSynchronizedAnalysis;
      updateTopics: typeof updateSynchronizedAnalysisTopics;
    };
  }
}

window.SynchronizedAnalysis = {
  mount: mountSynchronizedAnalysis,
  unmount: unmountSynchronizedAnalysis,
  updateTopics: updateSynchronizedAnalysisTopics,
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => mountSynchronizedAnalysis());
} else {
  setTimeout(() => mountSynchronizedAnalysis(), 100);
}

export default {
  mount: mountSynchronizedAnalysis,
  unmount: unmountSynchronizedAnalysis,
  updateTopics: updateSynchronizedAnalysisTopics,
};
