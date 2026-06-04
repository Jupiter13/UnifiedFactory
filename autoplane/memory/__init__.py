"""Memory management for the AutoPlane Design Agent.

This module handles short-term, long-term, and persistent memory:
- Short-Term: DesignState (in-memory)
- Long-Term: FAISS vector store for similarity search
- Persistent: PostgreSQL for metadata storage
"""

import json
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

import faiss
import numpy as np
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from autoplane.models.state import DesignState

logger = logging.getLogger(__name__)

Base = declarative_base()


class DesignRecord(Base):
    """SQLAlchemy model for storing design metadata."""

    __tablename__ = "design_records"

    job_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    payload_kg = Column(Float, nullable=False)
    material = Column(String, nullable=True)
    engine = Column(String, nullable=True)
    wing_span = Column(Float, nullable=True)
    wing_area = Column(Float, nullable=True)
    fuselage_length = Column(Float, nullable=True)
    tail_area = Column(Float, nullable=True)
    range_km = Column(Float, nullable=True)
    cruise_speed_kts = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    state_json = Column(Text, nullable=True)  # Full state for detailed retrieval


class VectorStore:
    """FAISS vector store for similarity search."""

    def __init__(self, dimension: int = 128):
        """Initialize the vector store.

        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.embeddings: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []
        logger.info(f"VectorStore initialized with dimension {dimension}")

    def add(self, embedding: np.ndarray, metadata: Dict[str, Any]) -> None:
        """Add an embedding to the store.

        Args:
            embedding: Feature vector
            metadata: Associated metadata
        """
        if embedding.shape[0] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embedding.shape[0]} != {self.dimension}"
            )

        embedding = embedding.reshape(1, -1).astype(np.float32)
        self.index.add(embedding)
        self.embeddings.append(embedding.flatten())
        self.metadata.append(metadata)
        logger.debug(f"Added embedding, total: {self.index.ntotal}")

    def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings.

        Args:
            query_embedding: Query vector
            k: Number of results to return

        Returns:
            List of (distance, metadata) tuples
        """
        if self.index.ntotal == 0:
            return []

        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                results.append({
                    "distance": float(dist),
                    "metadata": self.metadata[idx],
                })

        return results

    def save(self, path: str) -> None:
        """Save the index to disk.

        Args:
            path: Path to save the index
        """
        faiss.write_index(self.index, f"{path}.index")
        with open(f"{path}_metadata.json", "w") as f:
            json.dump(self.metadata, f)
        logger.info(f"Saved index to {path}")

    def load(self, path: str) -> None:
        """Load the index from disk.

        Args:
            path: Path to load the index from
        """
        self.index = faiss.read_index(f"{path}.index")
        with open(f"{path}_metadata.json", "r") as f:
            self.metadata = json.load(f)
        self.embeddings = [np.array(m.get("embedding", [])) for m in self.metadata]
        logger.info(f"Loaded index from {path}")


class DesignMemory:
    """Memory manager combining vector store and PostgreSQL."""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize the memory manager.

        Args:
            db_url: PostgreSQL connection URL (uses SQLite if None)
        """
        if db_url is None:
            db_url = "sqlite:///./autoplane.db"

        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        self.vector_store = VectorStore(dimension=128)
        logger.info("DesignMemory initialized")

    def _state_to_embedding(self, state: DesignState) -> np.ndarray:
        """Convert DesignState to an embedding vector.

        Args:
            state: DesignState to embed

        Returns:
            Feature vector
        """
        features = [
            state.payload_kg / 10000,  # Normalized payload
            state.wing_span / 100 if state.wing_span else 0,
            state.wing_area / 1000 if state.wing_area else 0,
            state.fuselage_length / 100 if state.fuselage_length else 0,
            state.tail_area / 100 if state.tail_area else 0,
            state.performance.range_km / 10000 if state.performance else 0,
            state.performance.cruise_speed_kts / 1000 if state.performance else 0,
            state.cost.total_cost / 1000000 if state.cost else 0,
            1.0 if state.material == "Carbon Fiber" else 0.0,
            1.0 if state.material == "Titanium" else 0.0,
            1.0 if state.material == "Al-6061" else 0.0,
            1.0 if state.engine == "Turbofan-1" else 0.0,
            1.0 if state.engine == "Turbofan-2" else 0.0,
            1.0 if state.engine == "Propeller-1" else 0.0,
        ]

        # Pad to dimension size
        while len(features) < 128:
            features.append(0.0)

        return np.array(features[:128], dtype=np.float32)

    def store_design(self, state: DesignState, user_id: Optional[str] = None) -> str:
        """Store a design in both vector store and database.

        Args:
            state: DesignState to store
            user_id: Optional user identifier

        Returns:
            Job ID
        """
        job_id = state.job_id or str(uuid.uuid4())
        state.job_id = job_id

        # Store in PostgreSQL
        session = self.Session()
        try:
            record = DesignRecord(
                job_id=job_id,
                user_id=user_id,
                payload_kg=state.payload_kg,
                material=state.material,
                engine=state.engine,
                wing_span=state.wing_span,
                wing_area=state.wing_area,
                fuselage_length=state.fuselage_length,
                tail_area=state.tail_area,
                range_km=state.performance.range_km if state.performance else None,
                cruise_speed_kts=state.performance.cruise_speed_kts if state.performance else None,
                total_cost=state.cost.total_cost if state.cost else None,
                status=state.status,
                state_json=state.model_dump_json(),
            )
            session.merge(record)
            session.commit()
            logger.debug(f"Stored design record: {job_id}")
        finally:
            session.close()

        # Store in vector store
        embedding = self._state_to_embedding(state)
        metadata = {
            "job_id": job_id,
            "payload_kg": state.payload_kg,
            "material": state.material,
            "engine": state.engine,
            "wing_span": state.wing_span,
            "wing_area": state.wing_area,
            "range_km": state.performance.range_km if state.performance else None,
        }
        self.vector_store.add(embedding, metadata)

        return job_id

    def get_design(self, job_id: str) -> Optional[DesignState]:
        """Retrieve a design by job ID.

        Args:
            job_id: Job identifier

        Returns:
            DesignState or None if not found
        """
        session = self.Session()
        try:
            record = session.query(DesignRecord).filter_by(job_id=job_id).first()
            if record and record.state_json:
                state_dict = json.loads(record.state_json)
                return DesignState(**state_dict)
            return None
        finally:
            session.close()

    def find_similar(
        self, state: DesignState, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar designs.

        Args:
            state: Reference design state
            k: Number of results

        Returns:
            List of similar designs with metadata
        """
        embedding = self._state_to_embedding(state)
        return self.vector_store.search(embedding, k)

    def list_designs(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> List[DesignState]:
        """List stored designs.

        Args:
            user_id: Optional filter by user
            limit: Maximum number of results

        Returns:
            List of DesignStates
        """
        session = self.Session()
        try:
            query = session.query(DesignRecord)
            if user_id:
                query = query.filter_by(user_id=user_id)
            records = query.order_by(DesignRecord.created_at.desc()).limit(limit).all()

            designs = []
            for record in records:
                if record.state_json:
                    state_dict = json.loads(record.state_json)
                    designs.append(DesignState(**state_dict))
                else:
                    designs.append(DesignState(
                        job_id=record.job_id,
                        payload_kg=record.payload_kg,
                        material=record.material,
                        engine=record.engine,
                        wing_span=record.wing_span,
                        wing_area=record.wing_area,
                        fuselage_length=record.fuselage_length,
                        tail_area=record.tail_area,
                        status=record.status,
                    ))

            return designs
        finally:
            session.close()

    def delete_design(self, job_id: str) -> bool:
        """Delete a design.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        session = self.Session()
        try:
            record = session.query(DesignRecord).filter_by(job_id=job_id).first()
            if record:
                session.delete(record)
                session.commit()
                logger.debug(f"Deleted design: {job_id}")
                return True
            return False
        finally:
            session.close()


# Global memory instance
_memory_instance = None


def get_memory(db_url: Optional[str] = None) -> DesignMemory:
    """Get the global memory instance.

    Args:
        db_url: Optional database URL

    Returns:
        DesignMemory singleton
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = DesignMemory(db_url)
    return _memory_instance


def reset_memory() -> None:
    """Reset the global memory instance (for testing)."""
    global _memory_instance
    _memory_instance = None