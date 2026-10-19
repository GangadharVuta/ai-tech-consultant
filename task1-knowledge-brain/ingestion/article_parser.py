import hashlib
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

class ArticleParser:
    """
    Parses Brilliant Directories help center article HTML.
    Extracts structured text, headings, breadcrumb hierarchy, and associated screenshots with context.
    """

    @staticmethod
    def compute_hash(text: str) -> str:
        """Computes SHA-256 hash of clean text for change detection."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def parse(self, html_content: str, source_url: str) -> Dict:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Remove non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
            element.decompose()

        # 2. Extract Title
        title = ""
        title_tag = soup.find("h1") or soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove trailing site branding like " - Brilliant Directories Solution Center"
            title = re.sub(r"\s*[-|]\s*Brilliant Directories.*$", "", title, flags=re.I)
        if not title:
            # Fallback to URL slug
            slug = source_url.rstrip("/").split("/")[-1]
            title = slug.replace("-", " ").title()

        # 3. Extract Breadcrumbs (Category / Folder)
        category = "General"
        folder = "General"
        breadcrumb_items = soup.find_all(class_=re.compile(r"breadcrumb", re.I))
        if breadcrumb_items:
            crumbs = [c.get_text(strip=True) for c in breadcrumb_items[0].find_all("a")]
            if len(crumbs) >= 2:
                category = crumbs[1]
            if len(crumbs) >= 3:
                folder = crumbs[2]

        # 4. Find Main Content Container
        # Freshdesk / BD typically uses .article-content, .article__body, .content, or article tag
        main_content = (
            soup.find("article")
            or soup.find(class_=re.compile(r"article[-_]body|article[-_]content|solution[-_]body", re.I))
            or soup.find(id=re.compile(r"article[-_]body|solution[-_]body", re.I))
            or soup.find("main")
            or soup.body
        )

        if not main_content:
            main_content = soup

        # 5. Extract Images and their surrounding text context
        images: List[Dict] = []
        for img in main_content.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            
            # Skip tiny tracker icons or spacer gifs
            if any(ext in src.lower() for ext in [".ico", "avatar", "spacer", "badge"]):
                continue

            alt = img.get("alt", "").strip()
            
            # Find surrounding text (previous paragraph or parent paragraph text)
            parent = img.parent
            context_text = ""
            prev_p = img.find_previous(["p", "li", "h2", "h3", "h4"])
            if prev_p:
                context_text = prev_p.get_text(strip=True)[:250]
            elif parent and parent.name in ["p", "div"]:
                context_text = parent.get_text(strip=True)[:250]

            images.append({
                "src": src,
                "alt": alt,
                "surrounding_context": context_text
            })

        # 6. Extract Headings and Hierarchical Sections
        sections: List[Dict] = []
        current_heading = "Overview"
        current_paras: List[str] = []
        current_images: List[str] = []

        for elem in main_content.find_all(["h2", "h3", "h4", "p", "ul", "ol", "table"]):
            if elem.name in ["h2", "h3", "h4"]:
                # Save previous section if it has content
                if current_paras:
                    sections.append({
                        "heading": current_heading,
                        "text": "\n\n".join(current_paras),
                        "images": list(current_images)
                    })
                    current_paras = []
                    current_images = []
                current_heading = elem.get_text(strip=True)
            elif elem.name in ["p", "ul", "ol", "table"]:
                txt = elem.get_text(" ", strip=True)
                if txt and len(txt) > 5:
                    current_paras.append(txt)
                for img in elem.find_all("img"):
                    isrc = img.get("src") or img.get("data-src")
                    if isrc and isrc not in current_images:
                        current_images.append(isrc)

        if current_paras:
            sections.append({
                "heading": current_heading,
                "text": "\n\n".join(current_paras),
                "images": list(current_images)
            })

        # Fallback if no sections were identified
        full_text = main_content.get_text("\n", strip=True)
        if not sections and full_text:
            sections.append({
                "heading": "Overview",
                "text": full_text,
                "images": [img["src"] for img in images]
            })

        content_hash = self.compute_hash(full_text)

        return {
            "url": source_url,
            "title": title,
            "category": category,
            "folder": folder,
            "full_text": full_text,
            "sections": sections,
            "images": images,
            "content_hash": content_hash
        }
