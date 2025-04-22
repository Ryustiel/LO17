
from typing import List

from ..base.base_corpus import BaseCorpus
import pandas as pd


class CorpusNLP(BaseCorpus):
    """
    A couple methods to apply NLP processing on a corpus of documents.
    """
    
    @property
    def spacy_lemmas(self) -> pd.DataFrame:
        """
        Create a DataFrame mapping each unique word in the input text to its spaCy lemma.
        
        Args:
            text (str): The input text.
        
        Returns:
            pd.DataFrame: DataFrame with columns ['word', 'stem'] where 'stem' is the spaCy lemma.
        """
        from ...nlp import get_spacy
        nlp = get_spacy("fr_core_news_sm")
        words = {w for w in self.tokens.keys() if w.isalpha()}
        mapping = {word: doc[0].lemma_ for word, doc in zip(words, nlp.pipe(words)) if word.isalpha()}
        return pd.DataFrame(sorted(mapping.items()), columns=["word", "stem"])

    @property
    def snowball_stems(self) -> pd.DataFrame:
        """
        Create a DataFrame mapping each unique word in the input text to its Snowball stem.
        
        Args:
            text (str): The input text.
        
        Returns:
            pd.DataFrame: DataFrame with columns ['word', 'stem'] where 'stem' is the Snowball stem.
        """
        from nltk.stem import SnowballStemmer
        stemmer = SnowballStemmer("french")
        words = {w for w in self.tokens.keys() if w.isalpha()}
        mapping = {w: stemmer.stem(w) for w in words}
        return pd.DataFrame(sorted(mapping.items()), columns=["word", "stem"])
    
    def spacy_lemmatize(self, text: str) -> List[str]:
        """
        Lemmatize the input text using spaCy.
        
        Args:
            text (str): The input text.
        
        Returns:
            List[str]: List of lemmatized words.
        """
        from ...nlp import get_spacy
        nlp = get_spacy("fr_core_news_sm")
        doc = nlp(text)
        return [token.lemma_ for token in doc if token.is_alpha]
    
    def snowball_stem(self, text: str) -> List[str]:
        """
        Stem the input text using Snowball.
        
        Args:
            text (str): The input text.
        
        Returns:
            List[str]: List of stemmed words.
        """
        from nltk.stem import SnowballStemmer
        stemmer = SnowballStemmer("french")
        return [stemmer.stem(w) for w in text.split() if w.isalpha()]
    