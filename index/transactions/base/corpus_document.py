
from typing import (
    List,
    Tuple,
    Optional,
    Union,
    Literal,
    Self,
)
from pydantic import BaseModel, Field, PrivateAttr


class CorpusDocument(BaseModel):
    """
    Represents a document that belongs in a corpus.
    Provide metadata about that document.
    """
    

    @property
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
        return "\n".join([getattr(self, field) for field in self.corps_fields])

    def 
