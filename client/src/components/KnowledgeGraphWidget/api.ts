/**
 * LightRAG API Client
 * Communicates with the LightRAG server to fetch knowledge graph data
 */

import { KnowledgeGraph } from './types';

// LightRAG server URL - can be configured via environment variable or window global
const LIGHTRAG_URL = (window as any).__LIGHTRAG_URL__ ||
                     (window as any).LIGHTRAG_URL ||
                     'http://localhost:9621';


// LightRAG API key for authentication
const LIGHTRAG_API_KEY = (window as any).__LIGHTRAG_API_KEY__ ||
                         (window as any).LIGHTRAG_API_KEY ||
                         '';

/**
 * Fetch the knowledge graph from LightRAG
 * @param label - Node label to filter by (use '*' for all nodes)
 * @param maxDepth - Maximum depth of graph traversal
 */
export async function fetchGraph(
  label: string = '*',
  maxDepth: number = 3
): Promise<KnowledgeGraph> {
  try {
    const url = `${LIGHTRAG_URL}/graphs?label=${encodeURIComponent(label)}&max_depth=${maxDepth}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (LIGHTRAG_API_KEY) {
      headers['X-API-Key'] = LIGHTRAG_API_KEY;
    }
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch graph: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('[KnowledgeGraph] Error fetching graph:', error);
    throw error;
  }
}

/**
 * Fetch available graph labels from LightRAG
 */
export async function fetchGraphLabels(): Promise<string[]> {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (LIGHTRAG_API_KEY) {
      headers['X-API-Key'] = LIGHTRAG_API_KEY;
    }
    const response = await fetch(`${LIGHTRAG_URL}/graph/label/list`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch labels: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('[KnowledgeGraph] Error fetching labels:', error);
    throw error;
  }
}

/**
 * Check if LightRAG server is healthy
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const headers: Record<string, string> = {};
    if (LIGHTRAG_API_KEY) {
      headers['X-API-Key'] = LIGHTRAG_API_KEY;
    }
    const response = await fetch(`${LIGHTRAG_URL}/health`, {
      method: 'GET',
      headers,
    });
    return response.ok;
  } catch {
    return false;
  }
}
