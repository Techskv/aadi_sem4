import os
import logging
from typing import List, Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Base path for vector store storage
VECTOR_STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "storage", "vector_store"
)

# ─── Lazy availability flags ───────────────────────────────────────────────────
FAISS_AVAILABLE = False
EMBEDDINGS_AVAILABLE = False

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.document import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("langchain-community or langchain-text-splitters not installed. RAG disabled.")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    logger.warning("langchain-huggingface not installed. RAG disabled.")


class RAGService:
    """
    RAG Service - Handles indexing and retrieval of reference materials for exams.
    Gracefully disabled if dependencies (FAISS, HuggingFace embeddings) are unavailable.
    """

    def __init__(self):
        self.embeddings = None
        self._available = False

        if not FAISS_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            logger.warning("RAG Service: dependencies missing. RAG context will be skipped.")
            return

        try:
            logger.info("Initializing RAG embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self._available = True
            logger.info("RAG Service: embedding model loaded successfully.")

            # Ensure base directory exists
            os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

        except Exception as e:
            logger.warning(
                f"RAG Service: failed to load embedding model ({e}). "
                "RAG context will be skipped. Evaluation will continue without it."
            )

    @property
    def available(self) -> bool:
        return self._available

    def index_document(self, exam_id: int, content: str, filename: str) -> bool:
        """
        Split text content into chunks and add to/update the exam's vector store index.
        Returns False silently if RAG is unavailable.
        """
        if not self._available or not content:
            return False

        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            chunks = text_splitter.split_text(content)

            docs = [
                Document(page_content=chunk, metadata={"source": filename, "exam_id": exam_id})
                for chunk in chunks
            ]

            exam_index_path = os.path.join(VECTOR_STORE_PATH, f"exam_{exam_id}")

            if os.path.exists(os.path.join(exam_index_path, "index.faiss")):
                vectorstore = FAISS.load_local(
                    exam_index_path, self.embeddings, allow_dangerous_deserialization=True
                )
                vectorstore.add_documents(docs)
            else:
                vectorstore = FAISS.from_documents(docs, self.embeddings)

            vectorstore.save_local(exam_index_path)
            logger.info(f"RAG: Indexed {filename} for exam {exam_id} ({len(chunks)} chunks)")
            return True

        except Exception as e:
            logger.error(f"RAG: Indexing failed for {filename}: {e}", exc_info=True)
            return False

    def query_context(self, exam_id: int, query: str, k: int = 3) -> Optional[str]:
        """
        Retrieve relevant chunks from the exam's vector store.
        Returns None silently if RAG is unavailable or no index exists.
        """
        if not self._available:
            return None

        exam_index_path = os.path.join(VECTOR_STORE_PATH, f"exam_{exam_id}")

        if not os.path.exists(os.path.join(exam_index_path, "index.faiss")):
            return None

        try:
            vectorstore = FAISS.load_local(
                exam_index_path, self.embeddings, allow_dangerous_deserialization=True
            )
            results = vectorstore.similarity_search(query, k=k)

            if not results:
                return None

            context = "\n---\n".join([doc.page_content for doc in results])
            logger.info(f"RAG: Retrieved {len(results)} chunks for query: '{query[:50]}...'")
            return context

        except Exception as e:
            logger.error(f"RAG: Retrieval failed for exam {exam_id}: {e}")
            return None

    def delete_index(self, exam_id: int) -> bool:
        """Clear the vector index for a specific exam."""
        if not self._available:
            return False
        exam_index_path = os.path.join(VECTOR_STORE_PATH, f"exam_{exam_id}")
        if os.path.exists(exam_index_path):
            import shutil
            shutil.rmtree(exam_index_path)
            return True
        return False


# Singleton instance — safe even if model fails to load
rag_service = RAGService()
