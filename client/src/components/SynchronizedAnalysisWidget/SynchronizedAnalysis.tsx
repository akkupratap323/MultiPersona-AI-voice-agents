import { useRef } from 'react';
import { TopicFlowGraph } from './TopicFlowGraph';
import { TopicNode } from './topicExtraction';

interface SynchronizedAnalysisProps {
  topics: TopicNode[];
}

export function SynchronizedAnalysis({ topics }: SynchronizedAnalysisProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <div className="sync-analysis">
      <TopicFlowGraph topics={topics} scrollRef={scrollRef} onScroll={() => {}} />
    </div>
  );
}
