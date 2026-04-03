"""
A2UI Template Library for Nester AI Voice Assistant

Pre-defined templates for automatic selection based on query content.
Each template type corresponds to a specific visual layout in the frontend.

IMPORTANT: All templates now include EXAMPLE STRUCTURES to guide LightRAG's LLM
on the exact format expected for each field. This ensures proper data extraction.

Template Types:
- template-grid: Grid of cards for lists (projects, products, services)
- timeline: Chronological events display
- contact-card: Contact information card
- comparison-chart: Side-by-side comparison
- stats-flow-layout: Dashboard with KPIs and metrics
- stats-chart: Statistics with charts
- team-flip-cards: Team member profiles
- service-hover-reveal: Service listings with hover details
- magazine-hero: Long-form content display
- faq-accordion: Q&A accordion
- blog-magazine: Blog posts grid
- sales-dashboard: Sales/revenue dashboard with KPIs
- image-gallery / video-gallery: Media galleries
"""

from typing import Dict, Any, List
import json
from loguru import logger


# Template library with structured examples for LLM guidance
# Matches a2ui-chatbot-service template library exactly
TEMPLATE_LIBRARY: Dict[str, Dict[str, Any]] = {
    "template-grid": {
        "version": "1.0",
        "root": {
            "type": "template-grid",
            "props": {
                "title": "",
                "templates": [{"name": "", "description": "", "category": ""}],
                "columns": 3,
                "showSearch": True,
                "showCount": True
            }
        },
        "_hint": "templates: array of items. Add as many objects as available in the data."
    },

    "timeline": {
        "version": "1.0",
        "root": {
            "type": "timeline",
            "props": {
                "title": "",
                "events": [{"year": "", "title": "", "description": ""}],
                "orientation": "vertical"
            }
        },
        "_hint": "events: array of events. Add as many objects as available in the data."
    },

    "comparison-chart": {
        "version": "1.0",
        "root": {
            "type": "comparison-chart",
            "props": {
                "title": "",
                "items": [{"name": "", "features": [{"feature": "", "value": ""}]}]
            }
        },
        "_hint": "items: array of items to compare. Each item has a features array. Add as many as available."
    },

    "contact-card": {
        "version": "1.0",
        "root": {
            "type": "contact-card",
            "props": {
                "title": "",
                "contacts": [{"type": "", "value": "", "description": ""}]
            }
        },
        "_hint": "contacts: array of contact methods (type: phone/email/address/website/etc). Add all available contacts."
    },

    "image-gallery": {
        "version": "1.0",
        "root": {
            "type": "image-gallery",
            "props": {
                "title": "",
                "images": [{"url": "", "caption": "", "alt": ""}],
                "layout": "grid"
            }
        },
        "_hint": "images: array of image objects. Add as many as available."
    },

    "video-gallery": {
        "version": "1.0",
        "root": {
            "type": "video-gallery",
            "props": {
                "title": "",
                "videos": [{"url": "", "title": "", "description": ""}],
                "layout": "grid"
            }
        },
        "_hint": "videos: array of video objects. Add as many as available."
    },

    "team-flip-cards": {
        "version": "1.0",
        "root": {
            "type": "team-flip-cards",
            "props": {
                "title": "",
                "members": [{"name": "", "role": "", "bio": "", "image": "", "email": ""}]
            }
        },
        "_hint": "members: array of team members. Add as many as available in the data. Include 'image' (photo URL), 'email', 'linkedin' if found."
    },

    "service-hover-reveal": {
        "version": "1.0",
        "root": {
            "type": "service-hover-reveal",
            "props": {
                "title": "",
                "services": [{"name": "", "description": ""}]
            }
        },
        "_hint": "services: array of services. Add ALL services found in the data."
    },

    "stats-flow-layout": {
        "version": "1.0",
        "root": {
            "type": "stats-flow-layout",
            "props": {
                "title": "",
                "topStats": [{"label": "", "value": ""}],
                "radialProgress": {"label": "", "completion_rate": ""},
                "performanceMetrics": [{"label": "", "value": ""}],
                "bottomStats": [{"label": "", "value": ""}]
            }
        },
        "_hint": "All array fields are dynamic. Add as many stat objects as available."
    },

    "stats-chart": {
        "version": "1.0",
        "root": {
            "type": "stats-chart",
            "props": {
                "title": "",
                "stats": [{"label": "", "value": ""}],
                "charts": [{"type": "bar", "title": "", "data": [{"name": "", "value": ""}]}]
            }
        },
        "_hint": "stats and charts are dynamic arrays. Add as many as available. Chart types: bar, line, pie, table."
    },

    "magazine-hero": {
        "version": "1.0",
        "root": {
            "type": "magazine-hero",
            "props": {
                "title": "",
                "subtitle": "",
                "content": "",
                "metadata": {"author": "", "date": ""},
                "tags": [],
                "pullQuote": ""
            }
        },
        "_hint": "tags: array of strings. Add as many tags as relevant."
    },

    "faq-accordion": {
        "version": "1.0",
        "root": {
            "type": "faq-accordion",
            "props": {
                "title": "",
                "faqs": [{"question": "", "answer": ""}],
                "variant": "searchable"
            }
        },
        "_hint": "faqs: array of Q&A objects. Add ALL questions found in the data."
    },

    "blog-magazine": {
        "version": "1.0",
        "root": {
            "type": "blog-magazine",
            "props": {
                "title": "",
                "posts": [{"title": "", "excerpt": "", "author": "", "date": "", "readTime": "", "category": "", "featured": False, "id": ""}],
                "variant": "magazine"
            }
        },
        "_hint": "posts: array of post objects with title, excerpt, author, date, readTime, category, featured, id. Extract ALL blog posts found including author names and publication dates."
    },

    "sales-dashboard": {
        "version": "1.0",
        "root": {
            "type": "sales-dashboard",
            "props": {
                "title": "",
                "subtitle": "",
                "kpiCards": [{"title": "", "value": "", "icon": "DollarSign", "variant": "primary"}],
                "charts": [{"type": "bar", "title": "", "data": [{"name": "", "value": ""}], "xAxisKey": "name", "yAxisKey": "value"}]
            }
        },
        "_format_example": {
            "description": "CRITICAL: The example below shows the JSON structure. Replace {{ KPI_CARDS }} and {{ CHARTS }} with this structure filled with REAL data from the CSV.",
            "kpiCards_example": [
                {"title": "Total Revenue", "value": "$31,422", "subtitle": "From 11 shipped orders", "icon": "DollarSign", "variant": "primary"},
                {"title": "Total Orders", "value": "11", "subtitle": "Shipped orders", "icon": "ShoppingCart", "variant": "success"}
            ],
            "charts_example": [
                {
                    "type": "bar",
                    "title": "Sales by Product Line",
                    "orientation": "horizontal",
                    "data": [
                        {"name": "Motorcycles", "value": 2871},
                        {"name": "Classic Cars", "value": 5512}
                    ],
                    "xAxisKey": "name",
                    "yAxisKey": "value"
                },
                {
                    "type": "table",
                    "title": "Top Customers",
                    "data": [
                        {"name": "Land of Toys Inc.", "value": 2871},
                        {"name": "Motor Mint Distributors Inc.", "value": 5512}
                    ],
                    "nameKey": "name",
                    "valueKey": "value"
                }
            ]
        }
    },

    # Simple text card for basic responses (fallback)
    "simple-card": {
        "version": "1.0",
        "root": {
            "type": "simple-card",
            "props": {
                "title": "",
                "content": "",
                "icon": ""
            }
        },
        "_hint": "Simple card for basic text responses. Use when no specific template matches."
    }
}


def get_template_from_library(template_type: str) -> Dict[str, Any]:
    """
    Get template from library by type, stripped of internal metadata fields.

    Args:
        template_type: Template type (template-grid, timeline, comparison-chart,
                      stats-chart, contact-card, etc.)

    Returns:
        Template structure dictionary (version + root only).
        Returns magazine-hero template if type not found.

    Examples:
        >>> template = get_template_from_library("timeline")
        >>> template["root"]["type"]
        'timeline'

        >>> template = get_template_from_library("unknown")
        >>> template["root"]["type"]
        'magazine-hero'
    """
    logger.debug(f"get_template_from_library called for: '{template_type}'")

    if template_type in TEMPLATE_LIBRARY:
        logger.debug(f"   Template found: {template_type}")
        template = TEMPLATE_LIBRARY[template_type]
    else:
        logger.warning(f"   Template '{template_type}' not found, using 'magazine-hero' fallback")
        template = TEMPLATE_LIBRARY["magazine-hero"]

    # Strip internal fields that should not be sent to LightRAG or returned to frontend
    import copy
    result = copy.deepcopy(template)
    return {k: v for k, v in result.items() if not k.startswith("_")}


def get_template_catalog() -> str:
    """
    Build a compact template catalog string for LLM template selection.
    Shows each template's structure and when to use it.
    The LLM uses this to pick the best template based on actual retrieved context.
    """
    catalog = [
        {
            "type": "service-hover-reveal",
            "when": "Context describes services, offerings, capabilities, or solutions",
            "structure": {"title": "str", "services": [{"name": "str", "description": "str"}]},
            "extra_fields": "fullDescription, problem_solved, who_it_is_for, icon"
        },
        {
            "type": "contact-card",
            "when": "Context has contact info: phone, email, address, social links",
            "structure": {"title": "str", "contacts": [{"type": "str", "value": "str", "description": "str"}]},
            "extra_fields": "availability, response_time, url"
        },
        {
            "type": "template-grid",
            "when": "Context has a list of items: projects, products, features, tools, resources",
            "structure": {"title": "str", "templates": [{"name": "str", "description": "str"}]},
            "extra_fields": "category, icon, tags, url, status"
        },
        {
            "type": "timeline",
            "when": "Context has chronological events, milestones, or history",
            "structure": {"title": "str", "events": [{"year": "str", "title": "str", "description": "str"}]},
            "extra_fields": "milestone, icon, category"
        },
        {
            "type": "comparison-chart",
            "when": "Context compares multiple items with features/specs side by side",
            "structure": {"title": "str", "items": [{"name": "str", "features": [{"feature": "str", "value": "str"}]}]},
            "extra_fields": "price, recommended, icon"
        },
        {
            "type": "team-flip-cards",
            "when": "Context has team members, people profiles, or staff info",
            "structure": {"title": "str", "members": [{"name": "str", "role": "str", "bio": "str"}]},
            "extra_fields": "image, email, linkedin, expertise"
        },
        {
            "type": "faq-accordion",
            "when": "Context has questions and answers, FAQ, or Q&A format",
            "structure": {"title": "str", "faqs": [{"question": "str", "answer": "str"}]},
            "extra_fields": "category, order"
        },
        {
            "type": "stats-flow-layout",
            "when": "Context has specific NUMERIC data: counts, percentages, amounts, rates",
            "structure": {"title": "str", "topStats": [{"label": "str", "value": "str"}]},
            "extra_fields": "change, trend, radialProgress, performanceMetrics, bottomStats"
        },
        {
            "type": "stats-chart",
            "when": "Context has numeric data suitable for charts: sales figures, distributions, rankings",
            "structure": {"title": "str", "stats": [{"label": "str", "value": "str"}], "charts": [{"type": "bar|line|pie|table", "title": "str", "data": [{"name": "str", "value": "number"}]}]},
            "extra_fields": "xAxisKey, yAxisKey, orientation"
        },
        {
            "type": "sales-dashboard",
            "when": "Context has sales/revenue/order data with KPIs and chart-worthy metrics",
            "structure": {"title": "str", "kpiCards": [{"title": "str", "value": "str", "icon": "str", "variant": "str"}], "charts": [{"type": "str", "title": "str", "data": [{"name": "str", "value": "number"}]}]},
            "extra_fields": "subtitle, xAxisKey, yAxisKey, orientation"
        },
        {
            "type": "magazine-hero",
            "when": "Context is descriptive/narrative text: about us, overview, article, case study, general info",
            "structure": {"title": "str", "subtitle": "str", "content": "str"},
            "extra_fields": "metadata (author, date), tags, pullQuote"
        },
        {
            "type": "blog-magazine",
            "when": "Context has multiple articles, blog posts, or news items",
            "structure": {"title": "str", "posts": [{"title": "str", "excerpt": "str", "author": "str", "date": "str"}]},
            "extra_fields": "category, readTime, featured, id, image"
        },
        {
            "type": "image-gallery",
            "when": "Context has image URLs or references to visual assets",
            "structure": {"title": "str", "images": [{"url": "str", "caption": "str"}]},
            "extra_fields": "alt, category"
        },
        {
            "type": "video-gallery",
            "when": "Context has video URLs or references to video content",
            "structure": {"title": "str", "videos": [{"url": "str", "title": "str"}]},
            "extra_fields": "description, duration, thumbnail"
        },
        {
            "type": "simple-card",
            "when": "Simple text response with no specific data structure needed",
            "structure": {"title": "str", "content": "str", "icon": "str"},
            "extra_fields": ""
        }
    ]

    return json.dumps(catalog, indent=None, separators=(',', ':'))


def list_available_templates() -> Dict[str, Any]:
    """
    List all available templates with metadata for semantic selector.

    Returns:
        Dictionary containing list of templates with their metadata including
        type, name, description, use cases, and trigger keywords.

    Example:
        >>> templates_info = list_available_templates()
        >>> len(templates_info["templates"])
        15
        >>> templates_info["templates"][0]["type"]
        'template-grid'
    """
    templates_metadata = {
        "count": len(TEMPLATE_LIBRARY),
        "templates": [
            {
                "type": "template-grid",
                "name": "Template Grid",
                "description": "Grid layout for displaying multiple items (projects, products, services, features, team members, case studies, portfolio items, or any list-based content). Perfect for showcasing collections of similar items with consistent structure. Shows title, description, icon/image, and metadata for each item in a responsive grid format",
                "use_cases": [
                    "project listings",
                    "product showcase",
                    "service offerings",
                    "feature lists",
                    "portfolio display",
                    "team overview",
                    "case studies",
                    "tool collections",
                    "resource lists",
                    "card grid",
                    "item gallery",
                    "multiple items",
                    "list of things",
                    "collection display",
                    "catalog view"
                ],
                "trigger_keywords": [
                    "projects",
                    "list",
                    "show me",
                    "display",
                    "all",
                    "collection",
                    "showcase",
                    "products",
                    "services",
                    "features",
                    "portfolio",
                    "items",
                    "things",
                    "what",
                    "examples",
                    "catalog",
                    "offerings",
                    "tools",
                    "resources",
                    "grid",
                    "cards",
                    "multiple",
                    "several",
                    "various"
                ]
            },
            {
                "type": "timeline",
                "name": "Timeline",
                "description": "Chronological event timeline for displaying history, milestones, roadmap, company evolution, project phases, or any time-based sequence. Perfect for showing historical progression, key dates, development phases, or chronological narratives. Features vertical layout with dates, titles, and descriptions",
                "use_cases": [
                    "company history",
                    "project timeline",
                    "milestones",
                    "roadmap",
                    "evolution",
                    "development phases",
                    "historical events",
                    "chronological order",
                    "progress tracking",
                    "key dates",
                    "timeline view",
                    "history display",
                    "founding story",
                    "growth journey",
                    "year by year",
                    "temporal sequence"
                ],
                "trigger_keywords": [
                    "timeline",
                    "history",
                    "when",
                    "founded",
                    "since",
                    "milestones",
                    "chronological",
                    "evolution",
                    "progression",
                    "roadmap",
                    "years",
                    "dates",
                    "phases",
                    "journey",
                    "development",
                    "over time",
                    "historical",
                    "established",
                    "started",
                    "began",
                    "growth",
                    "sequence",
                    "events"
                ]
            },
            {
                "type": "comparison-chart",
                "name": "Comparison Chart",
                "description": "Side-by-side comparison table for products, plans, services, options, or alternatives. Perfect for helping users choose between multiple options by comparing features, prices, pros/cons, specifications, or capabilities. Shows clear differentiation between choices",
                "use_cases": [
                    "product comparison",
                    "plan comparison",
                    "pricing tiers",
                    "feature comparison",
                    "vs analysis",
                    "option evaluation",
                    "alternatives",
                    "pros and cons",
                    "side by side",
                    "which to choose",
                    "decision making",
                    "specifications",
                    "capabilities",
                    "differences"
                ],
                "trigger_keywords": [
                    "compare",
                    "comparison",
                    "versus",
                    "vs",
                    "difference",
                    "between",
                    "which",
                    "better",
                    "best",
                    "choose",
                    "options",
                    "alternatives",
                    "pros and cons",
                    "advantages",
                    "disadvantages",
                    "features",
                    "side by side",
                    "evaluate",
                    "decision"
                ]
            },
            {
                "type": "contact-card",
                "name": "Contact Card",
                "description": "Contact information card displaying email, phone, address, social media links, and other contact methods. Perfect for 'Contact Us' pages, support information, office locations, or any scenario requiring contact details. Clean, organized presentation of multiple contact channels",
                "use_cases": [
                    "contact information",
                    "get in touch",
                    "reach us",
                    "support contact",
                    "office details",
                    "communication channels",
                    "how to reach",
                    "contact methods",
                    "company address",
                    "headquarters location",
                    "contact methods",
                    "ways to contact"
                ],
                "trigger_keywords": [
                    "contact",
                    "phone",
                    "reach",
                    "address",
                    "email",
                    "call",
                    "location",
                    "office",
                    "where",
                    "find us",
                    "get in touch",
                    "communication",
                    "reach out",
                    "message",
                    "headquarters",
                    "postal address",
                    "how to contact",
                    "contact us",
                    "contact information",
                    "phone number",
                    "email address",
                    "office address",
                    "where is",
                    "where are you",
                    "located",
                    "find you"
                ]
            },
            {
                "type": "image-gallery",
                "name": "Image Gallery",
                "description": "Interactive image gallery for displaying photos, logos, screenshots, diagrams, visual content, or picture collections. Perfect for showcasing visual assets, product images, portfolio photography, company photos, infographics, or any image-based content. Features lightbox view, grid layout, and image captions",
                "use_cases": [
                    "display images",
                    "photo gallery",
                    "logo showcase",
                    "visual content",
                    "screenshot gallery",
                    "product photos",
                    "portfolio images",
                    "company pictures",
                    "infographics",
                    "visual assets",
                    "image collection",
                    "picture gallery",
                    "photo showcase"
                ],
                "trigger_keywords": [
                    "image",
                    "images",
                    "photo",
                    "photos",
                    "picture",
                    "pictures",
                    "logo",
                    "logos",
                    "screenshot",
                    "screenshots",
                    "visual",
                    "visuals",
                    "gallery",
                    "show me images",
                    "show me photos",
                    "image gallery",
                    "photo gallery",
                    "picture gallery",
                    "visual content",
                    "graphics",
                    "diagrams",
                    "illustrations",
                    "infographic",
                    "photography"
                ]
            },
            {
                "type": "video-gallery",
                "name": "Video Gallery",
                "description": "Interactive video gallery for displaying YouTube videos, Vimeo embeds, tutorials, demos, webinars, or any video content. Perfect for video tutorials, product demonstrations, introduction videos, training materials, presentations, or multimedia content. Features responsive embeds, video thumbnails, and play controls",
                "use_cases": [
                    "video collection",
                    "tutorial videos",
                    "demo videos",
                    "introduction videos",
                    "training materials",
                    "webinar recordings",
                    "presentation videos",
                    "product demos",
                    "how-to videos",
                    "video content",
                    "multimedia gallery",
                    "video showcase",
                    "educational videos"
                ],
                "trigger_keywords": [
                    "video",
                    "videos",
                    "watch",
                    "youtube",
                    "vimeo",
                    "recording",
                    "demo",
                    "tutorial",
                    "presentation",
                    "webinar",
                    "show me videos",
                    "video gallery",
                    "multimedia",
                    "play",
                    "streaming",
                    "watch videos"
                ]
            },
            {
                "type": "team-flip-cards",
                "name": "Team Flip Cards",
                "description": "Interactive flip cards for displaying team members, staff profiles, leadership, founders, or people information. Perfect for 'About Us' pages, team introductions, staff directory, or showcasing key personnel. Features flip animation revealing detailed bio, role, and social links on hover/click",
                "use_cases": [
                    "team members",
                    "staff profiles",
                    "meet the team",
                    "leadership",
                    "founders",
                    "who we are",
                    "people",
                    "employees",
                    "team directory",
                    "personnel",
                    "our team",
                    "team showcase",
                    "staff directory"
                ],
                "trigger_keywords": [
                    "team",
                    "members",
                    "staff",
                    "people",
                    "who",
                    "employees",
                    "founders",
                    "leadership",
                    "management",
                    "personnel",
                    "meet",
                    "our team",
                    "team members",
                    "who works",
                    "who are",
                    "profiles",
                    "bios"
                ]
            },
            {
                "type": "service-hover-reveal",
                "name": "Service Hover Reveal",
                "description": "Interactive service cards with hover-reveal details for displaying services, offerings, capabilities, solutions, or features. Perfect for service pages, capability showcases, or feature highlights. Cards expand on hover to reveal additional details, descriptions, and benefits",
                "use_cases": [
                    "services offered",
                    "what we do",
                    "capabilities",
                    "solutions",
                    "offerings",
                    "service catalog",
                    "expertise",
                    "what we offer",
                    "service details",
                    "capabilities",
                    "service showcase",
                    "service offerings",
                    "offerings"
                ],
                "trigger_keywords": [
                    "services",
                    "offerings",
                    "what we do",
                    "what do you offer",
                    "capabilities",
                    "solutions",
                    "expertise",
                    "what we offer",
                    "service",
                    "provide",
                    "offer",
                    "deliver",
                    "specialize",
                    "help with"
                ]
            },
            {
                "type": "stats-flow-layout",
                "name": "Stats Flow Layout",
                "description": "Advanced statistics dashboard with sparklines, radial progress bars, performance metrics, and metric cards. Perfect for displaying analytics, KPIs, business metrics, performance data, statistical information, numbers, and data visualizations. Shows quantitative information in an interactive, visually appealing dashboard format. Ideal for company financials, revenue data, employee counts, growth metrics, and business statistics",
                "use_cases": [
                    "analytics dashboard",
                    "performance metrics",
                    "KPI tracking",
                    "statistics overview",
                    "data visualization",
                    "business metrics",
                    "numbers and stats",
                    "metric dashboard",
                    "performance data",
                    "key metrics",
                    "statistical data",
                    "quantitative information",
                    "metrics display",
                    "company financials",
                    "revenue information",
                    "employee statistics",
                    "growth metrics",
                    "business performance",
                    "financial data",
                    "company statistics",
                    "company metrics",
                    "company numbers",
                    "financial overview",
                    "business numbers"
                ],
                "trigger_keywords": [
                    "analytics",
                    "metrics",
                    "KPI",
                    "statistics",
                    "stats",
                    "performance",
                    "data",
                    "numbers",
                    "dashboard",
                    "business metrics",
                    "key metrics",
                    "quantitative",
                    "measure",
                    "tracking",
                    "progress",
                    "results",
                    "achievements",
                    "company stats",
                    "business stats",
                    "financial",
                    "revenue",
                    "growth",
                    "employees",
                    "size",
                    "scale"
                ]
            },
            {
                "type": "stats-chart",
                "name": "Stats Chart",
                "description": "Statistics display with charts (bar, line, radial) for data visualization, metrics, performance indicators, analytics, or numerical information. Perfect for showing quantitative data, trends, comparisons, or statistical information with visual charts and numeric displays",
                "use_cases": [
                    "data visualization",
                    "charts and graphs",
                    "statistics display",
                    "metrics with charts",
                    "performance charts",
                    "data charts",
                    "visual statistics",
                    "chart display",
                    "graphical data"
                ],
                "trigger_keywords": [
                    "chart",
                    "graph",
                    "visualization",
                    "data",
                    "metrics",
                    "statistics",
                    "analytics",
                    "numbers",
                    "stats",
                    "performance",
                    "trends"
                ]
            },
            {
                "type": "magazine-hero",
                "name": "Magazine Hero",
                "description": "Magazine-style hero section for long-form content, articles, blog posts, case studies, or detailed explanations. Perfect for rich text content with author info, read time, tags, and pull quotes. Features elegant typography, metadata display, and content-focused layout ideal for storytelling",
                "use_cases": [
                    "article display",
                    "blog post",
                    "case study",
                    "long-form content",
                    "detailed explanation",
                    "story",
                    "narrative",
                    "editorial content",
                    "magazine layout",
                    "feature article",
                    "in-depth content",
                    "rich text",
                    "content page"
                ],
                "trigger_keywords": [
                    "article",
                    "blog",
                    "post",
                    "story",
                    "read",
                    "content",
                    "case study",
                    "detailed",
                    "explanation",
                    "about",
                    "learn",
                    "understand",
                    "tell me",
                    "describe",
                    "explain",
                    "overview"
                ]
            },
            {
                "type": "faq-accordion",
                "name": "FAQ Accordion",
                "description": "Expandable FAQ accordion for frequently asked questions, Q&A sections, help documentation, or common inquiries. Perfect for support pages, help centers, or answering common user questions. Features searchable, collapsible questions with detailed answers",
                "use_cases": [
                    "frequently asked questions",
                    "Q&A section",
                    "help documentation",
                    "common questions",
                    "support questions",
                    "inquiry answers",
                    "help center",
                    "knowledge base",
                    "question answers",
                    "FAQ section"
                ],
                "trigger_keywords": [
                    "faq",
                    "frequently asked",
                    "questions",
                    "q&a",
                    "q and a",
                    "common questions",
                    "help",
                    "how to",
                    "answers",
                    "inquiry",
                    "ask",
                    "question"
                ]
            },
            {
                "type": "blog-magazine",
                "name": "Blog Magazine",
                "description": "Magazine-style blog layout for displaying multiple blog posts, articles, news items, or content pieces. Perfect for blog homepages, news sections, content hubs, or article collections. Features post cards with images, excerpts, author info, dates, tags, and read time",
                "use_cases": [
                    "blog homepage",
                    "article list",
                    "news section",
                    "content hub",
                    "post collection",
                    "blog posts",
                    "latest articles",
                    "recent news",
                    "content feed",
                    "blog grid"
                ],
                "trigger_keywords": [
                    "blog",
                    "posts",
                    "articles",
                    "news",
                    "latest",
                    "recent",
                    "updates",
                    "content",
                    "publications",
                    "writings",
                    "stories"
                ]
            },
            {
                "type": "sales-dashboard",
                "name": "Sales Dashboard",
                "description": "Comprehensive sales analytics dashboard with KPI cards, charts, and data tables. Perfect for displaying sales metrics, revenue data, order statistics, and business performance. Features KPI cards with icons and variants, multiple chart types (bar, line, table), and responsive layout",
                "use_cases": [
                    "sales analytics",
                    "revenue dashboard",
                    "order statistics",
                    "business performance",
                    "sales metrics",
                    "financial dashboard",
                    "KPI dashboard",
                    "sales overview",
                    "revenue tracking",
                    "business analytics"
                ],
                "trigger_keywords": [
                    "sales",
                    "revenue",
                    "orders",
                    "customers",
                    "dashboard",
                    "kpi",
                    "business",
                    "profit",
                    "income",
                    "quarterly",
                    "annual",
                    "fiscal"
                ]
            },
            {
                "type": "simple-card",
                "name": "Simple Card",
                "description": "Simple text card for basic responses when no specific template matches. Displays a title, content text, and optional icon. Used as a fallback when the query doesn't match any specialized template",
                "use_cases": [
                    "simple answer",
                    "basic response",
                    "default fallback",
                    "general information",
                    "text response"
                ],
                "trigger_keywords": []
            }
        ]
    }

    return templates_metadata
