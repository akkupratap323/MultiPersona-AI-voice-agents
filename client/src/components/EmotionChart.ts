/**
 * EmotionChart - Real-time line chart for emotion metrics
 * Displays Arousal, Dominance, and Valence as three lines on a single plot
 */

export interface EmotionDataPoint {
  arousal: number;
  dominance: number;
  valence: number;
  timestamp: number;
}

export class EmotionChart {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private data: EmotionDataPoint[] = [];
  private maxDataPoints: number = 30;
  private animationId: number | null = null;

  // Colors with high contrast between metrics
  private metrics = [
    { key: 'valence' as const, label: 'V', color: '#3b82f6', fullName: 'VALENCE' },      // Blue
    { key: 'arousal' as const, label: 'A', color: '#ef4444', fullName: 'AROUSAL' },      // Bright Red
    { key: 'dominance' as const, label: 'D', color: '#f59e0b', fullName: 'DOMINANCE' },  // Amber/Orange
  ];

  private colors = {
    grid: 'rgba(255, 255, 255, 0.08)',
    gridStrong: 'rgba(255, 255, 255, 0.15)',
    text: 'rgba(255, 255, 255, 0.5)',
    textBright: 'rgba(255, 255, 255, 0.8)',
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

    // Delay initial resize to ensure DOM is ready
    setTimeout(() => {
      this.resizeCanvas();
      // Start animation loop after resize
      this.animate();
    }, 100);

    window.addEventListener('resize', () => this.resizeCanvas());

    // Initialize with neutral baseline
    const now = Date.now();
    this.data.push({
      valence: 0.5,
      arousal: 0.5,
      dominance: 0.5,
      timestamp: now,
    });

  }

  private resizeCanvas(): void {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    // Use fixed height if rect is 0
    const width = rect.width || 200;
    const height = rect.height || 100;

    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.ctx.setTransform(1, 0, 0, 1, 0, 0); // Reset transform
    this.ctx.scale(dpr, dpr);

  }

  /**
   * Add a new data point - called once per conversation turn
   */
  public addDataPoint(arousal: number, dominance: number, valence: number): void {
    this.data.push({
      arousal: Math.max(0, Math.min(1, arousal)),
      dominance: Math.max(0, Math.min(1, dominance)),
      valence: Math.max(0, Math.min(1, valence)),
      timestamp: Date.now(),
    });

    // Keep only the last maxDataPoints
    if (this.data.length > this.maxDataPoints) {
      this.data.shift();
    }

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

    const padding = { top: 10, right: 45, bottom: 5, left: 20 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    if (chartWidth <= 0 || chartHeight <= 0) return;

    // Clear canvas
    this.ctx.clearRect(0, 0, width, height);

    // Draw background grid
    this.drawGrid(chartWidth, chartHeight, padding);

    // Draw lines for each metric (need at least 2 points for lines)
    if (this.data.length >= 2) {
      this.metrics.forEach((metric) => {
        this.drawLine(metric.key, metric.color, chartWidth, chartHeight, padding);
      });
    }

    // Always draw current values if we have data
    if (this.data.length > 0) {
      this.drawCurrentValues(chartHeight, padding, width);
    }
  }

  private drawGrid(
    chartWidth: number,
    chartHeight: number,
    padding: { top: number; right: number; bottom: number; left: number }
  ): void {
    const width = this.canvas.width / (window.devicePixelRatio || 1);

    // Horizontal grid lines (0, 0.5, 1)
    this.ctx.strokeStyle = this.colors.grid;
    this.ctx.lineWidth = 1;

    for (let i = 0; i <= 2; i++) {
      const y = padding.top + (chartHeight * i) / 2;
      this.ctx.beginPath();
      this.ctx.moveTo(padding.left, y);
      this.ctx.lineTo(width - padding.right, y);
      this.ctx.stroke();

      // Y-axis labels
      this.ctx.fillStyle = this.colors.text;
      this.ctx.font = '9px "JetBrains Mono", monospace';
      this.ctx.textAlign = 'right';
      const value = 1 - i * 0.5;
      this.ctx.fillText(value.toFixed(1), padding.left - 5, y + 3);
    }

    // Draw center line stronger
    this.ctx.strokeStyle = this.colors.gridStrong;
    this.ctx.beginPath();
    this.ctx.moveTo(padding.left, padding.top + chartHeight / 2);
    this.ctx.lineTo(width - padding.right, padding.top + chartHeight / 2);
    this.ctx.stroke();
  }

  private drawLine(
    metric: 'arousal' | 'dominance' | 'valence',
    color: string,
    chartWidth: number,
    chartHeight: number,
    padding: { top: number; right: number; bottom: number; left: number }
  ): void {
    if (this.data.length < 2) return;

    // Draw glow effect first (thicker, more transparent)
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 6;
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';
    this.ctx.globalAlpha = 0.2;

    this.ctx.beginPath();
    this.data.forEach((point, index) => {
      const x = padding.left + (index / (this.maxDataPoints - 1)) * chartWidth;
      const y = padding.top + (1 - point[metric]) * chartHeight;

      if (index === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    });
    this.ctx.stroke();
    this.ctx.globalAlpha = 1;

    // Draw main line
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 2.5;

    this.ctx.beginPath();
    this.data.forEach((point, index) => {
      const x = padding.left + (index / (this.maxDataPoints - 1)) * chartWidth;
      const y = padding.top + (1 - point[metric]) * chartHeight;

      if (index === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    });
    this.ctx.stroke();

    // Draw endpoint dot
    const lastPoint = this.data[this.data.length - 1];
    const lastX = padding.left + ((this.data.length - 1) / (this.maxDataPoints - 1)) * chartWidth;
    const lastY = padding.top + (1 - lastPoint[metric]) * chartHeight;

    // Glow
    this.ctx.beginPath();
    this.ctx.arc(lastX, lastY, 6, 0, Math.PI * 2);
    this.ctx.fillStyle = color;
    this.ctx.globalAlpha = 0.3;
    this.ctx.fill();
    this.ctx.globalAlpha = 1;

    // Dot
    this.ctx.beginPath();
    this.ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    this.ctx.fillStyle = color;
    this.ctx.fill();
  }

  private drawCurrentValues(
    chartHeight: number,
    padding: { top: number; right: number; bottom: number; left: number },
    width: number
  ): void {
    if (this.data.length === 0) return;

    const latest = this.data[this.data.length - 1];
    const x = width - padding.right + 6;

    this.ctx.font = 'bold 9px "JetBrains Mono", monospace';
    this.ctx.textAlign = 'left';

    // Fixed positions relative to center line: V above, A at center, D below
    const centerY = padding.top + chartHeight / 2;
    const spacing = 14;

    // V - above center
    this.ctx.fillStyle = this.metrics[0].color;
    this.ctx.fillText(`V:${latest.valence.toFixed(2)}`, x, centerY - spacing);

    // A - at center
    this.ctx.fillStyle = this.metrics[1].color;
    this.ctx.fillText(`A:${latest.arousal.toFixed(2)}`, x, centerY + 3);

    // D - below center
    this.ctx.fillStyle = this.metrics[2].color;
    this.ctx.fillText(`D:${latest.dominance.toFixed(2)}`, x, centerY + spacing + 6);
  }

  public destroy(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    window.removeEventListener('resize', () => this.resizeCanvas());
  }
}

// Export for global access
declare global {
  interface Window {
    EmotionChart: typeof EmotionChart;
  }
}

window.EmotionChart = EmotionChart;
