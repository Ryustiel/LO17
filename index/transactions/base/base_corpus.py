
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
    