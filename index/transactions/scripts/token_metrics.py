
from typing import List, Dict

import math, pandas


class TokenMetrics(dict):  # Dict[str, Dict[str, int]]  : { document_id: {token: count} }
    """
    A mapping of document ids to a dictionary of tokens and their counts.
    This class is used to compute term frequencies (TF) and TF-IDF scores for a corpus of documents.
    """

    @property
    def term_frequencies(self) -> pandas.DataFrame:
        """
        Computes term frequencies (TF) for each document in the corpus.
        
        Returns:
            A DataFrame with columns ["document_id", "mot", "tf"].
        """
        tf_rows = []
        for doc_id, tokens in self.items():
            for token, count in tokens.items():
                tf_rows.append({"document_id": doc_id, "mot": token, "tf": count})
                
        return pandas.DataFrame(tf_rows, columns=["document_id", "mot", "tf"])

    @property
    def tfidf(self) -> pandas.DataFrame:
        """
        Computes TF-IDF scores for each term in each document.

        Internally this function:
        (a) compute self.tf to get the term frequencies,
        (b) computes the document frequency (DF) for each term and then
            the inverse document frequency (IDF) as idf = log10(N / df)
        (c) merges the two to yield TF-IDF = tf * idf.

        Returns:
            A DataFrame with columns ["document_id", "mot", "tf_idf"].
        """
        tf_df = self.term_frequencies
        N = len(self.keys())
        if tf_df.empty or N == 0:
            return pandas.DataFrame(columns=["document_id", "mot", "tf_idf"])

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
        tfidf_df = pandas.merge(tf_df, df_count[["mot", "idf"]], on="mot", how="left")
        tfidf_df["tf_idf"] = tfidf_df["tf"] * tfidf_df["idf"]
        return tfidf_df[["document_id", "mot", "tf_idf"]]

    def get_irrelevant_terms(self, idf_threshold: float = 0.1) -> List[str]:
        """
        Select irrelevant terms based on their IDF score.

        Parameters:
            idf_threshold: Only words with idf <= threshold are retained.

        Returns:
            A list of irrelevant terms.
        """
        tf_df = self.term_frequencies
        N = len(self.keys())
        if tf_df.empty or N == 0:
            idf_df = pandas.DataFrame(columns=["mot", "idf"])
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
        irrelevant_words = idf_df[idf_df["idf"] <= idf_threshold]["mot"]
        
        return irrelevant_words
        
    def build_anti_dict(self, idf_threshold: float = 0.1) -> pandas.DataFrame:
        """
        Select irrelevant terms based on their IDF score.

        Parameters:
            idf_threshold: Only words with idf <= threshold are retained.

        Returns:
            A dataframe mapping words to empty strings.
        """
        irrelevant_terms = self.get_irrelevant_terms(idf_threshold)
        anti_dict = pandas.DataFrame({"mot": [term for term in irrelevant_terms], "remplacement": [""] * len(irrelevant_terms)})
        return anti_dict
