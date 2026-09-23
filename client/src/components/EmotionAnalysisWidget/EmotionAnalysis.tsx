import { useEffect, useMemo, useRef } from 'react';
import type { EmotionTopicNode } from './types';
import './EmotionAnalysis.css';

export interface EmotionAnalysisProps {
  topics: EmotionTopicNode[];
  hideTitle?: boolean;
}

/* ── Emotion → visual mapping ── */
const EMOTION_MAP: Record<string, { glyph: string; color: string; label: string }> = {
  Excited:   { glyph: 'EX', color: '#f59e0b', label: 'Excited' },
  Positive:  { glyph: '+', color: '#10b981', label: 'Positive' },
  Neutral:   { glyph: '—', color: '#94a3b8', label: 'Neutral' },
  Calm:      { glyph: 'CA', color: '#06b6d4', label: 'Calm' },
  Concerned: { glyph: '!', color: '#fb7185', label: 'Concerned' },
};

const AXIS_COLORS = {
  valence:    '#06b6d4',
  arousal:    '#f97316',
  dominance:  '#a855f7',
  engagement: '#22c55e',
  stability:  '#3b82f6',
};

/* ── Metric calculation from topic data ── */
function calculateMetrics(topic: EmotionTopicNode) {
  let valence = 0.5;
  if (topic.sentiment === 'positive') valence = 0.2 + topic.intensity * 0.6;
  if (topic.sentiment === 'negative') valence = 0.2 - topic.intensity * 0.2;
  const arousal = topic.intensity;
  let dominance = 0.5;
  if (topic.sentimentLabel === 'Excited') dominance = 0.7;
  if (topic.sentimentLabel === 'Positive') dominance = 0.6;
  if (topic.sentimentLabel === 'Concerned') dominance = 0.3;
  // Derived metrics
  const engagement = Math.min(1, (arousal + valence) / 2 + 0.1);
  const stability = Math.max(0, 1 - Math.abs(arousal - 0.5) * 2);
  return { valence, arousal, dominance, engagement, stability };
}

/* ── Pentagon geometry helpers ── */
const CX = 100, CY = 100;
const AXES = ['valence', 'arousal', 'dominance', 'engagement', 'stability'] as const;
const AXIS_LABELS = ['VALENCE', 'AROUSAL', 'DOM', 'ENG', 'STAB'];

function pentagonPoint(axisIndex: number, radius: number): [number, number] {
  // Start from top (–90°), go clockwise
  const angle = (Math.PI * 2 * axisIndex) / 5 - Math.PI / 2;
  return [CX + Math.cos(angle) * radius, CY + Math.sin(angle) * radius];
}

function pentagonPath(radius: number): string {
  return Array.from({ length: 5 }, (_, i) => pentagonPoint(i, radius))
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`)
    .join(' ') + ' Z';
}

function dataPolygonPoints(values: number[], maxRadius: number): string {
  return Array.from({ length: 5 }, (_, i) => {
    const r = values[i] * maxRadius;
    const [x, y] = pentagonPoint(i, r);
    return `${x},${y}`;
  }).join(' ');
}

/* ── Component ── */
export function EmotionAnalysis({ topics, hideTitle }: EmotionAnalysisProps) {
  const radarRef = useRef<SVGSVGElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  // Auto-scroll timeline
  useEffect(() => {
    if (timelineRef.current) {
      timelineRef.current.scrollLeft = timelineRef.current.scrollWidth;
    }
  }, [topics.length]);

  // Current emotion state (latest topic)
  const latest = topics.length > 0 ? topics[topics.length - 1] : null;
  const emotionInfo = latest ? (EMOTION_MAP[latest.sentimentLabel] || EMOTION_MAP.Neutral) : EMOTION_MAP.Neutral;
  const metrics = latest ? calculateMetrics(latest) : { valence: 0.5, arousal: 0.3, dominance: 0.5, engagement: 0.4, stability: 0.7 };
  const confidence = latest ? Math.round(latest.intensity * 100) : 0;

  // Confidence ring dashoffset (circumference = 2πr ≈ 213 for r=34)
  const ringCircumference = 213;
  const ringOffset = ringCircumference - (ringCircumference * confidence) / 100;

  const metricValues = [
    metrics.valence,
    metrics.arousal,
    metrics.dominance,
    metrics.engagement,
    metrics.stability,
  ];
  const recentTraces = useMemo(
    () => topics.slice(-4, -1).map((topic) => {
      const point = calculateMetrics(topic);
      return [point.valence, point.arousal, point.dominance, point.engagement, point.stability];
    }),
    [topics],
  );

  const maxRadius = 70;

  return (
    <div className="ea-card">
      {/* ── Top: Current State ── */}
      <section className="ea-state">
        <div className="ea-emoji-ring">
          <div className="ea-particle-glow" style={{ background: `radial-gradient(circle, ${emotionInfo.color}22 0%, transparent 70%)` }} />
          <div className="ea-emoji-circle" style={{ borderColor: `${emotionInfo.color}80`, boxShadow: `0 0 20px ${emotionInfo.color}44` }}>
            {emotionInfo.glyph}
          </div>
          <svg className="ea-confidence-ring" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="34" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="2" />
            <circle cx="36" cy="36" r="34" fill="none" stroke={emotionInfo.color} strokeWidth="2"
              strokeDasharray={ringCircumference} strokeDashoffset={ringOffset}
              strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.5s ease' }} />
          </svg>
        </div>
        <div className="ea-state-info">
          <span className="ea-state-label">CURRENT SIGNAL</span>
          <span className="ea-state-emotion">{emotionInfo.label}</span>
          <div className="ea-state-confidence">
            <span className="ea-confidence-dot" style={{ background: '#22c55e' }} />
            <span className="ea-confidence-text">CONFIDENCE: {confidence}%</span>
          </div>
        </div>
        <div className="ea-live-meta">
          <span className="ea-live-pill"><i /> LIVE</span>
          <span className="ea-sample-count">{topics.length} SIGNAL{topics.length === 1 ? '' : 'S'}</span>
        </div>
      </section>

      {/* ── Center: 3D Radar ── */}
      <section className="ea-radar-section">
        <div className="ea-radar-container">
          <svg className="ea-radar-svg" viewBox="0 0 200 200" overflow="visible">
            <defs>
              <linearGradient id="eaRadarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={`${emotionInfo.color}66`} />
                <stop offset="100%" stopColor={`${emotionInfo.color}22`} />
              </linearGradient>
              <radialGradient id="eaRadarHalo">
                <stop offset="0%" stopColor={`${emotionInfo.color}22`} />
                <stop offset="72%" stopColor={`${emotionInfo.color}08`} />
                <stop offset="100%" stopColor={emotionInfo.color} stopOpacity="0" />
              </radialGradient>
            </defs>

            <circle cx={CX} cy={CY} r="92" fill="url(#eaRadarHalo)" className="ea-radar-halo" />

            {/* Concentric pentagon grid */}
            {[0.2, 0.4, 0.6, 0.8, 1.0].map(level => (
              <path key={level} d={pentagonPath(level * maxRadius)} fill="none"
                stroke="rgba(255,255,255,0.07)" strokeWidth="0.5" />
            ))}

            {/* Axis lines */}
            {AXES.map((_, i) => {
              const [ex, ey] = pentagonPoint(i, maxRadius);
              return <line key={i} x1={CX} y1={CY} x2={ex} y2={ey} stroke="rgba(255,255,255,0.07)" strokeWidth="0.5" />;
            })}

            {/* Recent signal traces give the graph a sense of motion and history. */}
            {recentTraces.map((values, index) => (
              <polygon
                key={index}
                points={dataPolygonPoints(values, maxRadius)}
                fill="none"
                stroke={emotionInfo.color}
                strokeWidth="0.7"
                opacity={(index + 1) * 0.1}
                className="ea-history-polygon"
              />
            ))}

            {/* Current signal polygon */}
            <polygon
              points={dataPolygonPoints(metricValues, maxRadius)}
              fill="url(#eaRadarGrad)"
              stroke={emotionInfo.color}
              strokeWidth="1.5"
              className="ea-current-polygon"
              style={{ filter: `drop-shadow(0 0 10px ${emotionInfo.color}55)`, transition: 'fill 0.5s ease, stroke 0.5s ease' }}
            />
            <circle cx={CX} cy={CY} r="3" fill={emotionInfo.color} className="ea-radar-core" />

            {/* Axis endpoint dots & labels */}
            {AXES.map((axis, i) => {
              const [px, py] = pentagonPoint(i, maxRadius + 4);
              const [lx, ly] = pentagonPoint(i, maxRadius + 16);
              const value = metricValues[i];
              const color = AXIS_COLORS[axis];
              // Text anchor based on position
              const anchor = lx < 80 ? 'end' : lx > 120 ? 'start' : 'middle';
              const labelY = ly < 50 ? ly - 2 : ly + 6;
              return (
                <g key={axis}>
                  <circle cx={px} cy={py} r="2" fill={color} style={{ filter: `drop-shadow(0 0 4px ${color})` }}>
                    <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" />
                  </circle>
                  <text x={lx} y={labelY} textAnchor={anchor} fill="rgba(255,255,255,0.45)"
                    fontSize="6.5" fontFamily="'JetBrains Mono', monospace" fontWeight="500">
                    {AXIS_LABELS[i]} {value.toFixed(2)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </section>

      <section className="ea-metric-strip">
        {AXES.map((axis, index) => (
          <div className="ea-metric" key={axis}>
            <div className="ea-metric-copy">
              <span>{AXIS_LABELS[index]}</span>
              <strong>{Math.round(metricValues[index] * 100)}</strong>
            </div>
            <div className="ea-metric-track">
              <span style={{ width: `${metricValues[index] * 100}%`, background: AXIS_COLORS[axis] }} />
            </div>
          </div>
        ))}
      </section>

      {/* ── Bottom: Timeline Strip ── */}
      <section className="ea-timeline-section">
        <div className="ea-timeline-header">
          <span className="ea-timeline-label">SIGNAL HISTORY</span>
          <button className="ea-timeline-btn" onClick={() => {
            if (timelineRef.current) timelineRef.current.scrollLeft = timelineRef.current.scrollWidth;
          }}>→</button>
        </div>
        <div className="ea-timeline-track" ref={timelineRef}>
          <svg className="ea-timeline-svg" width={Math.max(200, topics.length * 40 + 20)} height="20">
            {/* Connecting line */}
            {topics.length > 1 && (
              <path
                d={topics.map((_, i) => `${i === 0 ? 'M' : 'L'}${10 + i * 40},10`).join(' ')}
                fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1"
              />
            )}
            {/* Dots */}
            {topics.map((topic, i) => {
              const info = EMOTION_MAP[topic.sentimentLabel] || EMOTION_MAP.Neutral;
              const isLast = i === topics.length - 1;
              return (
                <circle key={topic.id} cx={10 + i * 40} cy={10} r={isLast ? 4 : 3}
                  fill={info.color} stroke={isLast ? 'rgba(255,255,255,0.2)' : 'none'} strokeWidth="2">
                  <title>{topic.sentimentLabel} — {topic.timestamp.toLocaleTimeString()}</title>
                </circle>
              );
            })}
          </svg>
        </div>
      </section>
    </div>
  );
}

export default EmotionAnalysis;
