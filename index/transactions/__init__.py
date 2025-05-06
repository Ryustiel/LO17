"""
Objects that represent well defined data containers
and regroup operations that are related to them.
"""

from .base.base_document import BaseDocument
from .base.xml_base_model import XMLBaseModel
from .scripts.inverted_index import InvertedIndex
from .scripts.token_metrics import TokenMetrics
from .scripts.nlp import spacy_lemmas, spacy_lemmatize, snowball_stem, snowball_stems

from .document import Document, Image
from .corpus import Corpus
