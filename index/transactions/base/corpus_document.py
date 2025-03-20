
from typing import (
    List,
    Dict,
    Tuple,
    TypedDict,
    Optional,
    Union,
    Literal,
    Self,
)
from abc import abstractmethod, ABC
from pydantic import BaseModel

import re


class CorpusDocument(BaseModel, ABC):
    """
    Represents a document that belongs in a corpus.
    Provide metadata about that document.
    """
    @property
    @abstractmethod
    def corps_fields(self) -> Tuple[str]:
        """
        The fields that make up the "corpus" of the document.
        """
        pass

    @property
    def corps(self) -> str:
        """
        A string representing the "semantic" component of the document.
        This will be used to represent the contents of the document and build an index.

        In the context of this project, it is the title and main body of the Document object, 
        but it could be something else.
        """
        # TODO (Maybe) : Add a cache to store the result of this method.
        return "\n".join([getattr(self, field) for field in self.corps_fields])
    
    def tokens(self) -> Dict[str, int]:
        """
        List all the words occurring in this document and the number of times they occurred.

        Returns:
            A dictionary of words and their counts.
        """
        spans = self.corps.split()
        words = ["".join(re.findall(r'\w+', s)).lower() for s in spans if re.search(r'\w', s)]
        return list(set(words))
