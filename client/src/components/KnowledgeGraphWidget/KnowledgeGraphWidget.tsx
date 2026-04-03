/**
 * Knowledge Graph Widget
 *
 * Displays the LightRAG knowledge graph in a sci-fi command center style.
 * Features sonar ring background, glass-morphic context pills, and accent-themed colors.
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  SigmaContainer,
  useRegisterEvents,
  useSigma,
  useLoadGraph,
  useSetSettings,
  useCamera,
} from '@react-sigma/core';
import { useLayoutForceAtlas2 } from '@react-sigma/layout-forceatlas2';
import Graph from 'graphology';
import { EdgeArrowProgram } from 'sigma/rendering';
import EdgeCurveProgram, { EdgeCurvedArrowProgram } from '@sigma/edge-curve';
import MiniSearch from 'minisearch';
import seedrandom from 'seedrandom';

import { fetchGraph } from './api';
import { KnowledgeGraph, GraphWidgetProps } from './types';

import '@react-sigma/core/lib/style.css';
import './styles.css';

/* ── Color constants (accent-themed) ── */
const COLORS = {
  nodeDefault: '#6b7280',
  nodeHighlighted: '#2563eb',  // Will be overridden by accent-hero at runtime
  nodeDisabled: '#374151',
  edgeDefault: '#4b5563',
  edgeHighlighted: '#2563eb',
  labelDefault: '#d1d5db',
  labelHighlighted: '#ffffff',
};

const MIN_NODE_SIZE = 4;
const MAX_NODE_SIZE = 14;

function randomColor(seed: string): string {
  seedrandom(seed, { global: true });
  const colors = ['#6b7280', '#9ca3af', '#78716c', '#71717a'];
  return colors[Math.floor(Math.random() * colors.length)];
}

/* ── Get accent color from CSS variable ── */
function getAccentColor(): string {
  const style = getComputedStyle(document.documentElement);
  return style.getPropertyValue('--accent-hero')?.trim() || '#2563eb';
}

/**
 * Graph Events Handler
 */
function GraphEvents({ onNodeClick }: { onNodeClick?: (nodeId: string) => void }) {
  const registerEvents = useRegisterEvents();

  useEffect(() => {
    registerEvents({
      clickNode: (event: { node: string }) => {
        onNodeClick?.(event.node);
      },
    });
  }, [registerEvents, onNodeClick]);

  return null;
}

/**
 * FocusOnNode - centers camera and zooms
 */
function FocusOnNode({ node }: { node: string | null }) {
  const sigma = useSigma();
  const { gotoNode } = useCamera();

  useEffect(() => {
    if (!node) return;

    const graph = sigma.getGraph();
    if (!graph.hasNode(node)) return;

    graph.setNodeAttribute(node, 'highlighted', true);
    gotoNode(node);

    const camera = sigma.getCamera();
    setTimeout(() => {
      const currentState = camera.getState();
      camera.animate(
        { ...currentState, ratio: 0.35 },
        { duration: 300, easing: 'cubicInOut' }
      );
    }, 100);

    return () => {
      if (graph.hasNode(node)) {
        graph.setNodeAttribute(node, 'highlighted', false);
      }
    };
  }, [node, sigma, gotoNode]);

  return null;
}

/**
 * InitialZoom - animates camera on page load
 */
function InitialZoom({ graphLoaded }: { graphLoaded: boolean }) {
  const sigma = useSigma();
  const zoomApplied = useRef(false);
  const [pageReady, setPageReady] = useState(false);

  useEffect(() => {
    const handlePageReady = () => setPageReady(true);
    window.addEventListener('nesterPageReady', handlePageReady);
    return () => window.removeEventListener('nesterPageReady', handlePageReady);
  }, []);

  useEffect(() => {
    if (!graphLoaded || zoomApplied.current) return;

    const camera = sigma.getCamera();
    camera.setState({ ratio: 1.5, x: 0.5, y: 0.5 });

    if (pageReady) {
      const timer = setTimeout(() => {
        zoomApplied.current = true;
        camera.animate(
          { ratio: 0.5, x: 0.5, y: 0.5 },
          { duration: 1200, easing: 'cubicInOut' }
        );
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [graphLoaded, pageReady, sigma]);

  return null;
}

/**
 * GraphControl - handles graph loading and node/edge styling
 */
function GraphControl({
  graphData,
  highlightedNodes,
  focusedNode,
}: {
  graphData: KnowledgeGraph | null;
  highlightedNodes: Set<string>;
  focusedNode: string | null;
}) {
  const sigma = useSigma();
  const loadGraph = useLoadGraph();
  const setSettings = useSetSettings();
  const { assign: assignLayout } = useLayoutForceAtlas2({ iterations: 50 });
  const graphLoadedRef = useRef(false);

  useEffect(() => {
    if (!graphData || graphLoadedRef.current) return;
    graphLoadedRef.current = true;

    const graph = new Graph();
    const accent = getAccentColor();

    const degrees: Record<string, number> = {};
    graphData.nodes.forEach((n) => { degrees[n.id] = 0; });
    graphData.edges.forEach((e) => {
      degrees[e.source] = (degrees[e.source] || 0) + 1;
      degrees[e.target] = (degrees[e.target] || 0) + 1;
    });

    const maxDegree = Math.max(...Object.values(degrees), 1);
    const minDegree = Math.min(...Object.values(degrees), 0);
    const range = maxDegree - minDegree || 1;

    graphData.nodes.forEach((node) => {
      const degree = degrees[node.id] || 0;
      const size = MIN_NODE_SIZE + (MAX_NODE_SIZE - MIN_NODE_SIZE) * Math.pow((degree - minDegree) / range, 0.5);

      const displayName = node.labels?.length > 0
        ? node.labels.join(', ')
        : (node.properties?.name || node.properties?.entity_name || node.id);

      graph.addNode(node.id, {
        label: displayName,
        color: randomColor(node.id),
        x: node.x ?? Math.random(),
        y: node.y ?? Math.random(),
        size,
      });
    });

    graphData.edges.forEach((edge) => {
      if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
        try {
          graph.addDirectedEdge(edge.source, edge.target, {
            label: edge.type,
            color: COLORS.edgeDefault,
          });
        } catch {
          // Edge might already exist
        }
      }
    });

    loadGraph(graph);
    setTimeout(() => assignLayout(), 100);
  }, [graphData, loadGraph, assignLayout]);

  useEffect(() => {
    const accent = getAccentColor();

    setSettings({
      nodeReducer: (node, data) => {
        const newData: Record<string, any> = {
          ...data,
          highlighted: data.highlighted || false,
          labelColor: COLORS.labelDefault,
        };

        if (highlightedNodes.size > 0) {
          if (highlightedNodes.has(node)) {
            newData.highlighted = true;
            newData.color = accent;
            newData.labelColor = COLORS.labelHighlighted;
          } else {
            newData.color = COLORS.nodeDisabled;
          }
        }

        return newData;
      },
      edgeReducer: (edge, data) => {
        const graph = sigma.getGraph();
        const newData = { ...data };

        if (highlightedNodes.size > 0) {
          const [source, target] = graph.extremities(edge);
          if (highlightedNodes.has(source) || highlightedNodes.has(target)) {
            newData.color = accent;
          } else {
            newData.color = COLORS.edgeDefault;
          }
        }

        return newData;
      },
    });
  }, [highlightedNodes, focusedNode, setSettings, sigma]);

  return null;
}

/**
 * Main Knowledge Graph Widget Component
 */
export function KnowledgeGraphWidget({
  highlightKeywords = [],
  focusNodeId,
  visible = true,
  onNodeClick,
  className = '',
}: GraphWidgetProps) {
  const [graphData, setGraphData] = useState<KnowledgeGraph | null>(null);
  const [searchIndex, setSearchIndex] = useState<MiniSearch<{ id: number; nodeId: string; label: string }> | null>(null);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [focusedNode, setFocusedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [allNodeIds, setAllNodeIds] = useState<Set<string>>(new Set());
  const cycleIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load graph on mount
  useEffect(() => {
    async function loadGraphData() {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchGraph('*', 10);
        setGraphData(data);

        const nodeIds = new Set(data.nodes.map((n) => n.id.toLowerCase()));
        setAllNodeIds(nodeIds);

        const index = new MiniSearch<{ id: number; nodeId: string; label: string }>({
          fields: ['label'],
          storeFields: ['label', 'nodeId'],
          searchOptions: { fuzzy: 0.2, prefix: true },
        });

        index.addAll(data.nodes.map((n, i) => ({
          id: i,
          nodeId: n.id,
          label: n.id.toLowerCase(),
        })));

        setSearchIndex(index);
      } catch (e) {
        console.error('[KnowledgeGraph] Failed to load graph:', e);
        setError('Failed to load knowledge graph');
      } finally {
        setLoading(false);
      }
    }

    loadGraphData();
  }, []);

  // Keyword highlighting and cycling
  useEffect(() => {
    if (cycleIntervalRef.current) {
      clearInterval(cycleIntervalRef.current);
      cycleIntervalRef.current = null;
    }

    if (!searchIndex || !graphData || highlightKeywords.length === 0) {
      setHighlightedNodes(new Set());
      setFocusedNode(null);
      return;
    }

    const matchedNodes: string[] = [];

    highlightKeywords.forEach((keyword) => {
      const kw = keyword.toLowerCase().trim();
      if (!kw) return;

      if (allNodeIds.has(kw)) {
        const node = graphData.nodes.find((n) => n.id.toLowerCase() === kw);
        if (node && !matchedNodes.includes(node.id)) {
          matchedNodes.push(node.id);
        }
      } else {
        const results = searchIndex.search(kw).slice(0, 3);
        results.forEach((result) => {
          const node = graphData.nodes[result.id];
          if (node && !matchedNodes.includes(node.id)) {
            matchedNodes.push(node.id);
          }
        });
      }
    });

    if (matchedNodes.length === 0) {
      setHighlightedNodes(new Set());
      setFocusedNode(null);
      return;
    }

    setHighlightedNodes(new Set([matchedNodes[0]]));
    setFocusedNode(matchedNodes[0]);

    if (matchedNodes.length > 1) {
      let currentIndex = 0;

      cycleIntervalRef.current = setInterval(() => {
        currentIndex = (currentIndex + 1) % matchedNodes.length;
        const currentNode = matchedNodes[currentIndex];

        setHighlightedNodes(new Set([currentNode]));
        setFocusedNode(currentNode);

        if (currentIndex === 0) {
          if (cycleIntervalRef.current) {
            clearInterval(cycleIntervalRef.current);
            cycleIntervalRef.current = null;
          }
        }
      }, 2000);
    }

    return () => {
      if (cycleIntervalRef.current) {
        clearInterval(cycleIntervalRef.current);
        cycleIntervalRef.current = null;
      }
    };
  }, [highlightKeywords, searchIndex, graphData, allNodeIds]);

  const getAvailableKeywords = useCallback(() => {
    return graphData?.nodes.map((n) => n.id) || [];
  }, [graphData]);

  useEffect(() => {
    (window as any).getGraphKeywords = getAvailableKeywords;
    return () => { delete (window as any).getGraphKeywords; };
  }, [getAvailableKeywords]);

  const handleNodeClick = useCallback((nodeId: string) => {
    if (onNodeClick && graphData) {
      const nodeData = graphData.nodes.find((n) => n.id === nodeId);
      if (nodeData) onNodeClick(nodeId, nodeData);
    }
  }, [onNodeClick, graphData]);

  if (!visible) return null;

  const nodeCount = graphData?.nodes.length ?? 0;
  const edgeCount = graphData?.edges.length ?? 0;

  const sigmaSettings = {
    allowInvalidContainer: true,
    defaultNodeType: 'circle',
    defaultEdgeType: 'curvedArrow',
    renderEdgeLabels: false,
    renderLabels: true,
    labelSize: 11,
    labelColor: { color: COLORS.labelDefault, attribute: 'labelColor' },
    labelRenderedSizeThreshold: 4,
    edgeProgramClasses: {
      curvedArrow: EdgeCurvedArrowProgram,
      curved: EdgeCurveProgram,
      arrow: EdgeArrowProgram,
    },
  };

  // Context pills: show highlighted nodes, or fallback to first few graph nodes
  const contextNodes = highlightedNodes.size > 0
    ? [...highlightedNodes].slice(0, 5)
    : (graphData?.nodes.slice(0, 4).map(n => n.id) ?? []);

  return (
    <div className={`knowledge-graph-widget ${className}`}>
      {/* Header with stats */}
      <div className="kg-header">
        <div className="kg-header-left">
          <div className="kg-live-dot" />
          <span className="kg-header-title">Knowledge Graph</span>
        </div>
        <div className="kg-header-stats">
          <span>{nodeCount} Nodes</span>
          <span className="kg-header-divider">/</span>
          <span>{edgeCount} Edges</span>
        </div>
      </div>

      {/* Graph visualization area */}
      <div className="kg-container">
        {/* Sonar rings background */}
        <div className="kg-sonar-layer">
          <div className="kg-sonar-ring" />
          <div className="kg-sonar-ring" />
          <div className="kg-sonar-ring" />
        </div>

        {loading && (
          <div className="kg-loading">
            <div className="kg-spinner" />
            <span>Loading graph...</span>
          </div>
        )}

        {error && (
          <div className="kg-error">
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && graphData && (
          <SigmaContainer settings={sigmaSettings} className="kg-sigma">
            <GraphControl
              graphData={graphData}
              highlightedNodes={highlightedNodes}
              focusedNode={focusedNode}
            />
            <GraphEvents onNodeClick={handleNodeClick} />
            <FocusOnNode node={focusedNode} />
            <InitialZoom graphLoaded={!!graphData} />
          </SigmaContainer>
        )}
      </div>

      {/* Context strip footer */}
      {contextNodes.length > 0 && (
        <div className="kg-context-strip">
          <span className="kg-context-label">Context:</span>
          <div className="kg-context-pills">
            {contextNodes.map((nodeId) => {
              const node = graphData?.nodes.find((n) => n.id === nodeId);
              const displayName = node?.labels?.length
                ? node.labels[0]
                : (node?.properties?.name || nodeId);
              const isFocused = nodeId === (focusNodeId || focusedNode);
              return (
                <span
                  key={nodeId}
                  className={`kg-context-pill ${isFocused ? 'kg-pill-focused' : ''}`}
                >
                  <span className="kg-pill-dot" />
                  {displayName}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default KnowledgeGraphWidget;
