
from typing import (
    List,
    Dict,
)
from abc import abstractmethod, ABC
from .base_document import BaseDocument

class BaseCorpus(ABC):
    """
    Represents a set of documents that we want to analyze together.
    """
    documents: List[BaseDocument]
    
    def clear_cache(self):
        """
        Clear all the cached properties of the corpus.
        """
        for doc in self.documents:
            doc.clear_cache()
            
    @property
    def tokens(self) -> Dict[str, int]:
        """
        List all the words occurring in this corpus and the number of times they occurred.

        Returns:
            A dictionary of words and their counts.
        """
        word_counts = {}
        for doc in self.documents:
            for word, count in doc.tokens.items():
                word_counts[word] = word_counts.get(word, 0) + count
        return word_counts
    