"""
Objects that represent well defined data containers
and regroup operations that are related to them.
"""

from .base.xml_base_model import XMLBaseModel
from .base.inverted_index import InvertedIndex
from .base.token_metrics import TokenMetrics
from .scripts.nlp import spacy_lemmas, spacy_lemmatize, snowball_stem, snowball_stems
from .scripts.correction import correct_tokens

from .document import Document, Image
from .corpus import Corpus
from .query import Query
