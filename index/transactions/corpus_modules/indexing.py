
from typing import List, Dict, Optional

import pandas

from ..base.base_corpus import BaseCorpus
from ..base.inverted_index import InvertedIndex
from ..base.token_metrics import TokenMetrics


class CorpusIndex(BaseCorpus):
    """
    A couple methods to compute metrics and indexes on a corpus of documents.
    """

    def tokens(self, zones: Optional[List[str]] = None) -> Dict[str, int]:
        """
        List all the words occurring in this corpus and the number of times they occurred.

        Parameters:
            zones (List[str], None): 
                Une liste de noms de zones à prendre en compte dans le résultat.
                Si None, toutes les zones sont prises en compte.
        Returns:
            A dictionary of words and their counts.
        """
        word_counts = {}
        for doc in self.documents:
            for zone, tokens in doc.tokens.items():
                
                if zones is None or zone in zones:
                    
                    for word, count in tokens.items():
                        word_counts[word] = word_counts.get(word, 0) + count
                        
        return word_counts
    
    def token_index(self, zones: Optional[List[str]] = None) -> TokenMetrics:  # Dict[str, Dict[str, int]]
        """
        Generate a mapping of document ids to a dictionary of tokens and their counts.
        
        Parameters:
            zones (List[str], None): 
                Une liste de noms de zones à prendre en compte dans le résultat.
                Si None, toutes les zones sont prises en compte.
        Returns:
            A dictionary where each key is a document id and the value is a dictionary of tokens and their counts.
        """
        index = TokenMetrics()
        for doc in self.documents:
            for zone, tokens in doc.tokens.items():
                    
                    if zones is None or zone in zones:
                        
                        for token, count in tokens.items():
                            if doc.document_id not in index.keys():
                                index[doc.document_id] = {}
                            index[doc.document_id][token] = index[doc.document_id].get(token, 0) + count
                            
        return index

    def inverted_token_index_flattened(self, zones: Optional[List[str]] = None) -> pandas.DataFrame:
        """
        Parameters:
            zones (List[str], None): 
                Une liste de noms de zones à prendre en compte dans le résultat.
                Si None, toutes les zones sont prises en compte.
        Returns:
            Une dataframe avec tous les tokens du corpus au format (mot, document_id).
        """
        rows = []
        for doc in self.documents:
            for zone, tokens in doc.tokens.items():
                
                if zones is None or zone in zones:
                    
                    for token, _ in tokens.items():
                        rows.append({'token': token, 'document_id': doc.document_id})
        
        return pandas.DataFrame(rows, columns=['token', 'document_id'])
    
    def inverted_token_index(self, zones: Optional[List[str]] = None) -> InvertedIndex:
        """
        Parameters:
            zones (List[str], None): 
                Une liste de noms de zones à prendre en compte dans le résultat.
                Si None, toutes les zones sont prises en compte.
        Returns:
            Une dataframe avec tous les tokens du corpus au format (mot, space separated document_ids).
        """
        index: Dict[str, List[str]] = InvertedIndex()
        for doc in self.documents:
            for zone, tokens in doc.tokens.items():
                
                if zones is None or zone in zones:
                    
                    for token, _ in tokens.items():
                        if token not in index.keys():
                            index[token] = []
                        index[token].append(doc.document_id)
        
        return index
    