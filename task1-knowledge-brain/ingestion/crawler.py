import asyncio
import json
import logging
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from app.config import settings
from ingestion.sitemap_parser import SitemapParser
from ingestion.article_parser import ArticleParser
from multimodal.image_analyzer import ImageAnalyzer
from retrieval.chunker import HierarchicalChunker
from retrieval.vector_store import HybridVectorStore

logger = logging.getLogger(__name__)

class PoliteCrawler:
    """
    Polite, resumable crawler for Brilliant Directories Solution Center.
    Features:
    - Rate limiting with configurable per-request delay
    - Checkpoint persistence in manifest.json
    - Exponential backoff retry on transient errors
    - Deduplication and idempotency
    - Removal de-indexing
    """

    def __init__(
        self,
        delay_seconds: float = settings.CRAWL_DELAY_SECONDS,
        max_retries: int = 3,
        vector_store: Optional[HybridVectorStore] = None
    ):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.sitemap_parser = SitemapParser()
        self.article_parser = ArticleParser()
        self.image_analyzer = ImageAnalyzer()
        self.chunker = HierarchicalChunker()
        self.vector_store = vector_store or HybridVectorStore()
        self.is_running = False

    def fetch_page_with_retry(self, url: str) -> Optional[str]:
        """Fetches page HTML with exponential backoff on transient errors."""
        backoff = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.delay_seconds)
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": settings.USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml"
                    }
                )
                with urllib.request.urlopen(req, timeout=settings.REQUEST_TIMEOUT) as resp:
                    if resp.status == 200:
                        return resp.read().decode("utf-8", errors="ignore")
                    elif resp.status == 404:
                        logger.warning(f"404 Not Found for {url}; will not retry.")
                        return None
                    else:
                        logger.warning(f"Status {resp.status} on attempt {attempt} for {url}")
            except Exception as e:
                logger.warning(f"Network error on attempt {attempt} for {url}: {e}")

            time.sleep(backoff)
            backoff *= 2.0

        return None

    def ingest_url(self, url: str, lastmod: Optional[str] = None) -> bool:
        """
        Fetches, parses, chunks, and indexes a single article.
        Returns True on success, False on failure.
        """
        html = self.fetch_page_with_retry(url)
        if not html:
            return False

        try:
            parsed = self.article_parser.parse(html, source_url=url)
            
            # Analyze screenshots
            image_descriptions: Dict[str, str] = {}
            for img_info in parsed.get("images", []):
                src = img_info["src"]
                desc = self.image_analyzer.analyze_screenshot(
                    image_url=src,
                    article_title=parsed["title"],
                    section_heading=img_info.get("alt") or "Screenshot",
                    surrounding_context=img_info.get("surrounding_context", "")
                )
                image_descriptions[src] = desc

            # Chunk document
            chunks = self.chunker.chunk_article(parsed, image_descriptions=image_descriptions)

            # Update vector store
            self.vector_store.update_by_url(url, chunks)

            # Update manifest
            manifest = self.sitemap_parser.load_manifest()
            manifest[url] = {
                "title": parsed["title"],
                "category": parsed["category"],
                "folder": parsed["folder"],
                "lastmod": lastmod,
                "content_hash": parsed["content_hash"],
                "chunk_count": len(chunks),
                "image_count": len(parsed.get("images", [])),
                "status": "indexed",
                "last_crawled": datetime.now(timezone.utc).isoformat(),
                "error": None
            }
            self.sitemap_parser.save_manifest(manifest)
            return True

        except Exception as e:
            logger.error(f"Error parsing/indexing {url}: {e}")
            manifest = self.sitemap_parser.load_manifest()
            manifest[url] = {
                "lastmod": lastmod,
                "status": "failed",
                "error": str(e),
                "last_crawled": datetime.now(timezone.utc).isoformat()
            }
            self.sitemap_parser.save_manifest(manifest)
            return False

    def run_sync(self, max_pages: Optional[int] = None) -> Dict:
        """
        Runs incremental ingestion:
        1. Checks sitemap
        2. Detects additions, updates, removals
        3. Crawls additions & updates politely
        4. Removes deletions from vector index
        """
        self.is_running = True
        logger.info("Starting polite sitemap synchronization...")

        try:
            xml_data = self.sitemap_parser.fetch_sitemap_xml()
            remote_entries = self.sitemap_parser.parse_sitemap_entries(xml_data)
        except Exception as e:
            logger.error(f"Failed to fetch/parse sitemap: {e}")
            self.is_running = False
            return {"error": f"Sitemap unreachable: {e}"}

        added, updated, removed, unchanged = self.sitemap_parser.compute_diff(remote_entries)

        logger.info(
            f"Sitemap Sync: {len(remote_entries)} total entries | "
            f"Added: {len(added)} | Updated: {len(updated)} | Removed: {len(removed)} | Unchanged: {len(unchanged)}"
        )

        # 1. Prune removed pages
        for r_url in removed:
            self.vector_store.delete_by_url(r_url)
            manifest = self.sitemap_parser.load_manifest()
            if r_url in manifest:
                del manifest[r_url]
                self.sitemap_parser.save_manifest(manifest)

        # 2. Ingest added and updated pages
        to_process = added + updated
        if max_pages is not None:
            to_process = to_process[:max_pages]

        processed_count = 0
        success_count = 0

        for url in to_process:
            lastmod = remote_entries.get(url)
            ok = self.ingest_url(url, lastmod=lastmod)
            processed_count += 1
            if ok:
                success_count += 1

        self.is_running = False
        return {
            "total_in_sitemap": len(remote_entries),
            "added_found": len(added),
            "updated_found": len(updated),
            "removed_pruned": len(removed),
            "processed": processed_count,
            "succeeded": success_count,
            "total_indexed_chunks": len(self.vector_store.chunks)
        }
