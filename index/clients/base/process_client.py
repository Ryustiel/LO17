
from typing import (
    List,
    Dict,
    Optional,
    TypeVar,
    Generic,
)
from abc import abstractmethod
from pydantic import BaseModel

import os
import glob

DocumentModel = TypeVar("DocumentModel", bound=BaseModel)


class FileProcessClient(Generic[DocumentModel]):
    """
    Processes data from various sources
    and build instances of Document models.
    """

    @abstractmethod
    def process(self, file: str, path: str) -> DocumentModel:
        """
        Extracts information from a file.
        """
        pass

    def process_local_file(self, path: str) -> DocumentModel:
        """
        Process the document at the specified path.
        """
        with open(path, 'r', encoding='utf-8') as file:
            return self.process(file.read(), path)

    def process_folder(self, folder_path: str, limit: Optional[int] = None) -> Dict[str, DocumentModel]:
        """
        Process all documents from the specified folder.

        Parameters:
            folder_path (str):
                The path to the folder which contains the files to proces.
            limit (int, Optional):
                If set, will not process more than "limit" files from the folder.
        
        Returns:
            dict: A dictionary mapping source paths to Document objects.
                - Keys (str): The document's source path.
                - Values (DocumentModel): The document data object.
        """
        paths = glob.glob(os.path.join(folder_path, "*.htm"))

        docs: List[DocumentModel] = []
        for i, path in enumerate(paths):

            if limit and i >= limit:
                break
            else:
                docs.append(
                    self.process_local_file(path)
                )
                
        return docs
