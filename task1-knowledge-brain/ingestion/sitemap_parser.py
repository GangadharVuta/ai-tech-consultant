import json
import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

class SitemapParser:
    """
    Parses help center sitemap XML, extracts URLs and last-modified dates,
    maintains an incremental manifest, and identifies additions, updates, and deletions.
    """
    def __init__(self, sitemap_url: str = settings.SITEMAP_URL, manifest_path: Path = settings.MANIFEST_FILE):
        self.sitemap_url = sitemap_url
        self.manifest_path = manifest_path

    def load_manifest(self) -> Dict[str, dict]:
        """Loads the current ingestion manifest from disk, or returns empty dict."""
        if not self.manifest_path.exists():
            return {}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read manifest file: {e}")
            return {}

    def save_manifest(self, manifest: Dict[str, dict]) -> None:
        """Atomically saves the ingestion manifest to disk."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.manifest_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        temp_path.replace(self.manifest_path)

    def fetch_sitemap_xml(self) -> str:
        """Downloads sitemap XML from the configured remote URL."""
        req = urllib.request.Request(
            self.sitemap_url,
            headers={"User-Agent": settings.USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=settings.REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Sitemap download failed with status {resp.status}")
            return resp.read().decode("utf-8", errors="ignore")

    def parse_sitemap_entries(self, xml_content: str) -> Dict[str, Optional[str]]:
        """
        Parses sitemap XML and returns dict mapping {url: lastmod_iso_string}.
        Only indexes article solution pages (/support/solutions/articles/...).
        """
        entries: Dict[str, Optional[str]] = {}
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Malformed XML in sitemap: {e}")
            return entries

        # Standard sitemap namespace
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        for url_node in root.findall(".//ns:url", ns):
            loc_node = url_node.find("ns:loc", ns)
            if loc_node is None or not loc_node.text:
                continue
            url = loc_node.text.strip()
            
            # Filter specifically to knowledge articles for maximum relevance
            # e.g., https://support.brilliantdirectories.com/support/solutions/articles/...
            if "/support/solutions/articles/" not in url:
                continue
                
            lastmod_node = url_node.find("ns:lastmod", ns)
            lastmod = lastmod_node.text.strip() if (lastmod_node is not None and lastmod_node.text) else None
            entries[url] = lastmod

        return entries

    def compute_diff(self, remote_entries: Dict[str, Optional[str]]) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Compares live sitemap entries against the stored manifest.
        Returns: (added_urls, updated_urls, removed_urls, unchanged_urls)
        """
        manifest = self.load_manifest()
        
        added: List[str] = []
        updated: List[str] = []
        unchanged: List[str] = []
        removed: List[str] = []

        for url, remote_lastmod in remote_entries.items():
            if url not in manifest:
                added.append(url)
            else:
                local_entry = manifest[url]
                local_lastmod = local_entry.get("lastmod")
                # If remote lastmod exists and differs from local lastmod, mark updated
                if remote_lastmod and local_lastmod and remote_lastmod != local_lastmod:
                    updated.append(url)
                elif local_entry.get("status") != "indexed":
                    # Pending or failed in previous run
                    updated.append(url)
                else:
                    unchanged.append(url)

        for url in manifest.keys():
            if url not in remote_entries and manifest[url].get("status") == "indexed":
                removed.append(url)

        return added, updated, removed, unchanged
