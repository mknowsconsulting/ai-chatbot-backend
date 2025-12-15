"""
Embeddings Service
Generate vector embeddings for FAQ search using sentence-transformers
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Generate embeddings for text using sentence-transformers
    Model: paraphrase-multilingual-MiniLM-L12-v2 (supports Indonesian & English)
    """
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.model = None
        self.dimension = 384  # MiniLM-L12 produces 384-dimensional vectors
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✅ Embedding model loaded (dimension: {self.dimension})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize vectors (recommended for cosine similarity)
            batch_size: Batch size for encoding
            
        Returns:
            Numpy array of embeddings
            
        Example:
            embedding = embeddings_service.encode("Berapa biaya kuliah?")
            # Returns: array of shape (384,)
            
            embeddings = embeddings_service.encode(["Text 1", "Text 2"])
            # Returns: array of shape (2, 384)
        """
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise
    
    def encode_single(self, text: str, normalize: bool = True) -> List[float]:
        """
        Generate embedding for single text (returns as list for Qdrant)
        
        Args:
            text: Input text
            normalize: Whether to normalize vector
            
        Returns:
            List of floats (embedding vector)
        """
        embedding = self.encode(text, normalize=normalize)
        return embedding[0].tolist()
    
    def encode_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of texts
            normalize: Whether to normalize vectors
            batch_size: Batch size
            
        Returns:
            List of embedding vectors (each as list of floats)
        """
        embeddings = self.encode(texts, normalize=normalize, batch_size=batch_size)
        return embeddings.tolist()
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


# ============================================
# Global Embeddings Service Instance
# ============================================

embeddings_service = EmbeddingsService()
