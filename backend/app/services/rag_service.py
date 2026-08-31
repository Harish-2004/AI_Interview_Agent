"""LlamaIndex RAG Service for Resume & Job Description Indexing and Semantic Retrieval."""

import os
import re
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.node_parser import SimpleNodeParser

from app.config import settings

# Global LlamaIndex Core Settings Configuration
# Set MockEmbedding fallback when running offline or without OpenAI API key
if not os.environ.get("OPENAI_API_KEY") and not settings.openai_api_key:
    Settings.embed_model = MockEmbedding(embed_dim=1536)


class LlamaIndexRAGService:
    """RAG Service managing document indexing, node parsing, and retrieval via LlamaIndex."""

    def __init__(self):
        self._node_parser = SimpleNodeParser.from_defaults(chunk_size=256, chunk_overlap=32)
        self._resume_indices: dict[int, VectorStoreIndex] = {}
        self._jd_indices: dict[int, VectorStoreIndex] = {}
        self._resume_texts: dict[int, str] = {}

    def index_resume(self, candidate_id: int, resume_text: str) -> None:
        """Index a candidate resume using LlamaIndex Document and Node parser."""
        self._resume_texts[candidate_id] = resume_text
        doc = Document(text=resume_text, doc_id=f"resume_{candidate_id}", extra_info={"candidate_id": candidate_id})
        nodes = self._node_parser.get_nodes_from_documents([doc])
        index = VectorStoreIndex(nodes)
        self._resume_indices[candidate_id] = index

    def index_jd(self, job_id: int, jd_text: str) -> None:
        """Index a job description using LlamaIndex Document and Node parser."""
        doc = Document(text=jd_text, doc_id=f"jd_{job_id}", extra_info={"job_id": job_id})
        nodes = self._node_parser.get_nodes_from_documents([doc])
        index = VectorStoreIndex(nodes)
        self._jd_indices[job_id] = index

    def retrieve_resume_context(self, candidate_id: int, query: str, top_k: int | None = None) -> list[str]:
        """Retrieve top_k matching resume chunks for a given query."""
        k = top_k or settings.llama_index_top_k
        if candidate_id in self._resume_indices:
            try:
                retriever = self._resume_indices[candidate_id].as_retriever(similarity_top_k=k)
                nodes = retriever.retrieve(query)
                return [n.node.get_content() for n in nodes]
            except Exception:
                pass

        # Fallback heuristic retrieval if vector index is uninitialized or fallback mode
        text = self._resume_texts.get(candidate_id, "")
        if not text:
            return []
        
        sentences = [s.strip() for s in re.split(r"[.\n]", text) if s.strip()]
        query_words = set(query.lower().split())
        scored = []
        for s in sentences:
            s_words = set(s.lower().split())
            score = len(query_words.intersection(s_words))
            scored.append((score, s))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]

    def retrieve_jd_context(self, job_id: int, query: str, top_k: int | None = None) -> list[str]:
        """Retrieve top_k matching JD chunks for a given query."""
        k = top_k or settings.llama_index_top_k
        if job_id in self._jd_indices:
            try:
                retriever = self._jd_indices[job_id].as_retriever(similarity_top_k=k)
                nodes = retriever.retrieve(query)
                return [n.node.get_content() for n in nodes]
            except Exception:
                pass
        return []


# Global singleton instance for app-wide RAG retrieval
rag_service = LlamaIndexRAGService()
