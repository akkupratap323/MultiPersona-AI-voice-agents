/**
 * Minimal interface for EmotionAnalysis. Compatible with TopicNode from topicExtraction.
 */

export interface EmotionTopicNode {
  id: string;
  timestamp: Date;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentimentLabel: string;
  intensity: number;
  category?: string;
  name?: string;
}
