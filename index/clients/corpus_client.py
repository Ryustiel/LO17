
from typing import (
    List,
    Dict,
    Optional,
    Self,
)
import pandas as pd
from .base.process_client import FileProcessClient
from ..transactions import CorpusDocument

class CorpusClient:
    """
    Provide metadata about a corpus of documents.
    """
    documents: List[CorpusDocument]

    def __init__(self, documents: List[CorpusDocument]):
        self.documents = documents

    @classmethod
    def from_folder (cls, proces_client: FileProcessClient, folder_path: str, limit: Optional[int] = None) -> Self:
        """
        Load a corpus from a folder containing documents.
        """
        documents = proces_client.process_folder(folder_path, limit=limit)
        return cls(documents)
        
    def segmente(self) -> pd.DataFrame:
        """
        Retrieve a list of individual tokens from each document of the corpus (identified by filename), 
        associated with the document it was from.
        
        Returns:
            A dataframe with columns (token, filename) that can be converted to a tsv string.
            Tokens appear as many times as they appear in the documents.
        """
        from ..transactions import Document
        if not isinstance(self.documents, list) or not isinstance(self.documents[0], Document):
            raise ValueError("The documents attribute must be a list of Document objects for this method to work.")
        
        tokens = []
        docs: List[Document] = self.documents
        for doc in docs:
            for token in doc.tokens():
                tokens.append((token, doc.fichier))

        return pd.DataFrame(tokens, columns=["token", "filename"])
