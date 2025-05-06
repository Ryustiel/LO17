from functools import cached_property
from typing import Any, Dict, Tuple, Callable
from abc import abstractmethod, ABC
from pydantic import BaseModel

import re

class BaseDocument(BaseModel, ABC):
    """
    Represents a document that belongs in a corpus.
    Provide metadata about that document.
    """
    def clear_cache(self):
        """
        Reset all the cached properties of the document.
        """
        for attr in ("tokens", "document_id", "read_zones"):
            if hasattr(self, attr):
                delattr(self, attr)
    
    @cached_property
    @abstractmethod
    def zones(self) -> Dict[str, Callable[["BaseDocument"], str]]:
        """
        The fields that make up the "zones" of the document.
        """
        pass
    
    @cached_property
    @abstractmethod
    def document_id(self) -> Any:
        """
        A unique identifier for the document.
        """
        raise NotImplemented
    
    @cached_property
    @abstractmethod
    def tokens(self) -> Dict[str, Dict[str, int]]:
        """
        List all the words occurring in this document's fields and the number of times they occurred.
        Returns:
            A dictionary of field keys mapped to a dictionary of words and their counts.
        """
        pass

    @cached_property
    def read_zones(self) -> Dict[str, str]:
        """
        Returns the fields of the document as a dictionary.
        """
        return {key: func(self) for key, func in self.zones.items()}
