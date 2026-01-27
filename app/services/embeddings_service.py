"""
Embeddings Service
Generate vector embeddings using simple fallback (for Railway deployment)
"""

from typing import List, Union
import logging
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Simple embedding service using hash-based vectors
    NOTE: This is a fallback for deployment. Use proper embeddings in production.
    """
    
    def __init__(self):
        self.dimension = 384
        logger.info(f"✅ Embeddings service initialized (dimension: {self.dimension})")
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """Generate embeddings using deterministic hash-based vectors"""
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = []
            for text in texts:
                hash_val = hash(text.lower())
                np.random.seed(abs(hash_val) % (2**32))
                vec = np.random.randn(self.dimension)
                if normalize:
                    vec = vec / np.linalg.norm(vec)
                embeddings.append(vec)
            
            return np.array(embeddings)
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise
    
    def encode_single(self, text: str, normalize: bool = True) -> List[float]:
        """Generate embedding for single text"""
        embedding = self.encode(text, normalize=normalize)
        return embedding[0].tolist()
    
    def encode_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        embeddings = self.encode(texts, normalize=normalize, batch_size=batch_size)
        return embeddings.tolist()
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity"""
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


embeddings_service = EmbeddingsService()
