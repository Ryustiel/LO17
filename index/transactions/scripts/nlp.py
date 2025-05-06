
from typing import List

import pandas

def spacy_lemmatize(text: str) -> List[str]:
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
    
def snowball_stem(text: str) -> List[str]:
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

def spacy_lemmas(tokens: List[str]) -> pandas.DataFrame:
    """
    Create a DataFrame mapping each unique word in the input text to its spaCy lemma.
    
    Parameters:
        tokens (str): The input tokens.
    
    Returns:
        pandas.DataFrame: DataFrame with columns ['word', 'stem'] where 'stem' is the spaCy lemma.
    """
    from ...nlp import get_spacy
    nlp = get_spacy("fr_core_news_sm")
    words = {w for w in tokens if w.isalpha()}
    mapping = {word: doc[0].lemma_ for word, doc in zip(words, nlp.pipe(words)) if word.isalpha()}
    return pandas.DataFrame(sorted(mapping.items()), columns=["word", "stem"])

def snowball_stems(tokens: List[str]) -> pandas.DataFrame:
    """
    Create a DataFrame mapping each unique word in the input text to its Snowball stem.
    
    Parameters:
        tokens (str): The input tokens.
    
    Returns:
        pandas.DataFrame: DataFrame with columns ['word', 'stem'] where 'stem' is the Snowball stem.
    """
    from nltk.stem import SnowballStemmer
    stemmer = SnowballStemmer("french")
    words = {w for w in tokens if w.isalpha()}
    mapping = {w: stemmer.stem(w) for w in words}
    return pandas.DataFrame(sorted(mapping.items()), columns=["word", "stem"])
