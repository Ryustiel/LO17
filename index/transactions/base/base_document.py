from functools import cached_property
from typing import (
    Any,
    List,
    Dict,
    Tuple,
)
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
        del self.corps
        del self.tokens
        del self.document_id
        del self.corps_fields
    
    @cached_property
    @abstractmethod
    def corps_fields(self) -> Tuple[str]:
        """
        The fields that make up the "corps" of the document.
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
    def corps(self) -> str:
        """
        A string representing the "semantic" component of the document.
        This will be used to represent the contents of the document and build an index.

        In the context of this project, it is the title and main body of the Document object, 
        but it could be something else.
        """
        # TODO (Maybe) : Add a cache to store the result of this method.
        return "\n".join([getattr(self, field, "") or "" for field in self.corps_fields])
    
    @cached_property
    def tokens(self) -> Dict[str, int]:
        """
        List all the words occurring in this document and the number of times they occurred.

        Returns:
            A dictionary of words and their counts.
        """
        word_counts = {}
        # Utilise \w+, trouve directement toutes les séquences alphanumériques
        for word in re.findall(r"\w+", self.corps):
            cleaned_lower = word.lower()  # Met en minuscule
            word_counts[cleaned_lower] = word_counts.get(cleaned_lower, 0) + 1
        return word_counts
