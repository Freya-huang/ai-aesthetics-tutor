import os
import logging
import math
from collections import Counter
from typing import List, Union, Dict
import numpy as np

logger = logging.getLogger(__name__)


class BaseEmbedder:
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError


class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.model = None
        self._dimension = None
        self._load_model()

    def _load_model(self):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading sentence transformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded successfully. Embedding dimension: {self._dimension}")

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings

    @property
    def dimension(self) -> int:
        return self._dimension


def _char_ngrams(text: str, n_range=(2, 4)) -> List[str]:
    text = text.lower()
    ngrams = []
    for n in range(n_range[0], n_range[1] + 1):
        for i in range(len(text) - n + 1):
            ngrams.append(text[i:i + n])
    return ngrams


class TfidfEmbedder(BaseEmbedder):
    def __init__(self, max_features: int = 1000):
        self.max_features = max_features
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = None
        self._dimension = max_features
        self._fitted = False

    def fit(self, texts: List[str]):
        doc_freq = Counter()
        doc_count = len(texts)

        for text in texts:
            ngrams = set(_char_ngrams(text))
            doc_freq.update(ngrams)

        sorted_ngrams = sorted(doc_freq.items(), key=lambda x: (-x[1], x[0]))
        top_ngrams = sorted_ngrams[:self.max_features]

        self.vocabulary = {ngram: idx for idx, (ngram, _) in enumerate(top_ngrams)}
        self._dimension = len(self.vocabulary)

        self.idf = np.ones(self._dimension, dtype=np.float32)
        for ngram, idx in self.vocabulary.items():
            df = doc_freq.get(ngram, 0)
            self.idf[idx] = math.log((doc_count + 1) / (df + 1)) + 1

        self._fitted = True
        logger.info(f"TF-IDF vectorizer fitted. Vocabulary size: {self._dimension}")

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        if not self._fitted:
            self.fit(texts)

        embeddings = np.zeros((len(texts), self._dimension), dtype=np.float32)

        for text_idx, text in enumerate(texts):
            ngrams = _char_ngrams(text)
            tf = Counter(ngrams)

            for ngram, count in tf.items():
                if ngram in self.vocabulary:
                    idx = self.vocabulary[ngram]
                    embeddings[text_idx, idx] = count * self.idf[idx]

            norm = np.linalg.norm(embeddings[text_idx])
            if norm > 0:
                embeddings[text_idx] /= norm

        return embeddings

    @property
    def dimension(self) -> int:
        return self._dimension


def _is_offline_or_mock() -> bool:
    return os.getenv("MOCK_MODE", "").lower() == "true" or not os.getenv("LLM_API_KEY", "")


def get_embedder(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> BaseEmbedder:
    if _is_offline_or_mock():
        logger.info("Mock/offline mode detected, using TF-IDF embedder directly")
        return TfidfEmbedder()
    try:
        return SentenceTransformerEmbedder(model_name)
    except Exception as e:
        logger.warning(f"Failed to load sentence transformer model ({e}), falling back to TF-IDF embedder")
        return TfidfEmbedder()
