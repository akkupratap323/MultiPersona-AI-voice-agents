/**
 * Knowledge Graph Widget Mount Script
 *
 * Mounts the React-based Knowledge Graph Widget to the DOM
 * and exposes methods for the main app to interact with it.
 */

import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { KnowledgeGraphWidget } from './KnowledgeGraphWidget';
import { KnowledgeGraphNode } from './types';

let root: Root | null = null;
let currentKeywords: string[] = [];
let cycleInterval: ReturnType<typeof setInterval> | null = null;
let currentCycleIndex: number = 0;

/**
 * Initialize and mount the Knowledge Graph Widget
 */
export function mountKnowledgeGraph(containerId: string = 'knowledge-graph-root'): void {
  const container = document.getElementById(containerId);
  if (!container) {
    console.warn(`[KnowledgeGraph] Container #${containerId} not found`);
    return;
  }

  if (root) {
    return;
  }

  root = createRoot(container);
  renderWidget();
}

/**
 * Render the widget with current state
 */
function renderWidget(): void {
  if (!root) return;

  root.render(
    <KnowledgeGraphWidget
      highlightKeywords={currentKeywords}
      visible={true}
      onNodeClick={handleNodeClick}
    />
  );
}

/**
 * Handle node click events
 */
function handleNodeClick(nodeId: string, nodeData: KnowledgeGraphNode): void {
  // Dispatch custom event for the main app to handle
  window.dispatchEvent(new CustomEvent('knowledgeGraphNodeClick', {
    detail: { nodeId, nodeData }
  }));
}

/**
 * Update highlighted keywords (all at once)
 */
export function highlightKeywords(keywords: string[]): void {
  stopCycle();
  currentKeywords = keywords;
  renderWidget();
}

/**
 * Highlight keywords with cycling animation
 * Cycles through nodes: 1 → 2 → 3 → 4 → 1, then stops on first node
 */
export function highlightWithCycle(keywords: string[]): void {
  stopCycle();

  if (!keywords || keywords.length === 0) {
    clearHighlights();
    return;
  }

  currentKeywords = keywords;
  currentCycleIndex = 0;

  // Show first node immediately
  renderWidgetWithFocus(keywords[0]);

  // Cycle through nodes every 2 seconds, complete full loop back to first
  if (keywords.length > 1) {
    let cycleCount = 0;
    const totalSteps = keywords.length; // Will cycle through all and back to first

    cycleInterval = setInterval(() => {
      cycleCount++;
      currentCycleIndex = cycleCount % keywords.length;

      const focusNode = keywords[currentCycleIndex];
      renderWidgetWithFocus(focusNode);

      // Stop after returning to first node (one complete cycle)
      if (cycleCount >= totalSteps) {
        stopCycle();
      }
    }, 2000);
  }
}

/**
 * Stop the cycling animation
 */
export function stopCycle(): void {
  if (cycleInterval) {
    clearInterval(cycleInterval);
    cycleInterval = null;
  }
}

/**
 * Render widget with a specific focus node
 */
function renderWidgetWithFocus(focusNodeId: string): void {
  if (!root) return;

  root.render(
    <KnowledgeGraphWidget
      highlightKeywords={currentKeywords}
      focusNodeId={focusNodeId}
      visible={true}
      onNodeClick={handleNodeClick}
    />
  );
}

/**
 * Clear all highlights
 */
export function clearHighlights(): void {
  stopCycle();
  currentKeywords = [];
  renderWidget();
}

/**
 * Unmount the widget
 */
export function unmountKnowledgeGraph(): void {
  if (root) {
    root.unmount();
    root = null;
  }
}

// Expose to window for easy access from vanilla JS
declare global {
  interface Window {
    KnowledgeGraph: {
      mount: typeof mountKnowledgeGraph;
      unmount: typeof unmountKnowledgeGraph;
      highlight: typeof highlightKeywords;
      highlightWithCycle: typeof highlightWithCycle;
      stopCycle: typeof stopCycle;
      clear: typeof clearHighlights;
    };
  }
}

window.KnowledgeGraph = {
  mount: mountKnowledgeGraph,
  unmount: unmountKnowledgeGraph,
  highlight: highlightKeywords,
  highlightWithCycle: highlightWithCycle,
  stopCycle: stopCycle,
  clear: clearHighlights,
};

// Auto-mount on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => mountKnowledgeGraph());
} else {
  // DOM is already ready
  setTimeout(() => mountKnowledgeGraph(), 100);
}

export default {
  mount: mountKnowledgeGraph,
  unmount: unmountKnowledgeGraph,
  highlight: highlightKeywords,
  highlightWithCycle: highlightWithCycle,
  stopCycle: stopCycle,
  clear: clearHighlights,
};
