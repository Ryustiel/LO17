
from typing import Self, List

import math, pandas


class InvertedIndex(dict):  # Dict[str, List[str]]  token: List[document_ids]
    """
    An inverted index is a mapping of tokens (words) to the ids of the documents they appear in.
    """
    
    def to_dataframe(self) -> pandas.DataFrame:
        """
        Converts the inverted index to a DataFrame. (with padding)

        Returns:
            A DataFrame with columns ["mot", "id_1", "id_2", ..., "id\_//max id//"].
        """
        max_len = max(len(v) for v in self.values()) if self else 0
        columns = ["token"] + [f"id_{i+1}" for i in range(max_len)]
        rows = []
        for token, doc_ids in self.items():
            row = [token] + doc_ids + [math.nan] * (max_len - len(doc_ids))
            rows.append(row)
                
        return pandas.DataFrame(rows, columns=columns)
    
    @classmethod
    def from_dataframe(cls, df: pandas.DataFrame) -> Self:
        """
        Converts a DataFrame to an inverted index.

        Parameters:
            df: A DataFrame with columns ["mot", "id_1", "id_2", ..., "id\_//max id//"].
        """
        index = cls()
        for _, row in df.iterrows():
            token = row[0]
            doc_ids = [str(id) for id in row[1:] if not pandas.isna(id)]
            index[token] = doc_ids
            
        return index
    
    def find_docs(self, tokens: List[str]) -> List[str]:
        """
        Finds the documents that contain all the specified tokens.

        Parameters:
            tokens: A list of tokens to search for.

        Returns:
            A list of document ids that contain all the specified tokens.
        """
        if not tokens:
            return []
        
        # Get the document ids for the first token
        doc_ids = set(self.get(tokens[0], []))
        
        # Intersect with the document ids for each subsequent token
        for token in tokens[1:]:
            doc_ids.intersection_update(self.get(token, []))
            
        return list(doc_ids)
