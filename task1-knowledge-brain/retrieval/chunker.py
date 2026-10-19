import hashlib
import re
from typing import Dict, List, Optional

class HierarchicalChunker:
    """
    Splits articles into semantically coherent chunks based on section headings,
    preserving context, prerequisites, and associated screenshot descriptions.
    """

    def __init__(self, target_chunk_size: int = 400, overlap_sentences: int = 2):
        self.target_chunk_size = target_chunk_size
        self.overlap_sentences = overlap_sentences

    def chunk_article(self, parsed_article: Dict, image_descriptions: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Chunks an article into structured units with complete metadata and image references.
        """
        image_descriptions = image_descriptions or {}
        chunks: List[Dict] = []
        
        url = parsed_article["url"]
        title = parsed_article["title"]
        category = parsed_article.get("category", "General")
        folder = parsed_article.get("folder", "General")
        sections = parsed_article.get("sections", [])

        # If no sections, treat the full text as one section
        if not sections and parsed_article.get("full_text"):
            sections = [{"heading": "Overview", "text": parsed_article["full_text"], "images": []}]

        for s_idx, section in enumerate(sections):
            heading = section.get("heading", "Overview")
            sec_text = section.get("text", "").strip()
            sec_images = section.get("images", [])

            if not sec_text:
                continue

            # Build image descriptions block for this section
            img_blocks = []
            for img_url in sec_images:
                desc = image_descriptions.get(img_url)
                if desc:
                    img_blocks.append(f"[Visual Screenshot Note: {desc}]")
                else:
                    img_blocks.append(f"[Visual Screenshot: {img_url}]")
            
            images_context = "\n".join(img_blocks) if img_blocks else ""

            # Split section text into paragraphs
            paragraphs = [p.strip() for p in sec_text.split("\n\n") if p.strip()]
            
            current_chunk_paras: List[str] = []
            current_word_count = 0

            for para in paragraphs:
                words = len(para.split())
                if current_word_count + words > self.target_chunk_size and current_chunk_paras:
                    # Flush current chunk
                    body_text = "\n\n".join(current_chunk_paras)
                    chunk_id = hashlib.sha256(f"{url}_{s_idx}_{len(chunks)}".encode()).hexdigest()[:12]
                    
                    full_chunk_text = (
                        f"Document: {title}\n"
                        f"Category: {category} > {folder}\n"
                        f"Section: {heading}\n"
                        f"Content:\n{body_text}"
                    )
                    if images_context:
                        full_chunk_text += f"\n\nAssociated Visual Context:\n{images_context}"

                    chunks.append({
                        "chunk_id": chunk_id,
                        "url": url,
                        "title": title,
                        "category": category,
                        "folder": folder,
                        "heading": heading,
                        "text": full_chunk_text,
                        "raw_body": body_text,
                        "images": sec_images,
                        "is_expert_verified": False
                    })

                    # Maintain slight overlap if multiple paragraphs
                    if len(current_chunk_paras) > 1:
                        current_chunk_paras = [current_chunk_paras[-1], para]
                        current_word_count = len(current_chunk_paras[0].split()) + words
                    else:
                        current_chunk_paras = [para]
                        current_word_count = words
                else:
                    current_chunk_paras.append(para)
                    current_word_count += words

            # Flush remaining paragraphs
            if current_chunk_paras:
                body_text = "\n\n".join(current_chunk_paras)
                chunk_id = hashlib.sha256(f"{url}_{s_idx}_{len(chunks)}".encode()).hexdigest()[:12]
                
                full_chunk_text = (
                    f"Document: {title}\n"
                    f"Category: {category} > {folder}\n"
                    f"Section: {heading}\n"
                    f"Content:\n{body_text}"
                )
                if images_context:
                    full_chunk_text += f"\n\nAssociated Visual Context:\n{images_context}"

                chunks.append({
                    "chunk_id": chunk_id,
                    "url": url,
                    "title": title,
                    "category": category,
                    "folder": folder,
                    "heading": heading,
                    "text": full_chunk_text,
                    "raw_body": body_text,
                    "images": sec_images,
                    "is_expert_verified": False
                })

        return chunks
