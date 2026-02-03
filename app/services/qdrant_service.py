"""
Qdrant Service
Manages vector database operations for FAQ storage and retrieval
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from typing import List, Dict, Any, Optional
import logging
import uuid

from app.core.config import settings
from app.services.embeddings_service import embeddings_service

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Qdrant Vector Database Service
    Handles FAQ storage, search, and management
    """
    
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.client = None
        self.dimension = embeddings_service.get_dimension()
        
        # Collection names
        self.collection_faq_id = settings.QDRANT_COLLECTION_FAQ_ID
        self.collection_faq_en = settings.QDRANT_COLLECTION_FAQ_EN
        
        self._connect()
    
    def _connect(self):
        """Connect to Qdrant"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"✅ Qdrant connected at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Qdrant: {e}")
            self.client = None
    
    def create_collection(self, collection_name: str):
        """
        Create a new collection for FAQs
        
        Args:
            collection_name: Name of collection
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name in collection_names:
                logger.info(f"Collection '{collection_name}' already exists")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"✅ Collection '{collection_name}' created")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def initialize_collections(self):
        """Initialize all required collections"""
        logger.info("Initializing Qdrant collections...")
        self.create_collection(self.collection_faq_id)
        self.create_collection(self.collection_faq_en)
        logger.info("✅ All Qdrant collections initialized")
    
    def add_faq(
        self,
        collection_name: str,
        question: str,
        answer: str,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a single FAQ to collection
        
        Args:
            collection_name: Collection to add to
            question: FAQ question
            answer: FAQ answer
            category: Optional category
            metadata: Optional additional metadata
            
        Returns:
            Point ID (UUID)
        """
        try:
            # Generate embedding for question
            embedding = embeddings_service.encode_single(question)
            
            # Generate unique ID
            point_id = str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                "question": question,
                "answer": answer,
                "category": category or "general"
            }
            
            if metadata:
                payload.update(metadata)
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"Added FAQ to {collection_name}: {question[:50]}...")
            return point_id
            
        except Exception as e:
            logger.error(f"Failed to add FAQ: {e}")
            raise
    
    def add_faqs_batch(
        self,
        collection_name: str,
        faqs: List[Dict[str, str]]
    ) -> List[str]:
        """
        Add multiple FAQs in batch
        
        Args:
            collection_name: Collection to add to
            faqs: List of FAQ dictionaries with 'question', 'answer', optional 'category'
            
        Returns:
            List of point IDs
            
        Example:
            faqs = [
                {"question": "Q1?", "answer": "A1", "category": "admission"},
                {"question": "Q2?", "answer": "A2", "category": "academic"}
            ]
            ids = qdrant_service.add_faqs_batch("faq_public_id", faqs)
        """
        try:
            # Extract questions
            questions = [faq["question"] for faq in faqs]
            
            # Generate embeddings for all questions
            embeddings = embeddings_service.encode_batch(questions)
            
            # Create points
            points = []
            point_ids = []
            
            for i, faq in enumerate(faqs):
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)
                
                payload = {
                    "question": faq["question"],
                    "answer": faq["answer"],
                    "category": faq.get("category", "general")
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=payload
                )
                points.append(point)
            
            # Batch upload
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"✅ Added {len(faqs)} FAQs to {collection_name}")
            return point_ids
            
        except Exception as e:
            logger.error(f"Failed to add FAQs batch: {e}")
            raise
    
    def search_faq(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar FAQs
        
        Args:
            collection_name: Collection to search
            query: User's question
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            category: Optional filter by category
            
        Returns:
            List of FAQ results with scores
            
        Example:
            results = qdrant_service.search_faq(
                "faq_public_id",
                "Berapa biaya kuliah?",
                limit=3
            )
        """
        try:
            # Check if Qdrant is available
            if not self.client:
                logger.warning("Qdrant not available, returning empty results")
                return []
            # Generate embedding for query
            query_embedding = embeddings_service.encode_single(query)
            
            # Prepare filter
            query_filter = None
            if category:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=category)
                        )
                    ]
                )
            
            # Search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "question": hit.payload.get("question"),
                    "answer": hit.payload.get("answer"),
                    "category": hit.payload.get("category")
                })
            
            logger.info(f"Found {len(results)} FAQs for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"FAQ search error: {e}")
            return []
    
    def delete_faq(self, collection_name: str, point_id: str):
        """Delete a FAQ by ID"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id]
            )
            logger.info(f"Deleted FAQ: {point_id}")
        except Exception as e:
            logger.error(f"Failed to delete FAQ: {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def clear_collection(self, collection_name: str):
        """Clear all points from collection"""
        try:
            self.client.delete_collection(collection_name)
            self.create_collection(collection_name)
            logger.info(f"✅ Collection '{collection_name}' cleared")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise


# ============================================
# Global Qdrant Service Instance
# ============================================

qdrant_service = QdrantService()
