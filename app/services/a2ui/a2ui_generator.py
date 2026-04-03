"""
A2UI Generator for Nester AI Voice Assistant

Generates A2UI JSON structures from LLM responses based on detected template type.
Integrates with the voice assistant pipeline to provide visual cards alongside voice responses.

This generator follows the AgenticUICatalog approach:
1. Parse LightRAG text response to extract structured items
2. Select appropriate template from library based on query
3. Fill template with extracted items
4. Return A2UI document for frontend rendering
"""

from typing import Dict, Any, Optional, List
import re
import json
import copy

from loguru import logger

from .template_library import get_template_from_library, TEMPLATE_LIBRARY
from .orchestrator import detect_tier, get_tier_metadata


class A2UIGenerator:
    """
    Generates A2UI visual components from LLM text responses.

    This class:
    1. Detects appropriate template type from user query
    2. Parses LLM response to extract structured data
    3. Fills template from library with extracted data
    4. Generates A2UI JSON for frontend rendering
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize the A2UI generator.

        Args:
            enabled: Enable/disable A2UI generation
        """
        self.enabled = enabled
        logger.info(f"🎨 A2UIGenerator initialized (enabled={enabled})")

    def generate(
        self,
        query: str,
        llm_response: str,
        custom_template: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate A2UI visual component from query and LLM response.

        Args:
            query: User's original question
            llm_response: LLM's text response
            custom_template: Optional custom template

        Returns:
            A2UI document dict or None if generation fails/disabled
        """
        logger.info("=" * 60)
        logger.info("🎨 A2UI GENERATION STARTING")
        logger.info("=" * 60)
        logger.info(f"📝 Query: '{query[:80]}{'...' if len(query) > 80 else ''}'")
        logger.info(f"📄 LLM Response length: {len(llm_response)} chars")
        logger.info(f"🔧 Generator enabled: {self.enabled}")

        if not self.enabled:
            logger.warning("⚠️ A2UI Generator is DISABLED - returning None")
            return None

        try:
            # Step 1: Detect tier and template type
            logger.info("📊 Step 1: Detecting tier and template type...")
            tier_info = detect_tier(query, custom_template)
            template_type = tier_info["template_type"]
            logger.info(f"✅ Tier detected: {tier_info['tier_name']}")
            logger.info(f"✅ Template type: {template_type}")

            # Step 2: Get template structure from library
            logger.info("📋 Step 2: Getting template structure from library...")
            template = get_template_from_library(template_type)
            logger.info(f"✅ Template structure retrieved for '{template_type}'")

            # Step 3: Parse LLM response to extract items
            logger.info("🔍 Step 3: Parsing LLM response to extract items...")
            items = self._parse_response_to_items(llm_response, query)
            logger.info(f"✅ Extracted {len(items)} items from response")

            # Step 4: Fill template with extracted data
            logger.info("🔄 Step 4: Filling template with extracted data...")
            a2ui_doc = self._fill_template(template, items, query, tier_info)
            logger.info("✅ Template filled successfully")

            # Step 5: Add metadata
            logger.info("📎 Step 5: Adding metadata...")
            a2ui_doc["_metadata"] = get_tier_metadata(tier_info)

            # Log result summary
            props = a2ui_doc.get("root", {}).get("props", {})
            logger.info("=" * 60)
            logger.info("🎉 A2UI GENERATION COMPLETE!")
            logger.info(f"   Template: {template_type}")
            logger.info(f"   Tier: {tier_info['tier']}")
            logger.info(f"   Title: {props.get('title', 'N/A')}")

            # Log array sizes
            for key in ["templates", "services", "contacts", "events", "faqs", "members", "items"]:
                if key in props and isinstance(props[key], list):
                    logger.info(f"   {key}: {len(props[key])} items")
            logger.info("=" * 60)

            return a2ui_doc

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ A2UI GENERATION FAILED: {e}")
            logger.error("=" * 60)
            import traceback
            logger.error(traceback.format_exc())
            # Return simple fallback card
            logger.info("📋 Creating fallback card...")
            return self._create_fallback_card(query, llm_response)

    def _parse_response_to_items(self, response: str, query: str) -> List[Dict[str, Any]]:
        """
        Parse LLM text response into structured items.

        Follows AgenticUICatalog approach to extract distinct information chunks.

        Args:
            response: LLM text response
            query: Original query (for context)

        Returns:
            List of item dicts with 'title' and 'description' keys
        """
        items = []

        # Clean the response - remove JSON metadata if present
        cleaned_response = self._clean_response(response)

        # Strategy 1: Extract markdown sections (### Header)
        section_pattern = r'###\s*(?:Project\s*\d+[:\s]*)?([^\n]+)\n((?:(?!###).)*)'
        sections = re.findall(section_pattern, cleaned_response, re.DOTALL)

        if sections:
            logger.debug(f"   Found {len(sections)} markdown sections")
            for title, content in sections:
                title = self._clean_text(title)
                content = content.strip()
                # Get first 2-3 sentences as description
                sentences = re.split(r'(?<=[.!?])\s+', content)
                description = ' '.join(sentences[:3]).strip()
                description = self._clean_text(description)

                if title and len(title) > 3:
                    items.append({
                        "title": title[:100],
                        "description": description[:500] if description else title,
                    })
            if items:
                return items[:8]  # Max 8 items

        # Strategy 2: Extract bullet points with hierarchy
        items = self._parse_bullet_points(cleaned_response)
        if items:
            logger.debug(f"   Found {len(items)} bullet point items")
            return items[:8]

        # Strategy 3: Extract numbered items
        numbered_pattern = r'(?:^|\n)\s*(\d+)\.\s*([^:\n]+)(?:[:\s]+([^\n]+))?'
        numbered_matches = re.findall(numbered_pattern, cleaned_response)

        if numbered_matches:
            logger.debug(f"   Found {len(numbered_matches)} numbered items")
            for num, title, desc in numbered_matches:
                title = self._clean_text(title)
                desc = self._clean_text(desc) if desc else ""
                if title and len(title) > 3:
                    items.append({
                        "title": title[:100],
                        "description": desc[:500] if desc else title,
                    })
            if items:
                return items[:8]

        # Strategy 4: Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', cleaned_response)
        logger.debug(f"   Found {len(paragraphs)} paragraphs")

        for para in paragraphs[:6]:
            para = para.strip()
            para = self._clean_text(para)
            if len(para) > 30:
                # Use first sentence as title
                sentences = re.split(r'(?<=[.!?])\s+', para)
                title = sentences[0][:100] if sentences else para[:100]
                items.append({
                    "title": title,
                    "description": para[:500],
                })

        if items:
            return items[:8]

        # Fallback: single item with full content
        logger.debug("   Using fallback: single item")
        items.append({
            "title": "Information",
            "description": cleaned_response[:500],
        })

        return items

    def _parse_bullet_points(self, response: str) -> List[Dict[str, Any]]:
        """Parse bullet points with hierarchy support."""
        items = []
        lines = response.split('\n')
        current_item = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip references and citations
            if line.lower().startswith('reference') or line.startswith('[') or '.docx' in line.lower():
                continue

            # Check for bullet point
            match = re.match(r'^[\-\*\•]\s+(.+)', line)
            if match:
                content = match.group(1)
                content = self._clean_text(content)

                # Save previous item
                if current_item and (current_item.get("title") or current_item.get("description")):
                    items.append(current_item)

                # Parse title:description or just title
                if ':' in content and not content.startswith('http'):
                    parts = content.split(':', 1)
                    current_item = {
                        "title": parts[0].strip()[:100],
                        "description": parts[1].strip()[:500] if len(parts) > 1 else ""
                    }
                elif ' - ' in content:
                    parts = content.split(' - ', 1)
                    current_item = {
                        "title": parts[0].strip()[:100],
                        "description": parts[1].strip()[:500] if len(parts) > 1 else ""
                    }
                else:
                    current_item = {
                        "title": content[:100],
                        "description": content[:500]
                    }
            elif current_item:
                # Continuation line - append to description
                clean_line = self._clean_text(line)
                if clean_line and not line.startswith('['):
                    if current_item["description"]:
                        current_item["description"] += " " + clean_line
                    else:
                        current_item["description"] = clean_line

        # Add last item
        if current_item and (current_item.get("title") or current_item.get("description")):
            items.append(current_item)

        return items

    def _clean_response(self, response: str) -> str:
        """Clean response by removing JSON metadata and template variables."""
        cleaned = response

        # Remove JSON blocks that contain metadata
        if any(kw in response for kw in ['"Query"', '"Response_Format"', '"A2Ui_Template"']):
            # Find and remove JSON blocks
            while '{' in cleaned:
                start = cleaned.find('{')
                if start == -1:
                    break

                # Find matching closing brace
                depth = 0
                end = -1
                for i in range(start, len(cleaned)):
                    if cleaned[i] == '{':
                        depth += 1
                    elif cleaned[i] == '}':
                        depth -= 1
                        if depth == 0:
                            end = i
                            break

                if end == -1:
                    break

                block = cleaned[start:end+1]
                if any(kw in block for kw in ['"Query"', '"Response_Format"', '"A2Ui_Template"', '"Version"', '"Root"']):
                    cleaned = cleaned[:start] + cleaned[end+1:]
                else:
                    break

        # Remove template variables
        cleaned = re.sub(r'\{\{[^}]+\}\}', '', cleaned)

        return cleaned.strip()

    def _clean_text(self, text: str) -> str:
        """Clean text by removing markdown formatting."""
        if not text:
            return ""
        # Remove markdown bold/italic
        text = re.sub(r'\*\*|__', '', text)
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        # Remove citation markers [1], [2], etc.
        text = re.sub(r'\s*\[\d+\]\s*', ' ', text)
        # Clean extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _fill_template(
        self,
        template: Dict[str, Any],
        items: List[Dict[str, Any]],
        query: str,
        tier_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fill template structure with extracted items.

        Args:
            template: Template structure from library
            items: Extracted items from response
            query: Original query
            tier_info: Tier detection info

        Returns:
            Filled A2UI document
        """
        template_type = tier_info["template_type"]
        props = template["root"]["props"]

        # Set title
        props["title"] = self._generate_title(query, template_type)

        # Fill based on template type
        if template_type == "template-grid":
            props["templates"] = [
                {
                    "name": item.get("title", "")[:60],
                    "description": item.get("description", "")[:300],
                    "category": self._determine_category(query),
                    "tags": self._extract_tags(item.get("title", ""))
                }
                for item in items
            ]
            props["showSearch"] = len(items) > 3
            props["showCount"] = len(items) > 3

        elif template_type == "service-hover-reveal":
            props["services"] = [
                {
                    "name": item.get("title", "")[:60],
                    "description": item.get("description", "")[:300]
                }
                for item in items
            ]

        elif template_type == "contact-card":
            props["contacts"] = self._extract_contacts(items)

        elif template_type == "timeline":
            props["events"] = [
                {
                    "year": self._extract_year(item.get("title", "") + item.get("description", "")),
                    "title": item.get("title", "")[:60],
                    "description": item.get("description", "")[:300]
                }
                for item in items
            ]

        elif template_type == "team-flip-cards":
            props["members"] = [
                {
                    "name": item.get("title", "")[:60],
                    "role": self._extract_role(item.get("description", "")),
                    "bio": item.get("description", "")[:200],
                    "image": item.get("image", ""),  # Image URL if available
                    "email": item.get("email", ""),  # Email if available
                    "linkedin": item.get("linkedin", "")  # LinkedIn if available
                }
                for item in items
            ]

        elif template_type == "faq-accordion":
            props["faqs"] = [
                {
                    "question": item.get("title", "")[:100],
                    "answer": item.get("description", "")[:500]
                }
                for item in items
            ]

        elif template_type == "comparison-chart":
            props["items"] = [
                {
                    "name": item.get("title", "")[:60],
                    "features": self._extract_features(item.get("description", ""))
                }
                for item in items
            ]

        elif template_type == "stats-flow-layout":
            stats = self._extract_stats(items)
            props["topStats"] = stats[:3] if stats else [{"label": "Data", "value": "N/A"}]
            props["bottomStats"] = stats[3:6] if len(stats) > 3 else []

        elif template_type == "magazine-hero":
            # Combine all items into long-form content
            if items:
                props["subtitle"] = items[0].get("title", "")[:100]
                content_parts = [item.get("description", "") for item in items]
                props["content"] = "\n\n".join(content_parts)[:2000]
                # Extract pull quote if present
                quote_match = re.search(r'"([^"]{20,100})"', props["content"])
                if quote_match:
                    props["pullQuote"] = quote_match.group(1)

        elif template_type == "simple-card":
            if items:
                props["content"] = items[0].get("description", "")[:500]
                props["icon"] = "info"

        else:
            # Default: use template-grid format
            props["templates"] = [
                {
                    "name": item.get("title", "")[:60],
                    "description": item.get("description", "")[:300],
                    "category": "",
                    "tags": []
                }
                for item in items
            ]

        return template

    def _generate_title(self, query: str, template_type: str) -> str:
        """Generate appropriate title from query."""
        title = query.strip()

        # Remove question words
        for word in ["what", "who", "where", "when", "how", "tell me about", "show me", "list", "can you"]:
            if title.lower().startswith(word):
                title = title[len(word):].strip()
                if title.startswith("is ") or title.startswith("are ") or title.startswith("the "):
                    title = title[3:].strip()
                break

        # Capitalize
        if title:
            title = title[0].upper() + title[1:]

        # Template-specific defaults
        type_defaults = {
            "contact-card": "Contact Information",
            "timeline": "Timeline",
            "team-flip-cards": "Team Members",
            "service-hover-reveal": "Services",
            "stats-flow-layout": "Statistics",
            "comparison-chart": "Comparison",
            "faq-accordion": "FAQ",
        }

        if template_type in type_defaults and len(title) < 5:
            return type_defaults[template_type]

        return title[:60] or "Information"

    def _determine_category(self, query: str) -> str:
        """Determine category based on query."""
        query_lower = query.lower()
        if "project" in query_lower:
            return "Projects"
        elif "service" in query_lower:
            return "Services"
        elif "product" in query_lower:
            return "Products"
        elif "contact" in query_lower:
            return "Contact"
        elif "team" in query_lower or "member" in query_lower:
            return "Team"
        return ""

    def _extract_tags(self, title: str) -> List[str]:
        """Extract relevant tags from title."""
        tags = []
        title_lower = title.lower()

        tag_keywords = {
            "ai": ["ai", "artificial", "intelligence", "machine learning", "ml"],
            "web": ["web", "website", "frontend", "backend"],
            "mobile": ["mobile", "app", "ios", "android"],
            "cloud": ["cloud", "aws", "azure", "gcp"],
            "data": ["data", "analytics", "database"],
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in title_lower for kw in keywords):
                tags.append(tag)

        return tags[:3]

    def _extract_contacts(self, items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract contact information from items."""
        contacts = []
        all_text = " ".join([f"{item.get('title', '')} {item.get('description', '')}" for item in items])

        # Extract emails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', all_text)
        for email in emails:
            contacts.append({"type": "email", "value": email, "description": "Email"})

        # Extract phones
        phones = re.findall(r'[\+\d][\d\s\-\(\)]{7,}[\d]', all_text)
        for phone in phones:
            contacts.append({"type": "phone", "value": phone.strip(), "description": "Phone"})

        # Extract URLs
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', all_text)
        for url in urls:
            contacts.append({"type": "website", "value": url, "description": "Website"})

        # If no contacts found, use items as generic contacts
        if not contacts:
            for item in items[:4]:
                contacts.append({
                    "type": "info",
                    "value": item.get("title", ""),
                    "description": item.get("description", "")[:100]
                })

        return contacts[:6]

    def _extract_year(self, text: str) -> str:
        """Extract year from text."""
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return match.group(0) if match else ""

    def _extract_role(self, text: str) -> str:
        """Extract job role from text."""
        role_patterns = [
            r'\b(CEO|CTO|CFO|COO|Founder|Co-Founder|Director|Manager|Lead|Engineer|Developer|Designer)\b',
        ]
        for pattern in role_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "Team Member"

    def _extract_features(self, text: str) -> List[Dict[str, str]]:
        """Extract features from text."""
        features = []
        # Split by common delimiters
        parts = re.split(r'[,;•\-]', text)
        for part in parts[:5]:
            part = part.strip()
            if len(part) > 5:
                features.append({
                    "feature": part[:50],
                    "value": "✓"
                })
        if not features:
            features.append({"feature": text[:50], "value": "✓"})
        return features

    def _extract_stats(self, items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract statistics from items."""
        stats = []
        for item in items:
            text = f"{item.get('title', '')} {item.get('description', '')}"
            # Look for number patterns
            matches = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(%|K|M|B)?\s*([A-Za-z][^.]*)', text)
            for value, unit, label in matches[:2]:
                stats.append({
                    "label": label.strip()[:30],
                    "value": f"{value}{unit}" if unit else value
                })

        if not stats:
            # Fallback: use item titles as labels
            for item in items[:4]:
                stats.append({
                    "label": item.get("title", "")[:30],
                    "value": "N/A"
                })

        return stats[:6]

    def _create_fallback_card(self, query: str, response: str) -> Dict[str, Any]:
        """Create a simple fallback card when generation fails."""
        return {
            "version": "1.0",
            "root": {
                "type": "simple-card",
                "props": {
                    "title": "Response",
                    "content": response[:500],
                    "icon": "info"
                }
            },
            "_metadata": {
                "tier": "fallback",
                "tier_name": "Fallback Card",
                "template_type": "simple-card",
                "mode": "error_fallback",
                "description": "Generated fallback due to error"
            }
        }


# Singleton instance
_generator: Optional[A2UIGenerator] = None


def get_a2ui_generator(enabled: bool = True) -> A2UIGenerator:
    """Get or create the A2UI generator singleton."""
    global _generator
    if _generator is None:
        _generator = A2UIGenerator(enabled=enabled)
    return _generator
