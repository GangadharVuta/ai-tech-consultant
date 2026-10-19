import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from app.config import settings
from retrieval.vector_store import HybridVectorStore

logger = logging.getLogger(__name__)

class EscalationManager:
    """
    Manages unanswered customer questions, creates tasks for human experts,
    and feeds resolved expert answers back into the knowledge memory.
    """

    def __init__(self, escalations_file: Optional[Path] = None):
        self.escalations_file = escalations_file or settings.ESCALATIONS_FILE
        self.escalations: Dict[str, Dict] = self._load()

    def _load(self) -> Dict[str, Dict]:
        if self.escalations_file.exists():
            try:
                with open(self.escalations_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read escalations file: {e}")
        return {}

    def _save(self) -> None:
        self.escalations_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.escalations_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self.escalations, f, indent=2)
        temp_file.replace(self.escalations_file)

    def create_escalation(
        self,
        question: str,
        retrieved_sources: List[Dict],
        confidence: float,
        reason: str
    ) -> Dict:
        """Creates a new human escalation task."""
        esc_id = f"ESC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        item = {
            "id": esc_id,
            "question": question,
            "retrieved_sources": retrieved_sources,
            "confidence": confidence,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "expert_name": None,
            "expert_answer": None,
            "supporting_notes": None
        }
        self.escalations[esc_id] = item
        self._save()
        logger.info(f"Created escalation {esc_id} for question: '{question}'")
        return item

    def list_escalations(self, status: Optional[str] = None) -> List[Dict]:
        """Lists escalation tasks, optionally filtered by status."""
        items = list(self.escalations.values())
        if status:
            items = [it for it in items if it.get("status") == status]
        return sorted(items, key=lambda x: x["created_at"], reverse=True)

    def resolve_escalation(
        self,
        escalation_id: str,
        expert_name: str,
        expert_answer: str,
        supporting_notes: str,
        vector_store: HybridVectorStore
    ) -> Optional[Dict]:
        """
        Resolves an escalation task and indexes the approved expert answer
        directly back into the vector store as a verified knowledge chunk.
        """
        if escalation_id not in self.escalations:
            return None

        item = self.escalations[escalation_id]
        item["status"] = "resolved"
        item["resolved_at"] = datetime.now(timezone.utc).isoformat()
        item["expert_name"] = expert_name
        item["expert_answer"] = expert_answer
        item["supporting_notes"] = supporting_notes
        self._save()

        # Create new verified knowledge chunk
        chunk_id = f"expert_{escalation_id.lower().replace('-', '_')}"
        doc_url = f"https://support.brilliantdirectories.com/support/expert-answers/{escalation_id}"
        
        chunk = {
            "chunk_id": chunk_id,
            "url": doc_url,
            "title": f"Expert Answer: {item['question'][:60]}",
            "category": "Expert Resolutions",
            "folder": "Human in the Loop",
            "heading": "Authoritative Expert Solution",
            "text": (
                f"Document: Expert Resolution {escalation_id}\n"
                f"Question Asked: {item['question']}\n"
                f"Verified Expert Solution ({expert_name}):\n{expert_answer}\n"
                f"Additional Policy / Operational Notes:\n{supporting_notes}"
            ),
            "raw_body": expert_answer,
            "images": [],
            "is_expert_verified": True
        }

        # Index chunk into vector store
        vector_store.update_by_url(doc_url, [chunk])
        logger.info(f"Escalation {escalation_id} resolved and indexed into Knowledge Brain.")
        return item
