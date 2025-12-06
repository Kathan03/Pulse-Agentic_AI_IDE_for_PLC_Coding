"""
RAG (Retrieval-Augmented Generation) Engine for Pulse IDE.

Uses ChromaDB for vector storage and semantic search over the codebase.
Enables agents to "read" and understand the project structure and content.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

from src.core.config import Config


class ChromaDBRAG:
    """
    RAG engine using ChromaDB for semantic search over the codebase.

    Handles codebase ingestion, chunking, and semantic search queries.
    """

    # File extensions to process
    SUPPORTED_EXTENSIONS = {".py", ".md", ".txt", ".st"}

    # Directories to ignore
    IGNORE_DIRS = {".git", "__pycache__", "venv", "node_modules", ".venv", "env"}

    # Maximum chunk size (characters)
    MAX_CHUNK_SIZE = 2000

    def __init__(self, chroma_db_path: Optional[Path] = None):
        """
        Initialize the ChromaDB RAG engine.

        Args:
            chroma_db_path: Path to ChromaDB storage. Defaults to Config.CHROMA_DB_PATH.
        """
        self.chroma_db_path = chroma_db_path or Config.CHROMA_DB_PATH

        # Ensure directory exists
        self.chroma_db_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="pulse_codebase",
            metadata={"description": "Pulse IDE codebase for RAG"}
        )

    def _should_process_file(self, file_path: Path) -> bool:
        """
        Check if a file should be processed for ingestion.

        Args:
            file_path: Path to the file.

        Returns:
            bool: True if file should be processed, False otherwise.
        """
        # Check extension
        if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
            return False

        # Check if any parent directory is in ignore list
        for part in file_path.parts:
            if part in self.IGNORE_DIRS:
                return False

        return True

    def _chunk_content(self, content: str, file_path: str) -> List[Dict]:
        """
        Chunk file content for ingestion.

        For MVP, treats whole file as one chunk if < MAX_CHUNK_SIZE,
        otherwise splits by lines.

        Args:
            content: File content to chunk.
            file_path: Path to the file (for metadata).

        Returns:
            List[Dict]: List of chunks with metadata.
        """
        chunks = []

        if len(content) <= self.MAX_CHUNK_SIZE:
            # Treat whole file as one chunk
            chunks.append({
                "content": content,
                "metadata": {
                    "path": file_path,
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            })
        else:
            # Split by lines
            lines = content.split("\n")
            current_chunk = []
            current_size = 0
            chunk_index = 0

            for line in lines:
                line_size = len(line) + 1  # +1 for newline

                if current_size + line_size > self.MAX_CHUNK_SIZE and current_chunk:
                    # Save current chunk
                    chunks.append({
                        "content": "\n".join(current_chunk),
                        "metadata": {
                            "path": file_path,
                            "chunk_index": chunk_index,
                        }
                    })
                    current_chunk = []
                    current_size = 0
                    chunk_index += 1

                current_chunk.append(line)
                current_size += line_size

            # Add last chunk
            if current_chunk:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "metadata": {
                        "path": file_path,
                        "chunk_index": chunk_index,
                    }
                })

            # Update total_chunks in metadata
            total_chunks = len(chunks)
            for chunk in chunks:
                chunk["metadata"]["total_chunks"] = total_chunks

        return chunks

    def ingest_codebase(self, root_path: str | Path) -> Dict[str, int]:
        """
        Ingest a codebase into the ChromaDB collection.

        Walks through the directory tree, processes supported files,
        chunks content, and upserts into the vector store.

        Args:
            root_path: Root directory of the codebase.

        Returns:
            Dict[str, int]: Statistics about ingestion (files_processed, chunks_created).
        """
        root_path = Path(root_path)
        files_processed = 0
        chunks_created = 0

        documents = []
        metadatas = []
        ids = []

        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue

            if not self._should_process_file(file_path):
                continue

            try:
                # Read file content
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Chunk content
                chunks = self._chunk_content(content, str(file_path.relative_to(root_path)))

                # Prepare for ChromaDB
                for chunk in chunks:
                    chunk_id = f"{file_path.relative_to(root_path)}::{chunk['metadata']['chunk_index']}"
                    documents.append(chunk["content"])
                    metadatas.append(chunk["metadata"])
                    ids.append(chunk_id)
                    chunks_created += 1

                files_processed += 1

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        # Upsert into ChromaDB (batch operation)
        if documents:
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

        return {
            "files_processed": files_processed,
            "chunks_created": chunks_created
        }

    def search_codebase(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search the codebase using semantic similarity.

        Args:
            query: Search query (natural language or code snippet).
            n_results: Number of results to return. Defaults to 5.

        Returns:
            List[Dict]: Search results with document content and metadata.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Format results
        formatted_results = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })

        return formatted_results

    def clear_collection(self) -> None:
        """
        Clear all documents from the collection.

        Useful for re-ingestion or testing.
        """
        self.client.delete_collection(name="pulse_codebase")
        self.collection = self.client.get_or_create_collection(
            name="pulse_codebase",
            metadata={"description": "Pulse IDE codebase for RAG"}
        )

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the current collection.

        Returns:
            Dict: Collection statistics.
        """
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection.name,
            "path": str(self.chroma_db_path)
        }


# Singleton instance for easy access
_rag_instance: Optional[ChromaDBRAG] = None


def get_rag() -> ChromaDBRAG:
    """
    Get the singleton ChromaDBRAG instance.

    Returns:
        ChromaDBRAG: Singleton RAG engine instance.
    """
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = ChromaDBRAG()
    return _rag_instance
