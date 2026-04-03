/**
 * Knowledge Graph Widget Types
 */

export interface KnowledgeGraphNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
  color?: string;
  x?: number;
  y?: number;
  size?: number;
}

export interface KnowledgeGraphEdge {
  id: string;
  type?: string;
  source: string;
  target: string;
  properties: Record<string, any>;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export interface GraphWidgetProps {
  highlightKeywords?: string[];
  focusNodeId?: string;  // Node to focus/animate camera to
  visible?: boolean;
  onNodeClick?: (nodeId: string, nodeData: KnowledgeGraphNode) => void;
  className?: string;
}

export interface NodeAttributes {
  label: string;
  color: string;
  x: number;
  y: number;
  size: number;
  highlighted?: boolean;
  borderColor?: string;
  borderSize?: number;
}

export interface EdgeAttributes {
  label?: string;
  color?: string;
  size?: number;
}
