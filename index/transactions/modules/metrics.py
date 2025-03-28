
from typing import List

from ..base.base_corpus import BaseCorpus

import pandas as pd
import math


class CorpusMetrics(BaseCorpus):
    """
    A couple methods to compute metrics on a corpus of documents.
    """
    @property
    def token_by_doc(self) -> pd.DataFrame:
        """
        Result: 
            Une dataframe avec tous les tokens du corpus au format (mot, document_id).
        """
        rows = []
        for doc in self.documents:
            for token, count in doc.tokens.items():
                rows.append({'token': token, 'document_id': doc.document_id})
        
        return pd.DataFrame(rows, columns=['token', 'document_id'])
    

    @property
    def term_frequencies(self) -> pd.DataFrame:
        """
        Computes term frequencies (TF) for each document in the corpus.
        
        Returns:
            A DataFrame with columns ["document_id", "mot", "tf"].
        """
        if not self.documents:
            raise ValueError("The provided Corpus contains no documents.")

        tf_rows = []
        for doc in self.documents:
            for token, count in doc.tokens.items():
                tf_rows.append({"document_id": doc.document_id, "mot": token, "tf": count})
                
        return pd.DataFrame(tf_rows, columns=["document_id", "mot", "tf"])


    @property
    def tfidf(self) -> pd.DataFrame:
        """
        Computes TF-IDF scores for each term in each document.

        Internally this function:
        (a) compute self.tf to get the term frequencies,
        (b) computes the document frequency (DF) per term and then
            the inverse document frequency (IDF) as idf = log10(N / df)
        (c) merges the two to yield TF-IDF = tf * idf.

        Returns:
            A DataFrame with columns ["document_id", "mot", "tf_idf"].
        """
        tf_df = self.term_frequencies
        N = len(self.documents)
        if tf_df.empty or N == 0:
            return pd.DataFrame(columns=["document_id", "mot", "tf_idf"])

        # Compute DF (number of documents each token appears in)
        df_count = (
            tf_df.groupby("mot")["document_id"]
            .nunique()
            .reset_index(name="df")
        )
        # Compute IDF: if 0 < df < N then idf = log10(N / df), else 0.0.
        df_count["idf"] = df_count["df"].apply(
            lambda df_val: math.log10(N / df_val) if 0 < df_val < N else 0.0
        )
        # Merge TF and IDF to compute TF-IDF.
        tfidf_df = pd.merge(tf_df, df_count[["mot", "idf"]], on="mot", how="left")
        tfidf_df["tf_idf"] = tfidf_df["tf"] * tfidf_df["idf"]
        return tfidf_df[["document_id", "mot", "tf_idf"]]


    def anti_dict(self, idf_threshold: float = 0.1) -> pd.DataFrame:
        """
        Generates an anti-dictionary file containing words with IDF values
        less than or equal to the given threshold.

        This function computes the IDF values (using compute_tf) and then
        writes each candidate word to a file (one per line, with a tab and empty quotes).

        Args:
            idf_threshold: Only words with idf <= threshold are saved.

        Returns:
            A dataframe mapping words to empty strings.
        """
        tf_df = self.term_frequencies
        N = len(self.documents)
        if tf_df.empty or N == 0:
            idf_df = pd.DataFrame(columns=["mot", "idf"])
        else:
            df_count = (
                tf_df.groupby("mot")["document_id"]
                .nunique()
                .reset_index(name="df")
            )
            df_count["idf"] = df_count["df"].apply(
                lambda df_val: math.log10(N / df_val) if 0 < df_val < N else 0.0
            )
            idf_df = df_count[["mot", "idf"]]

        # Select candidate words with IDF <= threshold.
        anti_words = idf_df[idf_df["idf"] <= idf_threshold]["mot"]
        
        return anti_words # pd.DataFrame({"mot": anti_words, "remplacement": ""})
        