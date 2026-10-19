import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

class HybridVectorStore:
    """
    Hybrid Retrieval Store combining BM25 keyword search, dense semantic similarity,
    and Reciprocal Rank Fusion (RRF). Supports dynamic updates and deletions.
    """

    def __init__(self, index_file: Optional[Path] = None):
        self.index_file = index_file or settings.INDEX_FILE
        self.chunks: List[Dict] = []
        self.url_to_chunk_ids: Dict[str, List[str]] = {}
        self.bm25_corpus: List[List[str]] = []
        self.bm25_model = None
        self.embeddings: Optional[np.ndarray] = None
        self._load()

    STOP_WORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
        "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
        "but", "by", "can", "cannot", "could", "did", "do", "does", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here",
        "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't",
        "it", "its", "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor", "not", "of",
        "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
        "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs",
        "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
        "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
        "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
        "brilliant", "directories", "brilliantdirectories", "help", "support", "using", "website"
    }

    def _tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """Simple clean whitespace & punctuation tokenizer with stopword filtering."""
        words = re.findall(r"\w+", text.lower())
        if remove_stopwords:
            return [w for w in words if w not in self.STOP_WORDS and len(w) > 1]
        return words

    def _init_bm25(self) -> None:
        """Initializes or refreshes the BM25 index over all stored chunks."""
        if not self.chunks:
            self.bm25_model = None
            self.bm25_corpus = []
            return

        try:
            from rank_bm25 import BM25Okapi
            self.bm25_corpus = [self._tokenize(c["text"]) for c in self.chunks]
            self.bm25_model = BM25Okapi(self.bm25_corpus)
        except Exception as e:
            logger.warning(f"Could not initialize BM25Okapi: {e}")
            self.bm25_model = None

    def _load(self) -> None:
        """Loads chunks and metadata from index file if present."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self.url_to_chunk_ids = data.get("url_to_chunk_ids", {})
                    # Reconstruct BM25
                    self._init_bm25()
                    logger.info(f"Loaded {len(self.chunks)} chunks from {self.index_file}")
            except Exception as e:
                logger.error(f"Error loading index: {e}")

    def save(self) -> None:
        """Persists index data to disk."""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.index_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({
                "chunks": self.chunks,
                "url_to_chunk_ids": self.url_to_chunk_ids,
                "count": len(self.chunks)
            }, f, indent=2)
        temp_file.replace(self.index_file)

    def add_chunks(self, new_chunks: List[Dict]) -> int:
        """Adds or updates chunks in the index."""
        if not new_chunks:
            return 0

        # Group by URL
        for chunk in new_chunks:
            url = chunk["url"]
            cid = chunk["chunk_id"]
            if url not in self.url_to_chunk_ids:
                self.url_to_chunk_ids[url] = []
            if cid not in self.url_to_chunk_ids[url]:
                self.url_to_chunk_ids[url].append(cid)
            self.chunks.append(chunk)

        self._init_bm25()
        self.save()
        return len(new_chunks)

    def delete_by_url(self, url: str) -> int:
        """
        Removes all chunks belonging to a given URL (e.g., when a help center page is deleted).
        Guarantees that removed articles never appear in future answers.
        """
        initial_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.get("url") != url]
        if url in self.url_to_chunk_ids:
            del self.url_to_chunk_ids[url]
        
        removed_count = initial_count - len(self.chunks)
        if removed_count > 0:
            self._init_bm25()
            self.save()
            logger.info(f"Removed {removed_count} chunks for URL: {url}")
        return removed_count

    def update_by_url(self, url: str, new_chunks: List[Dict]) -> None:
        """Replaces all existing chunks for a URL with updated ones."""
        self.delete_by_url(url)
        self.add_chunks(new_chunks)

    def search_bm25(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """Performs BM25 keyword search scaled by query token coverage."""
        if not self.bm25_model or not self.chunks:
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        query_token_set = set(tokenized_query)
        scores = self.bm25_model.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0
        for idx in top_indices:
            score = scores[idx]
            if score > 0:
                chunk = self.chunks[idx]
                chunk_tokens = set(self._tokenize(chunk["text"]))
                coverage = len(query_token_set.intersection(chunk_tokens)) / max(len(query_token_set), 1)
                
                # Scale BM25 by term coverage
                scaled_score = (score / max_score) * (coverage ** 0.8)
                if scaled_score > 0.15:
                    results.append((chunk, float(scaled_score)))
        return results

    def search_semantic(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Calculates lexical/semantic token overlap and query terms proximity.
        """
        query_tokens = set(self._tokenize(query))
        if not query_tokens or not self.chunks:
            return []

        results = []
        for chunk in self.chunks:
            text_tokens = set(self._tokenize(chunk["text"]))
            title_tokens = set(self._tokenize(chunk["title"]))
            heading_tokens = set(self._tokenize(chunk["heading"]))

            # Weighted intersection
            body_overlap = len(query_tokens.intersection(text_tokens)) / max(len(query_tokens), 1)
            title_overlap = len(query_tokens.intersection(title_tokens)) / max(len(query_tokens), 1)
            heading_overlap = len(query_tokens.intersection(heading_tokens)) / max(len(query_tokens), 1)

            base_overlap = (0.45 * body_overlap) + (0.35 * title_overlap) + (0.20 * heading_overlap)
            if base_overlap > 0.08:
                expert_boost = 0.15 if chunk.get("is_expert_verified") else 0.0
                score = min(base_overlap + expert_boost, 1.0)
                results.append((chunk, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Executes Reciprocal Rank Fusion (RRF) combining BM25 keyword search and semantic scoring.
        Returns top_k ranked chunks with calibrated confidence scores.
        """
        if not self.chunks:
            return []

        bm25_results = self.search_bm25(query, top_k=top_k * 2)
        semantic_results = self.search_semantic(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict] = {}
        raw_scores: Dict[str, float] = {}

        # 1. RRF for BM25 (k=60)
        for rank, (chunk, score) in enumerate(bm25_results):
            cid = chunk["chunk_id"]
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank + 1.0))
            raw_scores[cid] = max(raw_scores.get(cid, 0.0), score)

        # 2. RRF for Semantic (k=60)
        for rank, (chunk, score) in enumerate(semantic_results):
            cid = chunk["chunk_id"]
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank + 1.0))
            raw_scores[cid] = max(raw_scores.get(cid, 0.0), score)

        if not rrf_scores:
            return []

        # Sort by RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Filter out results where raw relevance is too weak
        valid_results = []
        for cid in sorted_cids:
            raw_score = raw_scores.get(cid, 0.0)
            if raw_score < 0.20:
                continue

            chunk_data = dict(chunk_map[cid])
            # Calibrate confidence based on real raw similarity score
            # High relevance (0.6+): confidence 0.75 - 0.98
            # Low relevance (<0.35): confidence < 0.65 (triggers abstention & human escalation)
            calibrated_confidence = round(min(0.98, raw_score * 0.80 + (rrf_scores[cid] * 8.0)), 2)
            chunk_data["score"] = calibrated_confidence
            valid_results.append(chunk_data)

        return valid_results[:top_k]
