/**
 * Wave Visualization Configuration
 * 
 * This configuration controls the layered wave animation that rises from the bottom
 * of the canvas. The wave creates a depth effect using multiple layers with different
 * heights, colors, and blur values.
 * 
 * Layer Order (drawing): Back (2) -> Middle (1) -> Front (0)
 * Visual Order (perceived): Front is closest to viewer, Back is furthest
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Configuration for a single wave layer
 */
export interface WaveLayerConfig {
  /** RGBA color string for this layer (e.g., 'rgba(255, 255, 255, 1)') */
  color: string;
  /** Height multiplier for wave amplitude (higher = taller waves) */
  heightScale: number;
  /** Blur amount in pixels (higher = more blur/glow effect) */
  blur: number;
}

/**
 * Main wave visualization configuration
 */
export interface WaveVisualizationConfig {
  /** Number of points used to draw the wave curve (higher = smoother) */
  numPoints: number;
  /** Maximum height the wave can reach as a percentage of canvas height (0-1) */
  maxWaveHeightRatio: number;
  /** Time offset multiplier between layers for organic movement */
  layerTimeOffset: number;
  /** Speed multiplier increase per layer */
  layerSpeedIncrement: number;
  /** Edge fade power for smooth tapering at sides (lower = more fade) */
  edgeFadePower: number;
  /** Organic wave amplitude for subtle movement */
  organicWaveAmplitude: number;
  /** Configuration for each wave layer (front to back) */
  layers: WaveLayerConfig[];
}

// ============================================================================
// COLOR PALETTE
// ============================================================================

/**
 * Color palette for wave visualization
 * These hex colors are converted to RGBA for use in the canvas
 */
export const WAVE_COLORS = {
  /** Very light red - used for front layer */
  TOP: '#FEF1F1',
  /** Soft red/salmon - used for middle layer */
  MIDDLE: '#F46C72',
  /** Vivid red - used for back layer */
  BOTTOM: '#EF3139',
} as const;

/**
 * Helper to convert hex color to rgba string
 */
export function hexToRgba(hex: string, alpha: number = 1): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return `rgba(0, 0, 0, ${alpha})`;
  
  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);
  
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// ============================================================================
// DEFAULT CONFIGURATION
// ============================================================================

/**
 * Default wave visualization configuration
 * 
 * Layer Structure:
 * - Layer 0 (Front): Smallest, lightest color, medium blur
 * - Layer 1 (Middle): Medium height, medium color, least blur
 * - Layer 2 (Back): Tallest, darkest/vivid color, most blur
 * 
 * The back layer being tallest creates depth illusion as it peeks over the front layers
 */
export const DEFAULT_WAVE_CONFIG: WaveVisualizationConfig = {
  // Wave curve resolution
  numPoints: 120,
  
  // Maximum height as ratio of canvas height
  maxWaveHeightRatio: 0.85,
  
  // Layer animation offsets
  layerTimeOffset: 0.3,
  layerSpeedIncrement: 0.2,
  
  // Edge fade for smooth sides
  edgeFadePower: 0.6,
  
  // Organic wave movement amplitude
  organicWaveAmplitude: 0.08,
  
  // Layer configurations (index 0 = front, index 2 = back)
  layers: [
    {
      // Layer 0 - FRONT (drawn last, appears closest)
      color: hexToRgba(WAVE_COLORS.TOP, 1),      // Very Light Red
      heightScale: 0.2,                           // Shortest
      blur: 35,                                   // Medium blur
    },
    {
      // Layer 1 - MIDDLE
      color: hexToRgba(WAVE_COLORS.MIDDLE, 1),   // Soft Red/Salmon
      heightScale: 0.7,                           // Medium height
      blur: 25.9,                                 // Least blur (sharpest)
    },
    {
      // Layer 2 - BACK (drawn first, appears furthest)
      color: hexToRgba(WAVE_COLORS.BOTTOM, 1),   // Vivid Red
      heightScale: 1.4,                           // Tallest
      blur: 54.7,                                 // Most blur (depth effect)
    },
  ],
};

// ============================================================================
// PRESET CONFIGURATIONS (for future use)
// ============================================================================

/**
 * Alternative preset: Subtle/Minimal wave effect
 */
export const SUBTLE_WAVE_CONFIG: WaveVisualizationConfig = {
  ...DEFAULT_WAVE_CONFIG,
  maxWaveHeightRatio: 0.5,
  organicWaveAmplitude: 0.04,
  layers: [
    { color: hexToRgba(WAVE_COLORS.TOP, 0.6), heightScale: 0.15, blur: 20 },
    { color: hexToRgba(WAVE_COLORS.MIDDLE, 0.5), heightScale: 0.4, blur: 15 },
    { color: hexToRgba(WAVE_COLORS.BOTTOM, 0.4), heightScale: 0.8, blur: 30 },
  ],
};

/**
 * Alternative preset: Intense/Bold wave effect
 */
export const INTENSE_WAVE_CONFIG: WaveVisualizationConfig = {
  ...DEFAULT_WAVE_CONFIG,
  maxWaveHeightRatio: 0.95,
  organicWaveAmplitude: 0.12,
  layers: [
    { color: hexToRgba(WAVE_COLORS.TOP, 1), heightScale: 0.3, blur: 25 },
    { color: hexToRgba(WAVE_COLORS.MIDDLE, 1), heightScale: 0.9, blur: 20 },
    { color: hexToRgba(WAVE_COLORS.BOTTOM, 1), heightScale: 1.6, blur: 45 },
  ],
};

// ============================================================================
// EXPORTED ACTIVE CONFIGURATION
// ============================================================================

/**
 * Active wave configuration used by the application
 * Change this to use different presets or custom configurations
 */
export const waveConfig = DEFAULT_WAVE_CONFIG;
