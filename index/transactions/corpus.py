import math
import re
from typing import (
    List,
    Dict,
    Optional,
    Self,
    TYPE_CHECKING
)
from xml.dom import minidom
import xml.etree.ElementTree as ET
import pandas as pd
if TYPE_CHECKING:
    from ..clients import FileProcessClient

from .document import Document
from .base.xml_base_model import XMLBaseModel
from .base.base_corpus import BaseCorpus
from .modules.post_processing import CorpusPostProcessing
from .modules.metrics import CorpusMetrics
from .modules.nlp import CorpusNLP


class Corpus(
    XMLBaseModel, 
    CorpusPostProcessing, 
    CorpusMetrics, 
    CorpusNLP,
    BaseCorpus,  # Base class (bridges all the modules)
):
    """
    Représente et gère une collection de documents (BaseDocument).
    Permet le chargement, la segmentation basique, la modification en mémoire
    et l'exportation XML du corpus.
    """
    documents: List[Document]  # Utilise le type de base abstrait
    
    @classmethod
    def from_folder(cls, 
        process_client: "FileProcessClient", 
        folder_path: str,
        limit: Optional[int] = None
    ) -> Self:
        """
        Charge un corpus depuis un dossier en utilisant un FileProcessClient.
        """
        return cls(documents = process_client.process_folder(folder_path=folder_path, limit=limit))
