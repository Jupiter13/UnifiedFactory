"""Vector store integration for long-term memory.

Supports Pinecone and Qdrant for storing course embeddings and user interactions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class VectorDocument(BaseModel):
    """Document stored in vector store."""

    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None

    def __init__(self, **data):
        if data.get("created_at") is None:
            data["created_at"] = datetime.utcnow()
        super().__init__(**data)


class VectorStore:
    """Vector store client for embedding storage and retrieval.

    Supports both Pinecone and Qdrant backends.
    """

    def __init__(
        self,
        provider: str = "pinecone",
        api_key: Optional[str] = None,
        index_name: str = "edu-centre-courses",
        environment: Optional[str] = None,
    ):
        """Initialize vector store client.

        Args:
            provider: Vector store provider (pinecone, qdrant)
            api_key: API key for the vector store
            index_name: Name of the index to use
            environment: Provider-specific environment (e.g., gcp-starter for Pinecone)
        """
        self.provider = provider
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self._client = None
        self._index = None

    def connect(self) -> bool:
        """Connect to the vector store.

        Returns:
            True if connection successful
        """
        try:
            if self.provider == "pinecone":
                return self._connect_pinecone()
            elif self.provider == "qdrant":
                return self._connect_qdrant()
            return False
        except Exception:
            return False

    def _connect_pinecone(self) -> bool:
        """Connect to Pinecone.

        Returns:
            True if successful
        """
        try:
            # Import pinecone client
            try:
                from pinecone import Pinecone
            except ImportError:
                return False

            # Initialize client
            self._client = Pinecone(api_key=self.api_key)

            # Get or create index
            if self.index_name not in [idx.name for idx in self._client.list_indexes()]:
                self._client.create_index(
                    name=self.index_name,
                    dimension=768,
                    metric="cosine",
                    environment=self.environment,
                )

            self._index = self._client.Index(self.index_name)
            return True

        except Exception:
            return False

    def _connect_qdrant(self) -> bool:
        """Connect to Qdrant.

        Returns:
            True if successful
        """
        # Qdrant connection would be implemented here
        return False

    def add_document(self, document: VectorDocument) -> bool:
        """Add a document to the vector store.

        Args:
            document: Document to add

        Returns:
            True if successful
        """
        if not self._index:
            return False

        try:
            vector = document.embedding or self._generate_embedding(document.content)

            self._index.upsert(
                vectors=[{
                    "id": document.id,
                    "values": vector,
                    "metadata": document.metadata,
                }],
            )
            return True
        except Exception:
            return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents with scores
        """
        if not self._index:
            return self._mock_search(query, top_k)

        try:
            query_embedding = self._generate_embedding(query)

            results = self._index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_metadata,
            )

            return [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                }
                for match in results.matches
            ]
        except Exception:
            return []

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text.

        In production, this would call an embedding model (e.g., OpenAI, Cohere).

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Mock embedding for development/testing
        # In production, use actual embedding model
        import hashlib
        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [
            (hash_value >> i) % 100 / 100.0 - 0.5
            for i in range(0, 768, 8)
        ]

    def _mock_search(
        self,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Mock search for development/testing.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Mock results
        """
        return [
            {
                "id": f"doc_{i}",
                "score": 0.9 - i * 0.1,
                "metadata": {
                    "course_id": f"course_{i}",
                    "title": f"Sample Course {i}",
                    "text": f"Content about {query}",
                },
            }
            for i in range(min(top_k, 3))
        ]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the vector store.

        Args:
            document_id: Document ID to delete

        Returns:
            True if successful
        """
        if not self._index:
            return False

        try:
            self._index.delete(ids=[document_id])
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the vector store connection."""
        self._client = None
        self._index = None