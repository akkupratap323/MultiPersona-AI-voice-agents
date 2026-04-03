import { useEffect, useRef, useState } from 'react';
import { motion } from 'motion/react';
import { TopicNode, getTransitionLabel } from './topicExtraction';

interface TopicFlowGraphProps {
  topics: TopicNode[];
  scrollRef: React.RefObject<HTMLDivElement | null>;
  onScroll: () => void;
}

const STICKY_X_HEIGHT = 24;
const MIN_CHART_HEIGHT = 160;
const DEFAULT_CHART_HEIGHT = 240;

export function TopicFlowGraph({ topics, scrollRef, onScroll }: TopicFlowGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);
  const [chartHeight, setChartHeight] = useState(DEFAULT_CHART_HEIGHT);
  const [containerWidth, setContainerWidth] = useState(0);
  const [isManuallyControlled, setIsManuallyControlled] = useState(false);
  const autoScrollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const programmaticScrollRef = useRef(false);

  const isAtRightEdge = () => {
    if (!scrollRef.current) return true;
    const { scrollLeft: sl, scrollWidth, clientWidth } = scrollRef.current;
    return scrollWidth - sl - clientWidth < 30;
  };

  const handleScrollInternal = () => {
    if (scrollRef.current) {
      setScrollTop(scrollRef.current.scrollTop);
      setScrollLeft(scrollRef.current.scrollLeft);
      // Only mark as manually controlled if this was a user-initiated scroll
      if (!programmaticScrollRef.current) {
        if (!isAtRightEdge()) {
          setIsManuallyControlled(true);
        } else {
          setIsManuallyControlled(false);
        }
      }
      programmaticScrollRef.current = false;
    }
    onScroll();
  };

  const scrollToLatest = () => {
    if (!scrollRef.current) return;
    programmaticScrollRef.current = true;
    setIsManuallyControlled(false);
    const scrollLeftTarget = Math.max(0, scrollRef.current.scrollWidth - scrollRef.current.clientWidth);
    scrollRef.current.scrollTo({ left: scrollLeftTarget, behavior: 'smooth' });
  };

  useEffect(() => {
    if (!isManuallyControlled && scrollRef.current && topics.length > 0) {
      // Wait for DOM to update with new SVG dimensions before scrolling
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (!scrollRef.current) return;
          const lastTopic = topics[topics.length - 1];
          const plotH = chartHeight - 20 - STICKY_X_HEIGHT;
          const rowCnt = Math.max(new Set(topics.map((t) => t.row)).size, 1);
          const lastTopicY = 20 + (lastTopic.row + 0.5) * (plotH / rowCnt);
          const viewportHeight = scrollRef.current.clientHeight;
          const currentScrollTop = scrollRef.current.scrollTop;
          const visibleTop = currentScrollTop;
          const visibleBottom = currentScrollTop + viewportHeight;
          const isAboveViewport = lastTopicY < visibleTop + 60;
          const isBelowViewport = lastTopicY > visibleBottom - 60;
          let targetScrollTop = currentScrollTop;
          if (isAboveViewport || isBelowViewport) targetScrollTop = lastTopicY - (viewportHeight / 2);
          const scrollLeftTarget = Math.max(0, scrollRef.current.scrollWidth - scrollRef.current.clientWidth);
          programmaticScrollRef.current = true;
          scrollRef.current.scrollTo({
            left: scrollLeftTarget,
            top: Math.max(0, targetScrollTop),
            behavior: 'smooth'
          });
        });
      });
    }
  }, [topics, scrollRef, isManuallyControlled, chartHeight]);

  useEffect(() => () => {
    if (autoScrollTimeoutRef.current) clearTimeout(autoScrollTimeoutRef.current);
  }, []);

  useEffect(() => {
    const el = bodyRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setContainerWidth(Math.round(width));
      setChartHeight(Math.max(MIN_CHART_HEIGHT, Math.round(height)));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const getRowInfo = () => {
    const rowCategories: { [row: number]: string } = {};
    topics.forEach(topic => {
      if (rowCategories[topic.row] === undefined) rowCategories[topic.row] = topic.category;
    });
    if (topics.length === 0) rowCategories[0] = '—';
    return { rowCategories };
  };

  const { rowCategories } = getRowInfo();
  const rows = Object.keys(rowCategories).map(Number).sort((a, b) => a - b);
  /** Top of plot area (align with Emotion Analysis: grid starts here). */
  const topPadding = 20;
  /** Plot area height so last row meets x-axis strip (responsive like Emotion Analysis). */
  const plotHeight = chartHeight - topPadding - STICKY_X_HEIGHT;
  const rowCount = Math.max(rows.length, 1);
  const rowHeight = plotHeight / rowCount;
  /** Row center Y for row index i (responsive). */
  const getRowCenterY = (rowNum: number) => topPadding + (rowNum + 0.5) * rowHeight;
  /** Row top Y for drawing rects (responsive). */
  const getRowTopY = (rowNum: number) => topPadding + rowNum * rowHeight;
  const totalHeight = chartHeight;
  /** Enough space so y-axis labels (e.g. "Technology") don't overlap the left edge of the plot when scrolled. */
  const leftPadding = 70;
  const rightPadding = 10;
  const pixelsPerSecond = 17;
  /** Total time range in seconds (from data or default). */
  const totalSeconds =
    topics.length >= 2
      ? Math.max(Math.ceil((topics[topics.length - 1].timestamp.getTime() - topics[0].timestamp.getTime()) / 1000) + 10, 30)
      : 30;
  /** Plot width: at least fill container (responsive), or wider for horizontal scroll when timeline is long. */
  const containerPlotWidth = containerWidth > 0 ? containerWidth - leftPadding - rightPadding : 400;
  const timeBasedChartWidth = totalSeconds * pixelsPerSecond;
  const chartWidth = Math.max(containerPlotWidth, timeBasedChartWidth);
  const totalWidth = leftPadding + chartWidth + rightPadding;

  const getTimeBasedPositions = () => {
    const startTime = topics.length > 0 ? topics[0].timestamp.getTime() : Date.now() - totalSeconds * 1000;
    const timeMarks: { time: Date; x: number; label: string }[] = [];
    for (let sec = 0; sec <= totalSeconds; sec += 5) {
      const markTime = new Date(startTime + sec * 1000);
      const x = leftPadding + (sec / totalSeconds) * chartWidth;
      timeMarks.push({
        time: markTime,
        x,
        label: markTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      });
    }
    return { startTime, totalSeconds, timeMarks };
  };

  const { startTime, timeMarks } = getTimeBasedPositions();
  const getTopicX = (topic: TopicNode) => {
    const elapsedSeconds = (topic.timestamp.getTime() - startTime) / 1000;
    return leftPadding + (elapsedSeconds / totalSeconds) * chartWidth;
  };
  /** Min offset from left so first topic dot + label are not clipped by sticky y-axis. */
  const MIN_FIRST_TOPIC_OFFSET = 52;
  const getTopicXDisplay = (topic: TopicNode, index: number) => {
    const x = getTopicX(topic);
    return index === 0 ? Math.max(x, leftPadding + MIN_FIRST_TOPIC_OFFSET) : x;
  };

  return (
    <div className="sync-card">
      <div ref={bodyRef} className="sync-card-body">
        <div
          ref={scrollRef}
          className="sync-scroll-area-both"
          onScroll={handleScrollInternal}
        >
          <div ref={containerRef} className="sync-chart-inner" style={{ height: `${totalHeight}px`, width: `${totalWidth}px` }}>
            <svg width={totalWidth} height={totalHeight}>
                  {rows.map((rowNum) => (
                    <rect
                      key={`row-${rowNum}`}
                      x={leftPadding}
                      y={getRowTopY(rowNum)}
                      width={chartWidth}
                      height={rowHeight}
                      fill="transparent"
                      stroke="var(--sync-grid-line-color)"
                      strokeOpacity={1}
                      strokeWidth={1}
                    />
                  ))}
                  {timeMarks.map((mark, index) => (
                    <line
                      key={`grid-v-${index}`}
                      x1={mark.x}
                      y1={topPadding}
                      x2={mark.x}
                      y2={chartHeight - STICKY_X_HEIGHT}
                      stroke="var(--sync-grid-line-color-vertical, var(--sync-grid-line-color))"
                      strokeWidth={1}
                      strokeDasharray="2,3"
                      opacity={1}
                    />
                  ))}
                  {/* Connection lines only (no boxes yet) */}
                  {topics.map((topic, index) => {
                    if (index === 0) return null;
                    const prevTopic = topics[index - 1];
                    const x1 = getTopicXDisplay(prevTopic, index - 1);
                    const x2 = getTopicXDisplay(topic, index);
                    const y1 = getRowCenterY(prevTopic.row);
                    const y2 = getRowCenterY(topic.row);
                    return (
                      <motion.line
                        key={`connection-${topic.id}`}
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#7D7D7D"
                        strokeWidth={1.5}
                        strokeDasharray="4,4"
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 0.5 }}
                        transition={{ delay: index * 0.1, duration: 0.4 }}
                      />
                    );
                  })}
                  {/* Topic nodes (dots + names) drawn first so they sit under yellow boxes */}
                  {topics.map((topic, index) => {
                    const x = getTopicXDisplay(topic, index);
                    const y = getRowCenterY(topic.row);
                    return (
                      <g key={topic.id}>
                        <motion.circle
                          cx={x}
                          cy={y}
                          r={6}
                          fill="#f43f5e"
                          stroke="#1f2937"
                          strokeWidth={2}
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ delay: index * 0.1 + 0.1, duration: 0.3 }}
                        />
                        <motion.text
                          x={x}
                          y={y - 15}
                          fontSize="12"
                          fontWeight="500"
                          fill="white"
                          textAnchor="middle"
                          initial={{ opacity: 0, y: -5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 + 0.2, duration: 0.4 }}
                        >
                          {topic.name}
                        </motion.text>
                      </g>
                    );
                  })}
                  {/* Yellow AI transition boxes on top so their text is never covered by dots */}
                  {topics.map((topic, index) => {
                    if (index === 0 || !topic.aiRole) return null;
                    const prevTopic = topics[index - 1];
                    const x1 = getTopicXDisplay(prevTopic, index - 1);
                    const x2 = getTopicXDisplay(topic, index);
                    const y1 = getRowCenterY(prevTopic.row);
                    const y2 = getRowCenterY(topic.row);
                    const label = getTransitionLabel(topic.aiRole, prevTopic.name);
                    const boxWidth = Math.max(60, label.length * 7 + 16);
                    return (
                      <motion.g
                        key={`transition-box-${topic.id}`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: index * 0.1 + 0.2, duration: 0.3 }}
                      >
                        <rect x={(x1 + x2) / 2 - boxWidth / 2} y={(y1 + y2) / 2 - 10} width={boxWidth} height={20}
                          fill="rgba(234, 179, 8, 0.15)" stroke="#eab308" strokeWidth={1} rx={3} />
                        <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 + 1} fontSize="10" fontWeight="600"
                          fill="#eab308" textAnchor="middle" dominantBaseline="middle">{label}</text>
                      </motion.g>
                    );
                  })}
                </svg>
              </div>
            </div>
            <div className="sync-sticky-y" style={{ width: `${leftPadding}px` }}>
              <svg width={leftPadding} height="100%" viewBox={`0 0 ${leftPadding} ${chartHeight}`} preserveAspectRatio="xMinYMin slice">
                {rows.map((rowNum) => (
                  <text key={`y-label-${rowNum}`} x={leftPadding - 10} y={getRowCenterY(rowNum)} fontSize="9" fill="#7D7D7D"
                    textAnchor="end" dominantBaseline="middle" style={{ fontFamily: 'monospace' }}>
                    {rowCategories[rowNum]}
                  </text>
                ))}
              </svg>
            </div>
            <div className="sync-sticky-x">
              <svg width="100%" height="56" viewBox={`${scrollLeft} 0 ${scrollRef.current?.clientWidth || 800} 56`} preserveAspectRatio="xMinYMin slice">
                <line x1={leftPadding} y1={0} x2={leftPadding + chartWidth} y2={0} stroke="var(--sync-grid-line-color-vertical, var(--sync-grid-line-color))" strokeWidth={1} />
                {timeMarks.map((mark, index) => (
                  <text key={`time-${index}`} x={mark.x} y={20} textAnchor="middle" style={{ fontFamily: 'monospace', fontSize: 'var(--sync-x-axis-label-font-size)' }} fill="var(--sync-x-axis-label-color)">
                    {mark.label}
                  </text>
                ))}
              </svg>
            </div>
            {isManuallyControlled && (
              <button className="sync-scroll-to-latest" onClick={scrollToLatest} title="Scroll to latest">
                →
              </button>
            )}
      </div>
      <div className="sync-legend">
        <div className="sync-legend-item">
          <div className="sync-legend-dot rose" />
          <span className="sync-legend-text">User topics</span>
        </div>
        <div className="sync-legend-item">
          <div className="sync-legend-dot orange" />
          <span className="sync-legend-text">AI interactions</span>
        </div>
      </div>
    </div>
  );
}
