
from typing import Self, Dict, List
from abc import ABC, abstractmethod
import pydantic

from ..base.base_document import BaseDocument
from ..base.inverted_index import InvertedIndex


class BaseQuery(pydantic.BaseModel, ABC):
    """
    Une requête de recherche.
    """
    
    @classmethod
    @abstractmethod
    def build(cls, query: str) -> Self:
        """
        Crée une requête à partir d'une chaîne de caractères.
        
        Parameters:
            query (str): La chaîne de caractères à traiter.
        
        Returns:
            BaseQuery: Une instance de la requête construite.
        """
        pass
    
    @abstractmethod
    def search(self, documents: Dict[str, BaseDocument], index: Dict[str, InvertedIndex]) -> List[BaseDocument]:
        """
        Cherche des documents à partir de la requête.
        
        Parameters:
            documents (Dict[str, BaseDocument]): Un dictionnaire de documents à chercher, indexé par leur identifiant unique.
            index (Dict[str, InvertedIndex]): Un index inversé "zone: index" pour la recherche.
        
        Returns:
            List[BaseDocument]: Une liste de documents correspondant à la requête.
        """
        pass
        