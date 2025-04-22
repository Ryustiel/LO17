
from typing import List, Dict, Any

from ..base.base_corpus import BaseCorpus

import pandas as pd
import math


class CorpusIndex(BaseCorpus):
    """
    A couple methods to compute metrics on a corpus of documents.
    """

    @property
    def inverted_index(self) -> Dict[str, List[Any]]:
        """
        Result: 
            Un dictionnaire avec tous les tokens du corpus 
            et la liste des id de documents dans lesquels il apparaît (mot, List[document_ids]).
        """
        tokens = {}
        for doc in self.documents:
            for token, count in doc.tokens.items():
                if token not in tokens:
                    tokens[token] = []
                tokens[token].append(doc.document_id)
        return tokens
