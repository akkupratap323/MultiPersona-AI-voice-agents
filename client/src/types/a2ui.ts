/**
 * A2UI (Agent-to-UI) Type Definitions for Nester AI Voice Assistant
 *
 * These types define the structure of A2UI visual components generated
 * by the backend orchestrator based on user queries and LLM responses.
 */

// Base A2UI Document structure (v1 nested format)
export interface A2UIDocument {
  version: string;
  root: A2UIRoot;
  _metadata?: A2UIMetadata;
}

export interface A2UIRoot {
  type: A2UITemplateType;
  props: A2UIProps;
}

export interface A2UIMetadata {
  tier: string;
  tier_name: string;
  template_type: string;
  mode: string;
  description: string;
}

// All supported template types
export type A2UITemplateType =
  | 'simple-card'
  | 'template-grid'
  | 'timeline'
  | 'contact-card'
  | 'comparison-chart'
  | 'stats-flow-layout'
  | 'stats-chart'
  | 'team-flip-cards'
  | 'service-hover-reveal'
  | 'magazine-hero'
  | 'faq-accordion'
  | 'blog-magazine'
  | 'image-gallery'
  | 'video-gallery'
  | 'sales-dashboard';

// Props union type for all templates
export type A2UIProps =
  | SimpleCardProps
  | TemplateGridProps
  | TimelineProps
  | ContactCardProps
  | ComparisonChartProps
  | StatsFlowLayoutProps
  | StatsChartProps
  | TeamFlipCardsProps
  | ServiceHoverRevealProps
  | MagazineHeroProps
  | FAQAccordionProps
  | BlogMagazineProps
  | ImageGalleryProps
  | VideoGalleryProps
  | SalesDashboardProps;

// ==================== Template Props ====================

export interface SimpleCardProps {
  title: string;
  content: string;
  icon?: string;
}

export interface TemplateGridProps {
  title: string;
  templates: TemplateGridItem[];
  columns?: number;
  showSearch?: boolean;
  showCount?: boolean;
}

export interface TemplateGridItem {
  name: string;
  description: string;
  category?: string;
  icon?: string;
  tags?: string[];
  url?: string;
}

export interface TimelineProps {
  title: string;
  events: TimelineEvent[];
  orientation?: 'vertical' | 'horizontal';
}

export interface TimelineEvent {
  year: string;
  title: string;
  description: string;
  icon?: string;
}

export interface ContactCardProps {
  title: string;
  contacts: ContactItem[];
}

export interface ContactItem {
  type: 'email' | 'phone' | 'address' | 'website' | 'social' | 'info';
  value: string;
  description?: string;
  icon?: string;
}

export interface ComparisonChartProps {
  title: string;
  items: ComparisonItem[];
}

export interface ComparisonItem {
  name: string;
  features: ComparisonFeature[];
  recommended?: boolean;
  icon?: string;
}

export interface ComparisonFeature {
  feature: string;
  value: string;
}

export interface StatsFlowLayoutProps {
  title: string;
  topStats: StatItem[];
  radialProgress?: RadialProgressItem;
  performanceMetrics?: StatItem[];
  bottomStats?: StatItem[];
}

export interface StatItem {
  label: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export interface RadialProgressItem {
  label: string;
  completion_rate: string;
}

export interface StatsChartProps {
  title: string;
  stats: StatItem[];
  charts: ChartItem[];
}

export interface ChartItem {
  type: 'bar' | 'line' | 'pie' | 'table';
  title: string;
  data: ChartDataPoint[];
  xAxisKey?: string;
  yAxisKey?: string;
  orientation?: 'horizontal' | 'vertical';
}

export interface ChartDataPoint {
  name: string;
  value: number;
}

export interface TeamFlipCardsProps {
  title: string;
  members: TeamMember[];
}

export interface TeamMember {
  name: string;
  role: string;
  bio?: string;
  image?: string;
  email?: string;
  linkedin?: string;
}

export interface ServiceHoverRevealProps {
  title: string;
  services: ServiceItem[];
}

export interface ServiceItem {
  name: string;
  description: string;
  fullDescription?: string;
  icon?: string;
}

export interface MagazineHeroProps {
  title: string;
  subtitle?: string;
  content: string;
  image?: string;
  metadata?: {
    author?: string;
    date?: string;
  };
  projectInfo?: {
    year?: string;
    team?: string;
    duration?: string;
  };
  services?: string[];
  tags?: string[];
  pullQuote?: string;
}

export interface FAQAccordionProps {
  title: string;
  faqs: FAQItem[];
  variant?: 'searchable' | 'simple';
}

export interface FAQItem {
  question: string;
  answer: string;
  category?: string;
}

export interface BlogMagazineProps {
  title: string;
  posts: BlogPost[];
  variant?: 'magazine' | 'list';
}

export interface BlogPost {
  title: string;
  excerpt: string;
  category?: string;
  author?: string;
  date?: string;
  readTime?: string;
  image?: string;
  featured?: boolean;
}

export interface ImageGalleryProps {
  title: string;
  images: ImageItem[];
  layout?: 'grid' | 'masonry' | 'carousel';
}

export interface ImageItem {
  url: string;
  caption?: string;
  alt?: string;
}

export interface VideoGalleryProps {
  title: string;
  videos: VideoItem[];
  layout?: 'grid' | 'list';
}

export interface VideoItem {
  url: string;
  title: string;
  description?: string;
  thumbnail?: string;
}

export interface SalesDashboardProps {
  title: string;
  subtitle?: string;
  kpiCards: KPICard[];
  charts: ChartItem[];
}

export interface KPICard {
  title: string;
  value: string;
  subtitle?: string;
  icon?: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger';
}

// ==================== WebSocket Message Types ====================

export interface A2UIUpdateMessage {
  message_type: 'a2ui_update';
  a2ui: A2UIDocument;
  utterance_id: string;
  timestamp: number;
}

export interface StreamingTextMessage {
  message_type: 'streaming_text';
  text: string;
  is_final: boolean;
  sequence_id: number;
  utterance_id: string;
  timestamp: number;
}

export interface VisualHintMessage {
  message_type: 'visual_hint';
  hint_type: string;
  content_type: string;
  content: Record<string, any>;
  confidence: number;
  trigger_text: string;
  timestamp: number;
}

// Union type for all message types
export type A2UIMessage = A2UIUpdateMessage | StreamingTextMessage | VisualHintMessage;

// ==================== Helper Functions ====================

/**
 * Check if a message is an A2UI update
 */
export function isA2UIUpdate(msg: any): msg is A2UIUpdateMessage {
  return msg?.message_type === 'a2ui_update' && msg?.a2ui;
}

/**
 * Check if a message is streaming text
 */
export function isStreamingText(msg: any): msg is StreamingTextMessage {
  return msg?.message_type === 'streaming_text';
}

/**
 * Check if a message is a visual hint (legacy)
 */
export function isVisualHint(msg: any): msg is VisualHintMessage {
  return msg?.message_type === 'visual_hint';
}

/**
 * Get template type from A2UI document
 */
export function getTemplateType(doc: A2UIDocument): A2UITemplateType {
  return doc?.root?.type || 'magazine-hero';
}

/**
 * Get tier name from A2UI metadata
 */
export function getTierName(doc: A2UIDocument): string {
  return doc?._metadata?.tier_name || 'Unknown';
}
