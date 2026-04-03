import { useMemo, useRef, useState, useEffect } from 'react';
import './ToneModulator.css';

const EMOTION_EMOJIS: Record<string, string> = {
  neutral: '😐',
  excited: '😄',
  frustrated: '😤',
  sad: '😢',
  calm: '😌',
  happy: '😊',
};

const TONE_LABELS: Record<string, string> = {
  neutral: 'Neutral',
  calm: 'Calm',
  excited: 'Excited',
  frustrated: 'Frustrated',
  sad: 'Sad',
};

export interface ToneModulatorProps {
  detectedEmotion: string;
  nesterResponse: string;
  clarityData: number[];
  intensityData: number[];
  /** X-axis grid interval in seconds (default: 5) */
  xAxisIntervalSec?: number;
}

const MAX_POINTS = 24;
const DEFAULT_X_AXIS_INTERVAL_SEC = 5;
const MIN_CHART_HEIGHT = 60;
const CHART_BLOCKS_GAP = 12;

function MiniLineChart({
  data,
  color,
  height = 60,
  yTopLabel,
  yBottomLabel,
  xAxisIntervalSec = DEFAULT_X_AXIS_INTERVAL_SEC,
}: {
  data: number[];
  color: string;
  height?: number;
  yTopLabel: string;
  yBottomLabel: string;
  xAxisIntervalSec?: number;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(250);
  useEffect(() => {
    if (!wrapRef.current) return;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);
  const padding = { top: 14, right: 8, bottom: 22, left: 14 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const path = useMemo(() => {
    const raw = data.length >= 2 ? data.slice(-MAX_POINTS) : data.length === 1 ? [data[0], data[0]] : [0.5, 0.5];
    const points = raw;
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min || 1;
    const xStep = chartWidth / Math.max(points.length - 1, 1);
    const coords = points.map((v, i) => {
      const x = padding.left + i * xStep;
      const y = padding.top + (1 - (v - min) / range) * chartHeight;
      return `${x},${y}`;
    });
    return `M ${coords.join(' L ')}`;
  }, [data, chartWidth, chartHeight, padding.left, padding.top]);

  const points = data.length >= 2 ? data.slice(-MAX_POINTS) : data.length === 1 ? [data[0], data[0]] : [0.5, 0.5];
  const lastValue = points[points.length - 1];
  const lastX = padding.left + (points.length - 1) * (chartWidth / Math.max(points.length - 1, 1));
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const lastY = padding.top + (1 - (lastValue - min) / range) * chartHeight;

  const xLabels = useMemo(() => {
    const n = points.length;
    return Array.from({ length: n }, (_, i) => i * xAxisIntervalSec);
  }, [points.length, xAxisIntervalSec]);

  return (
    <div className="tone-mini-chart">
      <div className="tone-chart-y-labels">
        <span className="tone-chart-y-top">{yTopLabel}</span>
        <span className="tone-chart-y-bottom">{yBottomLabel}</span>
      </div>
      <div ref={wrapRef} className="tone-chart-svg-wrap">
        <svg width={width} height={height} className="tone-chart-svg">
        <defs>
          <linearGradient id={`grid-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(255,255,255,0.03)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0)" />
          </linearGradient>
        </defs>
        {/* Grid lines: horizontal dotted lines at 0, 0.2, 0.4, 0.6, 0.8, 1 */}
        {[0, 0.2, 0.4, 0.6, 0.8, 1].map((v, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={padding.top + (1 - v) * chartHeight}
              x2={width - padding.right}
              y2={padding.top + (1 - v) * chartHeight}
              stroke="rgba(255,255,255,0.12)"
              strokeDasharray="2 2"
              strokeWidth={1}
              className="tone-chart-grid-line"
            />
            <text
              x={padding.left - 6}
              y={padding.top + (1 - v) * chartHeight + 3}
              textAnchor="end"
              className="tone-chart-y-value"
              fontSize={4}
              fill="#7D7D7D"
            >
              {v === 0 || v === 1 ? v.toFixed(1) : v}
            </text>
          </g>
        ))}
        {/* Vertical grid lines at each X-axis tick */}
        {xLabels.map((_, i) => {
          const x = padding.left + (chartWidth / Math.max(points.length - 1, 1)) * i;
          return (
            <line
              key={`v-${i}`}
              x1={x}
              y1={padding.top}
              x2={x}
              y2={height - padding.bottom}
              stroke="rgba(255,255,255,0.12)"
              strokeDasharray="2 2"
              strokeWidth={1}
              className="tone-chart-grid-line"
            />
          );
        })}
        <path d={path} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={lastX} cy={lastY} r={4} fill="#F46C72" />
        {/* X-axis labels */}
        {xLabels.map((sec, i) => {
          const x = padding.left + (chartWidth / Math.max(points.length - 1, 1)) * i;
          return (
            <text
              key={i}
              x={x}
              y={height - 12}
              textAnchor={i === 0 ? 'start' : i === points.length - 1 ? 'end' : 'middle'}
              className="tone-chart-x-label"
              fontSize={4}
              fill="rgba(255,255,255,0.4) "
            >
              {sec}s
            </text>
          );
        })}
        </svg>
      </div>
    </div>
  );
}

export function ToneModulator({
  detectedEmotion = 'neutral',
  nesterResponse = 'calm',
  clarityData = [],
  intensityData = [],
  xAxisIntervalSec = DEFAULT_X_AXIS_INTERVAL_SEC,
}: ToneModulatorProps) {
  const chartsContainerRef = useRef<HTMLDivElement>(null);
  const [chartHeight, setChartHeight] = useState(MIN_CHART_HEIGHT);

  useEffect(() => {
    const el = chartsContainerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const h = entry.contentRect.height;
      const perChart = (h - CHART_BLOCKS_GAP) / 2;
      setChartHeight(Math.max(MIN_CHART_HEIGHT, Math.floor(perChart)));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const emotionEmoji = EMOTION_EMOJIS[detectedEmotion.toLowerCase()] || '😐';
  const emotionLabel = (detectedEmotion && detectedEmotion.charAt(0).toUpperCase() + detectedEmotion.slice(1)) || 'Neutral';
  const responseLabel = TONE_LABELS[nesterResponse.toLowerCase()] || nesterResponse || 'Calm';

  const clarity = clarityData.length > 0 ? clarityData : [0.5];
  const intensity = intensityData.length > 0 ? intensityData : [0.5];

  return (
    <div className="tone-modulator-widget">
      <div className="tone-modulator-header">
        <div className="tone-modulator-pills">
          <div className="tone-pill tone-pill-detected">
            <span className="tone-pill-label">Detected Emotion :</span>
            <span className="tone-pill-emoji">{emotionEmoji}</span>
            <span className="tone-pill-value">{emotionLabel}</span>
          </div>
          <div className="tone-pill-connector" />
          <div className="tone-pill tone-pill-response">
            <span className="tone-pill-label">Nester Response</span>
            <img src="/calm.svg" alt="" className="tone-pill-icon" />
            <span className="tone-pill-value">{responseLabel}</span>
          </div>
        </div>
      </div>

      <h3 className="tone-voice-title">Humanizing Voice control</h3>

      <div ref={chartsContainerRef} className="tone-chart-blocks">
        <div className="tone-chart-block">
          <span className="tone-chart-label">Clarity</span>
          <MiniLineChart
            data={clarity}
            color="#ffffff"
            height={chartHeight}
            yTopLabel="Assertive"
            yBottomLabel="Relaxed"
            xAxisIntervalSec={xAxisIntervalSec}
          />
        </div>

        <div className="tone-chart-block">
          <span className="tone-chart-label">Intensity</span>
          <MiniLineChart
            data={intensity}
            color="#F46C72"
            height={chartHeight}
            yTopLabel="Expressive"
            yBottomLabel="Subdued"
            xAxisIntervalSec={xAxisIntervalSec}
          />
        </div>
      </div>
    </div>
  );
}

export default ToneModulator;
