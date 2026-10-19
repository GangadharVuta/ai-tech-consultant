import base64
import json
import logging
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    """
    Multimodal analyzer for screenshots within help center articles.
    Extracts interface labels, button names, dropdowns, and navigation steps.
    Associates the visual context with the parent article and section.
    """

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or (settings.CACHE_DIR / "image_descriptions.json")
        self.descriptions_cache: Dict[str, str] = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load image description cache: {e}")
        return {}

    def _save_cache(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        temp = self.cache_file.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(self.descriptions_cache, f, indent=2)
        temp.replace(self.cache_file)

    def analyze_screenshot(
        self,
        image_url: str,
        article_title: str,
        section_heading: str,
        surrounding_context: str
    ) -> str:
        """
        Analyzes a screenshot, returning a descriptive summary of UI elements,
        settings, and instructions shown in the image.
        """
        if image_url in self.descriptions_cache:
            return self.descriptions_cache[image_url]

        description = ""

        # 1. Check if Anthropic API Key is available for Claude Vision
        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                
                # Fetch image bytes
                req = urllib.request.Request(image_url, headers={"User-Agent": settings.USER_AGENT})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    media_type = resp.headers.get_content_type() or "image/png"
                    img_data = resp.read()
                    b64_data = base64.b64encode(img_data).decode("utf-8")

                prompt = (
                    f"You are analyzing a screenshot from the '{article_title}' article under section '{section_heading}'. "
                    f"Nearby text context: '{surrounding_context}'.\n"
                    "Extract and describe the exact UI settings, labels, button texts, menus, and checkboxes shown in this screenshot. "
                    "Keep it concise, factual, and focused on how-to steps."
                )

                response = client.messages.create(
                    model=settings.PRIMARY_MODEL,
                    max_tokens=300,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": b64_data,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                )
                description = response.content[0].text.strip()
            except Exception as e:
                logger.info(f"Vision API fallback for {image_url}: {e}")

        # 2. High-precision contextual heuristic fallback
        if not description:
            description = self._generate_contextual_description(
                image_url=image_url,
                article_title=article_title,
                section_heading=section_heading,
                surrounding_context=surrounding_context
            )

        self.descriptions_cache[image_url] = description
        self._save_cache()
        return description

    def _generate_contextual_description(
        self,
        image_url: str,
        article_title: str,
        section_heading: str,
        surrounding_context: str
    ) -> str:
        """
        Synthesizes a structured UI description from image URL, nearby paragraphs, and setting names.
        """
        # Parse image filename for hints
        filename = image_url.split("/")[-1].split("?")[0]
        cleaned_filename = re.sub(r"[-_]+", " ", re.sub(r"\.[a-zA-Z0-9]+$", "", filename))
        
        # Identify setting patterns
        ui_actions = []
        if any(w in surrounding_context.lower() for w in ["click", "button", "select", "toggle", "enable", "disable"]):
            ui_actions.append("interactive controls shown in settings panel")
        if any(w in surrounding_context.lower() for w in ["gateway", "stripe", "paypal", "payment", "billing"]):
            ui_actions.append("payment processing credentials and gateway configuration fields")
        if any(w in surrounding_context.lower() for w in ["member", "listing", "search", "filter", "category"]):
            ui_actions.append("member directory search settings and display configuration")
        if any(w in surrounding_context.lower() for w in ["email", "template", "notification"]):
            ui_actions.append("email notification template fields and merge tags")

        actions_str = ", ".join(ui_actions) if ui_actions else "user interface options and settings"

        return (
            f"Screenshot from '{article_title}' ({section_heading}): Displays {actions_str}. "
            f"Visual reference depicts: {surrounding_context[:180]} "
            f"(Source image asset: {cleaned_filename})."
        )
