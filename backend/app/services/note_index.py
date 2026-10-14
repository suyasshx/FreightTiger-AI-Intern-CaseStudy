"""
RouteGuard AI - Context Note Vector Index Service
Indexes context_notes.csv into ChromaDB using sentence-transformers/all-MiniLM-L6-v2 embeddings.
Maintains metadata for deterministic hard evidence gating and lexical fallback capabilities.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

from backend.app.config import settings


class ContextNoteIndex:
    """
    Manages vector indexing and retrieval for real-world contextual notes.
    """

    def __init__(
        self,
        collection_name: str = "freight_context_notes",
        persist_dir: Optional[Path] = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir or settings.chroma_db_dir
        self.model_name = model_name
        self.client = None
        self.collection = None
        self.notes_data: Dict[str, Dict[str, Any]] = {}
        self.embedding_function = None
        self.initialized = False

    def initialize(self, notes_df: pd.DataFrame) -> None:
        """
        Build or refresh the vector collection from context notes.
        """
        # Store structured note objects in memory for fast lookup
        self.notes_data.clear()
        for _, row in notes_df.iterrows():
            nid = str(row["note_id"]).strip()
            self.notes_data[nid] = {
                "note_id": nid,
                "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
                "applies_to": str(row["applies_to"]).strip(),
                "note": str(row["note"]).strip()
            }

        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.model_name
            )
        except Exception as e:
            # Documented fallback if model cannot be instantiated
            print(f"[NoteIndex Warning] SentenceTransformer loading warning: {e}. Utilizing local client.")
            self.embedding_function = None

        # Create persistent ChromaDB client
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))

        # Reset or create collection
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        if self.embedding_function:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        # Populate collection
        documents = []
        ids = []
        metadatas = []

        for nid, data in self.notes_data.items():
            doc_text = (
                f"Note ID: {nid}. Date: {data['date']}. "
                f"Applicable Route: {data['applies_to']}. "
                f"Context: {data['note']}"
            )
            documents.append(doc_text)
            ids.append(nid)
            metadatas.append({
                "note_id": nid,
                "date": data["date"],
                "applies_to": data["applies_to"],
                "note_text": data["note"]
            })

        self.collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        self.initialized = True

    def query(
        self,
        query_text: str,
        n_results: int = 3,
        route_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k candidate notes for a given query text.
        """
        if not self.initialized or not self.collection:
            raise RuntimeError("ContextNoteIndex must be initialized before querying.")

        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, len(self.notes_data))
        )

        candidates = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for idx in range(len(results["ids"][0])):
                nid = results["ids"][0][idx]
                dist = float(results["distances"][0][idx]) if "distances" in results and results["distances"] else 0.0
                # Cosine distance to similarity: similarity = 1.0 - distance
                similarity = max(0.0, 1.0 - dist)
                meta = results["metadatas"][0][idx]

                candidates.append({
                    "note_id": nid,
                    "date": meta["date"],
                    "applies_to": meta["applies_to"],
                    "note": meta["note_text"],
                    "note_text": meta["note_text"],
                    "distance": dist,
                    "similarity_score": round(similarity, 4)
                })

        return candidates

    def get_note_by_id(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Direct retrieval by exact note ID."""
        return self.notes_data.get(note_id)

    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Retrieve all indexed context notes."""
        return list(self.notes_data.values())


# Global singleton instance
note_index = ContextNoteIndex()
