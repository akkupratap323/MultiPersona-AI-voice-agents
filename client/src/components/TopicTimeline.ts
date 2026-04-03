/**
 * TopicTimeline - Visual representation of conversation topics over time
 * Shows topic flow with continuity, branching, and new topic starts
 */

export interface TopicNode {
  id: string;
  topic: string;
  keywords: string[];
  timestamp: number;
  parentId: string | null;  // null for new topics, parent id for continuations/branches
  isBranch: boolean;        // true if this branches from parent
  x: number;                // calculated position
  y: number;                // calculated position
}

export class TopicTimeline {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private nodes: TopicNode[] = [];
  private animationId: number | null = null;
  private scrollOffset: number = 0;
  private nodeIdCounter: number = 0;

  // Layout constants
  private readonly NODE_RADIUS = 6;
  private readonly NODE_SPACING_Y = 45;  // Slightly reduced for better fit
  private readonly BRANCH_OFFSET_X = 40;
  private readonly PADDING = { top: 25, right: 20, bottom: 15, left: 30 };
  private readonly MAX_VISIBLE_NODES = 4;  // Keep last 4 nodes visible (depth 3 + current)

  // Colors
  private colors = {
    nodeFill: '#3b82f6',           // Blue
    nodeStroke: '#60a5fa',         // Light blue
    nodeContinue: '#22c55e',       // Green for continuing
    nodeBranch: '#f59e0b',         // Amber for branching
    nodeNew: '#ef4444',            // Red for new topic
    line: 'rgba(255, 255, 255, 0.3)',
    lineContinue: 'rgba(34, 197, 94, 0.5)',
    lineBranch: 'rgba(245, 158, 11, 0.5)',
    text: 'rgba(255, 255, 255, 0.8)',
    textMuted: 'rgba(255, 255, 255, 0.5)',
    background: 'transparent',
  };

  constructor(canvasId: string) {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    if (!canvas) {
      throw new Error(`Canvas element with id "${canvasId}" not found`);
    }
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Could not get 2D context from canvas');
    }
    this.ctx = ctx;

    // Setup
    setTimeout(() => {
      this.resizeCanvas();
      this.animate();
    }, 100);

    window.addEventListener('resize', () => this.resizeCanvas());

  }

  private resizeCanvas(): void {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    const width = rect.width || 200;
    const height = rect.height || 150;

    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(dpr, dpr);
  }

  /**
   * Add a new topic to the timeline
   * @param topic - The main topic/theme of this turn
   * @param keywords - Related keywords from the graph
   * @param topicType - Optional: "new", "continuation", or "branch" from backend LLM
   * @param parentTopicName - Optional: name of parent topic if branching
   */
  public addTopic(
    topic: string,
    keywords: string[] = [],
    topicType?: 'new' | 'continuation' | 'branch',
    parentTopicName?: string
  ): void {
    let parentNode: TopicNode | null = null;
    let isBranch = false;

    // If backend provides topic type, use it directly
    if (topicType) {
      if (topicType === 'new') {
        parentNode = null;
        isBranch = false;
      } else if (topicType === 'continuation') {
        // Find the last node as parent
        parentNode = this.nodes.length > 0 ? this.nodes[this.nodes.length - 1] : null;
        isBranch = false;
      } else if (topicType === 'branch') {
        // Find parent by name if provided, otherwise use last node
        if (parentTopicName) {
          parentNode = this.nodes.find(n => n.topic === parentTopicName) || null;
        }
        if (!parentNode && this.nodes.length > 0) {
          parentNode = this.nodes[this.nodes.length - 1];
        }
        isBranch = true;
      }
    } else {
      // Fallback to client-side detection if backend doesn't provide type
      parentNode = this.findParentNode(topic, keywords);
      isBranch = parentNode !== null && !this.isDirectContinuation(parentNode, topic, keywords);
    }

    const node: TopicNode = {
      id: `topic-${this.nodeIdCounter++}`,
      topic: topic,
      keywords: keywords,
      timestamp: Date.now(),
      parentId: parentNode?.id || null,
      isBranch: isBranch,
      x: 0,
      y: 0,
    };

    this.nodes.push(node);
    this.calculatePositions();
    this.autoScroll();

    // Topic tracking is handled by [Widget:ConversationAnalysis] in app.ts
  }

  /**
   * Find the most relevant parent node for the new topic
   */
  private findParentNode(topic: string, keywords: string[]): TopicNode | null {
    if (this.nodes.length === 0) return null;

    // Look at recent nodes (last 3)
    const recentNodes = this.nodes.slice(-3);

    // Check for keyword overlap
    let bestMatch: TopicNode | null = null;
    let bestScore = 0;

    for (const node of recentNodes) {
      const overlap = this.calculateOverlap(node.keywords, keywords);
      const topicSimilarity = this.calculateTopicSimilarity(node.topic, topic);
      const score = overlap * 2 + topicSimilarity;

      if (score > bestScore && score > 0.2) {
        bestScore = score;
        bestMatch = node;
      }
    }

    // If no good match, check if it's a continuation of the last topic
    if (!bestMatch && this.nodes.length > 0) {
      const lastNode = this.nodes[this.nodes.length - 1];
      const lastOverlap = this.calculateOverlap(lastNode.keywords, keywords);
      if (lastOverlap > 0.1) {
        return lastNode;
      }
    }

    return bestMatch;
  }

  /**
   * Check if this is a direct continuation (same topic) vs a branch
   */
  private isDirectContinuation(parent: TopicNode, topic: string, keywords: string[]): boolean {
    const topicSimilarity = this.calculateTopicSimilarity(parent.topic, topic);
    const keywordOverlap = this.calculateOverlap(parent.keywords, keywords);

    // High similarity = continuation, medium = branch
    return topicSimilarity > 0.7 || keywordOverlap > 0.5;
  }

  private calculateOverlap(arr1: string[], arr2: string[]): number {
    if (arr1.length === 0 || arr2.length === 0) return 0;
    const set1 = new Set(arr1.map(s => s.toLowerCase()));
    const matches = arr2.filter(s => set1.has(s.toLowerCase())).length;
    return matches / Math.max(arr1.length, arr2.length);
  }

  private calculateTopicSimilarity(topic1: string, topic2: string): number {
    const words1 = new Set(topic1.toLowerCase().split(/\s+/));
    const words2 = new Set(topic2.toLowerCase().split(/\s+/));

    let matches = 0;
    words1.forEach(w => {
      if (words2.has(w)) matches++;
    });

    return matches / Math.max(words1.size, words2.size);
  }

  /**
   * Calculate x,y positions for all nodes
   */
  private calculatePositions(): void {
    const dpr = window.devicePixelRatio || 1;
    const width = this.canvas.width / dpr;
    const centerX = width / 2;

    // Track columns for branching
    const columns: Map<string, number> = new Map();
    let currentColumn = 0;

    this.nodes.forEach((node, index) => {
      node.y = this.PADDING.top + index * this.NODE_SPACING_Y;

      if (node.parentId === null) {
        // New topic - reset to center
        currentColumn = 0;
        node.x = centerX;
      } else if (node.isBranch) {
        // Branch - offset from parent
        const parentNode = this.nodes.find(n => n.id === node.parentId);
        if (parentNode) {
          // Alternate left/right branching
          const direction = (this.nodes.filter(n => n.parentId === node.parentId).length % 2 === 0) ? 1 : -1;
          node.x = parentNode.x + (this.BRANCH_OFFSET_X * direction);
        } else {
          node.x = centerX;
        }
      } else {
        // Continuation - same x as parent
        const parentNode = this.nodes.find(n => n.id === node.parentId);
        node.x = parentNode ? parentNode.x : centerX;
      }

      // Clamp to canvas bounds
      node.x = Math.max(this.PADDING.left + this.NODE_RADIUS,
                        Math.min(width - this.PADDING.right - this.NODE_RADIUS, node.x));
    });
  }

  private autoScroll(): void {
    // No longer needed - we now limit visible nodes instead of scrolling
  }

  /**
   * Calculate positions for visible nodes only (fits within canvas)
   */
  private calculateVisiblePositions(visibleNodes: TopicNode[]): void {
    const dpr = window.devicePixelRatio || 1;
    const width = this.canvas.width / dpr;
    const centerX = width / 2;

    visibleNodes.forEach((node, index) => {
      // Position nodes from top, evenly spaced
      node.y = this.PADDING.top + index * this.NODE_SPACING_Y;

      if (node.parentId === null) {
        // New topic - center
        node.x = centerX;
      } else if (node.isBranch) {
        // Branch - offset from parent
        const parentNode = visibleNodes.find(n => n.id === node.parentId);
        if (parentNode) {
          const direction = (visibleNodes.filter(n => n.parentId === node.parentId).length % 2 === 0) ? 1 : -1;
          node.x = parentNode.x + (this.BRANCH_OFFSET_X * direction);
        } else {
          node.x = centerX;
        }
      } else {
        // Continuation - same x as parent or center
        const parentNode = visibleNodes.find(n => n.id === node.parentId);
        node.x = parentNode ? parentNode.x : centerX;
      }

      // Clamp to canvas bounds
      node.x = Math.max(this.PADDING.left + this.NODE_RADIUS,
                        Math.min(width - this.PADDING.right - this.NODE_RADIUS, node.x));
    });
  }

  /**
   * Draw connections between visible nodes only
   */
  private drawVisibleConnections(visibleNodes: TopicNode[]): void {
    visibleNodes.forEach(node => {
      if (node.parentId === null) return;

      // Find parent in visible nodes
      const parentNode = visibleNodes.find(n => n.id === node.parentId);
      if (!parentNode) {
        // Parent is not visible - draw from top edge to indicate continuation
        this.ctx.strokeStyle = this.colors.lineContinue;
        this.ctx.setLineDash([2, 2]);
        this.ctx.lineWidth = 1;
        this.ctx.globalAlpha = 0.5;
        this.ctx.beginPath();
        this.ctx.moveTo(node.x, 0);
        this.ctx.lineTo(node.x, node.y - this.NODE_RADIUS);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
        this.ctx.globalAlpha = 1;
        return;
      }

      // Determine line style based on relationship
      if (node.isBranch) {
        this.ctx.strokeStyle = this.colors.lineBranch;
        this.ctx.setLineDash([4, 4]);
      } else {
        this.ctx.strokeStyle = this.colors.lineContinue;
        this.ctx.setLineDash([]);
      }

      this.ctx.lineWidth = 2;
      this.ctx.beginPath();

      if (node.isBranch) {
        // Curved line for branches
        const midY = (parentNode.y + node.y) / 2;
        this.ctx.moveTo(parentNode.x, parentNode.y + this.NODE_RADIUS);
        this.ctx.bezierCurveTo(
          parentNode.x, midY,
          node.x, midY,
          node.x, node.y - this.NODE_RADIUS
        );
      } else {
        // Straight line for continuation
        this.ctx.moveTo(parentNode.x, parentNode.y + this.NODE_RADIUS);
        this.ctx.lineTo(node.x, node.y - this.NODE_RADIUS);
      }

      this.ctx.stroke();
      this.ctx.setLineDash([]);
    });
  }

  private animate = (): void => {
    this.draw();
    this.animationId = requestAnimationFrame(this.animate);
  };

  private draw(): void {
    const dpr = window.devicePixelRatio || 1;
    const width = this.canvas.width / dpr;
    const height = this.canvas.height / dpr;

    if (width <= 0 || height <= 0) return;

    // Clear
    this.ctx.clearRect(0, 0, width, height);

    if (this.nodes.length === 0) {
      this.drawEmptyState(width, height);
      return;
    }

    // Get only the last MAX_VISIBLE_NODES nodes to display
    const visibleNodes = this.nodes.slice(-this.MAX_VISIBLE_NODES);

    // Recalculate positions for visible nodes only (no scrolling)
    this.calculateVisiblePositions(visibleNodes);

    // Draw connections first (behind nodes)
    this.drawVisibleConnections(visibleNodes);

    // Draw nodes
    visibleNodes.forEach((node, index) => {
      this.drawNode(node, index === visibleNodes.length - 1);
    });
  }

  private drawEmptyState(width: number, height: number): void {
    this.ctx.fillStyle = this.colors.textMuted;
    this.ctx.font = '11px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'center';
    this.ctx.fillText('Topics will appear here', width / 2, height / 2);
  }

  private drawConnections(): void {
    this.nodes.forEach(node => {
      if (node.parentId === null) return;

      const parentNode = this.nodes.find(n => n.id === node.parentId);
      if (!parentNode) return;

      // Determine line style based on relationship
      if (node.isBranch) {
        this.ctx.strokeStyle = this.colors.lineBranch;
        this.ctx.setLineDash([4, 4]);
      } else {
        this.ctx.strokeStyle = this.colors.lineContinue;
        this.ctx.setLineDash([]);
      }

      this.ctx.lineWidth = 2;
      this.ctx.beginPath();

      if (node.isBranch) {
        // Curved line for branches
        const midY = (parentNode.y + node.y) / 2;
        this.ctx.moveTo(parentNode.x, parentNode.y + this.NODE_RADIUS);
        this.ctx.bezierCurveTo(
          parentNode.x, midY,
          node.x, midY,
          node.x, node.y - this.NODE_RADIUS
        );
      } else {
        // Straight line for continuation
        this.ctx.moveTo(parentNode.x, parentNode.y + this.NODE_RADIUS);
        this.ctx.lineTo(node.x, node.y - this.NODE_RADIUS);
      }

      this.ctx.stroke();
      this.ctx.setLineDash([]);
    });
  }

  private drawNode(node: TopicNode, isLatest: boolean): void {
    const radius = isLatest ? this.NODE_RADIUS + 2 : this.NODE_RADIUS;

    // Determine node color
    let nodeColor: string;
    if (node.parentId === null) {
      nodeColor = this.colors.nodeNew;
    } else if (node.isBranch) {
      nodeColor = this.colors.nodeBranch;
    } else {
      nodeColor = this.colors.nodeContinue;
    }

    // Glow effect for latest node
    if (isLatest) {
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, radius + 4, 0, Math.PI * 2);
      this.ctx.fillStyle = nodeColor;
      this.ctx.globalAlpha = 0.3;
      this.ctx.fill();
      this.ctx.globalAlpha = 1;
    }

    // Node circle
    this.ctx.beginPath();
    this.ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
    this.ctx.fillStyle = nodeColor;
    this.ctx.fill();

    // Node border
    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    this.ctx.lineWidth = 1;
    this.ctx.stroke();

    // Topic label
    this.ctx.fillStyle = isLatest ? this.colors.text : this.colors.textMuted;
    this.ctx.font = `${isLatest ? 'bold ' : ''}10px "JetBrains Mono", monospace`;
    this.ctx.textAlign = 'left';

    // Truncate topic if too long
    const maxWidth = 100;
    let displayTopic = node.topic;
    if (this.ctx.measureText(displayTopic).width > maxWidth) {
      while (this.ctx.measureText(displayTopic + '...').width > maxWidth && displayTopic.length > 0) {
        displayTopic = displayTopic.slice(0, -1);
      }
      displayTopic += '...';
    }

    const labelX = node.x + radius + 8;
    this.ctx.fillText(displayTopic, labelX, node.y + 4);
  }

  public destroy(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    window.removeEventListener('resize', () => this.resizeCanvas());
  }

  public clear(): void {
    this.nodes = [];
    this.scrollOffset = 0;
    this.nodeIdCounter = 0;
  }
}

// Export for global access
declare global {
  interface Window {
    TopicTimeline: typeof TopicTimeline;
  }
}

window.TopicTimeline = TopicTimeline;
