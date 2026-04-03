/**
 * Topic extraction from conversation messages.
 * Adapted from Voice Chat UI with Topic Flow.
 */

export interface Message {
  id: string;
  text: string;
  timestamp: Date;
  isFinal: boolean;
  speaker?: 'user' | 'ai';
}

export interface Topic {
  id: string;
  name: string;
  timestamp: Date;
  keywords: string[];
  parentId?: string;
  color: string;
  category: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentimentLabel: string;
  intensity: number;
  speaker?: 'user' | 'ai';
  aiRole?: string;
}

function detectAIRole(text: string): string {
  const lowerText = text.toLowerCase();
  const questionCount = (lowerText.match(/\?/g) || []).length;

  // Multiple questions = AI was asking follow-ups
  if (questionCount >= 2) return 'asking';

  // Agreement patterns anywhere in text
  if (lowerText.match(/(absolutely|definitely|exactly|that's right|you're right|agreed|great question|good point|yes,|of course)/)) {
    return 'agreeing';
  }

  // Clarification (question + clarifying words)
  if (questionCount > 0 && lowerText.match(/(clarif|mean|specific|which one|could you|do you mean|referring to)/)) return 'clarifying';

  // Suggestions
  if (lowerText.match(/(you (could|should|might)|recommend|suggest|consider|option|alternative|how about|what about)/)) return 'suggesting';

  // Redirection
  if (lowerText.match(/(however|on the other hand|actually|speaking of|regarding|moving on|another|also worth)/)) return 'redirecting';

  // Detailed explanation (long text with descriptive patterns)
  if (lowerText.length > 150 && lowerText.match(/(include|feature|built|designed|work|offer|provide|deliver|develop|create|implement|speciali)/)) return 'explaining';

  // Single question at end
  if (questionCount > 0) return 'asking';

  // Long response = explanation
  if (lowerText.length > 100) return 'explaining';

  return 'responding';
}

/**
 * Convert raw aiRole + previous topic context into a human-readable transition label.
 */
export function getTransitionLabel(aiRole: string, prevTopicName?: string): string {
  switch (aiRole) {
    case 'asking': return 'follow-up';
    case 'suggesting': return 'suggestion';
    case 'clarifying': return 'clarification';
    case 'agreeing': return 'agreement';
    case 'redirecting': return 'redirect';
    case 'explaining':
      if (prevTopicName) {
        const short = prevTopicName.length > 12 ? prevTopicName.slice(0, 12) : prevTopicName;
        return `detailed ${short.toLowerCase()}`;
      }
      return 'elaboration';
    case 'responding':
    default:
      return 'response';
  }
}

const categoryKeywords: { [key: string]: string[] } = {
  'Technology': ['ai', 'artificial intelligence', 'machine learning', 'voice', 'conversational', 'nlp', 'agent', 'agentic', 'automation', 'software', 'platform', 'architecture', 'algorithm', 'model', 'pipeline', 'integration', 'api', 'backend', 'frontend', 'system', 'framework', 'deploy', 'cloud', 'server', 'llm', 'stt', 'tts', 'speech', 'rag', 'knowledge graph', 'embedding', 'vector', 'database', 'real-time', 'streaming', 'websocket', 'inference', 'tech', 'digital', 'code', 'engineering', 'data', 'analytics', 'chatbot', 'multimodal', 'fintech', 'saas'],
  'Design': ['design', 'ux', 'ui', 'user experience', 'user research', 'interface', 'visual', 'prototype', 'wireframe', 'branding', 'identity', 'typography', 'layout', 'component', 'accessibility', 'responsive', 'animation', 'interaction', 'creative', 'usability', 'figma', 'mockup', 'style', 'aesthetic', 'color', 'spacing', 'navigation', 'mobile', 'desktop'],
  'Business': ['company', 'enterprise', 'client', 'customer', 'service', 'market', 'strategy', 'revenue', 'growth', 'sales', 'partnership', 'consulting', 'industry', 'startup', 'agency', 'business', 'corporate', 'solution', 'offering', 'approach', 'process', 'methodology', 'vision', 'mission'],
  'Projects': ['project', 'case study', 'build', 'product', 'portfolio', 'application', 'feature', 'implementation', 'workflow', 'demo', 'deliver', 'develop', 'tool', 'mvp', 'poc', 'pilot', 'basepair', 'booking', 'dashboard'],
  'People': ['team', 'founder', 'engineer', 'designer', 'developer', 'people', 'hire', 'culture', 'leadership', 'member', 'expert', 'collaborate', 'role', 'talent', 'who', 'ceo', 'cto', 'manager', 'director'],
  'Company': ['company', 'who are you', 'about you', 'assistant'],
};

function getSubTopic(text: string, category: string): string | null {
  const lowerText = text.toLowerCase();
  if (category === 'Technology') {
    if (lowerText.match(/voice|speech|stt|tts|conversational/)) return 'Voice AI';
    if (lowerText.match(/agent|agentic|multi-agent/)) return 'Agentic Systems';
    if (lowerText.match(/ai|artificial intelligence|machine learning|llm|model/)) return 'AI & ML';
    if (lowerText.match(/rag|knowledge graph|embedding|vector/)) return 'Knowledge & RAG';
    if (lowerText.match(/architecture|pipeline|system|infrastructure/)) return 'Architecture';
    if (lowerText.match(/data|analytics|database/)) return 'Data & Analytics';
    if (lowerText.match(/automat|workflow/)) return 'Automation';
    if (lowerText.match(/deploy|cloud|server/)) return 'Cloud & DevOps';
    return 'Technology';
  }
  if (category === 'Design') {
    if (lowerText.match(/user experience|user research|usability|ux/)) return 'UX Research';
    if (lowerText.match(/ui|interface|component|layout|visual/)) return 'UI Design';
    if (lowerText.match(/brand|identity|style|aesthetic/)) return 'Branding & Identity';
    if (lowerText.match(/interaction|animation|motion/)) return 'Interaction Design';
    if (lowerText.match(/responsive|mobile|desktop/)) return 'Responsive Design';
    if (lowerText.match(/accessibility|wcag|inclusive/)) return 'Accessibility';
    if (lowerText.match(/prototype|wireframe|mockup|figma/)) return 'Prototyping';
    return 'Design';
  }
  if (category === 'Business') {
    if (lowerText.match(/client|customer|enterprise/)) return 'Clients';
    if (lowerText.match(/service|offering|solution|consulting/)) return 'Services';
    if (lowerText.match(/strategy|vision|mission|approach|methodology/)) return 'Strategy';
    if (lowerText.match(/market|growth|revenue|sales/)) return 'Growth';
    return 'Business';
  }
  if (category === 'Projects') {
    if (lowerText.match(/booking/)) return 'Booking System';
    if (lowerText.match(/dashboard/)) return 'Dashboard';
    if (lowerText.match(/case study|portfolio/)) return 'Case Study';
    if (lowerText.match(/workflow|automat/)) return 'Workflow Automation';
    if (lowerText.match(/build|develop|implement/)) return 'Development';
    return 'Project Overview';
  }
  if (category === 'People') {
    if (lowerText.match(/founder|ceo|cto|leadership|leader/)) return 'Leadership';
    if (lowerText.match(/engineer|developer|code/)) return 'Engineering';
    if (lowerText.match(/designer|design team/)) return 'Design Team';
    if (lowerText.match(/culture|hire|talent/)) return 'Culture';
    return 'Team';
  }
  if (category === 'Company') {
    if (lowerText.match(/locat|where|office|based|headquarter/)) return 'Location';
    if (lowerText.match(/founded|history|story|started|origin|when/)) return 'History';
    if (lowerText.match(/what|do|does|about|overview|tell/)) return 'About Us';
    return 'Company';
  }
  return null;
}

function analyzeSentiment(text: string): { sentiment: 'positive' | 'neutral' | 'negative'; label: string; intensity: number } {
  const lowerText = text.toLowerCase();
  const positiveKeywords = ['love', 'great', 'awesome', 'amazing', 'excellent', 'perfect', 'beautiful', 'wonderful', 'excited', 'happy', 'enjoy', 'fantastic', 'brilliant', 'good', 'nice', 'best', 'incredible', 'outstanding', 'delightful', 'thrilled', 'impressed', 'favorite', 'glad'];
  const negativeKeywords = ['hate', 'bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'difficult', 'problem', 'issue', 'frustrat', 'annoying', 'disappointing', 'sad', 'worry', 'concern', 'stress', 'hard', 'struggle', 'tough', 'unfortunate'];
  const excitementKeywords = ['exciting', 'can\'t wait', 'looking forward', 'eager', 'pumped', 'psyched', 'thrilled', 'amazing', 'incredible'];
  const calmKeywords = ['okay', 'fine', 'alright', 'sure', 'consider', 'think', 'maybe', 'probably', 'planning', 'deciding'];
  const positiveCount = positiveKeywords.filter(k => lowerText.includes(k)).length;
  const negativeCount = negativeKeywords.filter(k => lowerText.includes(k)).length;
  const excitementCount = excitementKeywords.filter(k => lowerText.includes(k)).length;
  const calmCount = calmKeywords.filter(k => lowerText.includes(k)).length;
  if (excitementCount > 0) return { sentiment: 'positive', label: 'Excited', intensity: 0.8 + Math.min(excitementCount * 0.1, 0.2) };
  if (positiveCount > negativeCount && positiveCount > 0) return { sentiment: 'positive', label: 'Positive', intensity: 0.6 + Math.min(positiveCount * 0.1, 0.3) };
  if (negativeCount > positiveCount && negativeCount > 0) return { sentiment: 'negative', label: 'Concerned', intensity: 0.5 + Math.min(negativeCount * 0.1, 0.3) };
  if (calmCount > 0) return { sentiment: 'neutral', label: 'Calm', intensity: 0.3 + Math.min(calmCount * 0.05, 0.2) };
  return { sentiment: 'neutral', label: 'Neutral', intensity: 0.5 };
}

function generateTopicName(_keywords: string[], _text: string, category: string, subTopic?: string): string {
  if (subTopic) return subTopic;
  return category;
}

export function extractTopicsFromMessages(messages: Message[]): Topic[] {
  if (messages.length === 0) return [];
  const topics: Topic[] = [];
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];
  let currentCategory: string | null = null;
  let currentTopic: string | null = null;
  let colorIndex = 0;

  messages.forEach((message, index) => {
    // Process BOTH user and AI messages for conversation analysis
    const text = message.text.toLowerCase();
    let detectedCategory: string | null = null;
    let maxMatches = 0;
    for (const [category, keywords] of Object.entries(categoryKeywords)) {
      const matches = keywords.filter(keyword => text.includes(keyword)).length;
      if (matches > maxMatches) {
        maxMatches = matches;
        detectedCategory = category;
      }
    }
    if (detectedCategory && maxMatches > 0) {
      const subTopic = getSubTopic(text, detectedCategory);
      const topicName = generateTopicName([], message.text, detectedCategory, subTopic ?? undefined);
      if (currentTopic !== topicName) {
        const matchedKeywords = categoryKeywords[detectedCategory].filter(k => text.includes(k));
        const sentimentData = analyzeSentiment(message.text);
        let aiRole: string | undefined;

        // For AI messages, detect their role directly
        if (message.speaker === 'ai') {
          aiRole = detectAIRole(message.text);
        } else {
          // For user messages, search backwards for the nearest AI message
          for (let i = index - 1; i >= 0; i--) {
            if (messages[i].speaker === 'ai') {
              aiRole = detectAIRole(messages[i].text);
              break;
            }
          }
        }

        topics.push({
          id: `topic-${topics.length}`,
          name: topicName,
          timestamp: message.timestamp,
          keywords: matchedKeywords.slice(0, 5),
          parentId: topics.length > 0 ? topics[topics.length - 1].id : undefined,
          color: colors[colorIndex % colors.length],
          category: detectedCategory,
          sentiment: sentimentData.sentiment,
          sentimentLabel: sentimentData.label,
          intensity: sentimentData.intensity,
          speaker: message.speaker,
          aiRole,
        });
        if (currentCategory !== detectedCategory) {
          currentCategory = detectedCategory;
          colorIndex++;
        }
        currentTopic = topicName;
      }
    }
  });
  return topics;
}

export interface TopicNode extends Topic {
  x: number;
  y: number;
  row: number;
}

export function layoutTopics(topics: Topic[]): TopicNode[] {
  if (topics.length === 0) return [];
  const nodes: TopicNode[] = [];
  const rowAssignments: { [category: string]: number } = {};
  let currentRow = 0;
  topics.forEach((topic, index) => {
    if (rowAssignments[topic.category] === undefined) {
      rowAssignments[topic.category] = currentRow;
      currentRow++;
    }
    const row = rowAssignments[topic.category];
    nodes.push({
      ...topic,
      x: index * 150 + 120,
      y: row * 35 + 100,
      row,
    });
  });
  return nodes;
}
