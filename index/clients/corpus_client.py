
from typing import (
    List,
    Dict,
    Optional,
    Self,
)
from abc import abstractmethod
from pydantic import BaseModel
from .base.process_client import FileProcessClient
from ..transactions import CorpusDocument

class CorpusClient:
    """
    Provide metadata about a corpus of documents.
    """
    corpus: List[CorpusDocument]

    def __init__(self, corpus: List[CorpusDocument]):
        self.corpus = corpus

    @classmethod
    def from_folder (cls, proces_client: FileProcessClient, folder_path: str) -> Self:
        """
        Load a corpus from a folder containing documents.
        """
        corpus = proces_client.process_folder(folder_path)
        return cls(corpus)
        
    def segmente(self) -> str:
        """
        Retrieve a list of individual tokens from each document of the corpus (identified by filename), 
        associated with the document it was from.
        
        Returns:
            A tab separated csv string with the columns: token, filename.
            Tokens appear as many times as they appear in the documents.
        """
        from ..transactions import Document
        if not isinstance(self.corpus, List[Document]):
            raise ValueError("The corpus must be a list of Document objects for this method to work.")
        return "\n".join([f"{token}\t{doc.titre}" for doc in self.corpus for token in doc.all_words()])
