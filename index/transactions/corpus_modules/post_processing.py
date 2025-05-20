
from typing import List, Optional, Callable

import re, pandas

from ..base.base_corpus import BaseCorpus
from ..base.base_document import BaseDocument
from abc import abstractmethod


class CorpusPostProcessing(BaseCorpus):
    """
    A couple methods to post process a corpus of documents.
    """
    
    @staticmethod
    def substitution(texte: str, substitutions: pandas.DataFrame) -> str:
        """
        Applique des substitutions simples sur un texte donné.

        Parameters:
            texte: Le texte à traiter
            substitutions: Un DataFrame contenant les mots à remplacer et leurs remplacements

        Returns:
            Le texte avec les substitutions appliquées.
        """
        mapping = {
            mot.lower(): remplacement
            for mot, remplacement in substitutions.itertuples(index=False)
        }
        pattern = re.compile(
            r'\b(' + '|'.join(map(re.escape, mapping.keys())) + r')\b',
            flags=re.IGNORECASE
        )
        def _replacer(match):
            # match.group(0) est le mot trouvé (dans la casse originale)
            key = match.group(0).lower()
            return mapping.get(key, match.group(0))
        
        return pattern.sub(_replacer, texte)
    
    @staticmethod
    def standardize(texte: str) -> str:
        """
        Applique une normalisation simple sur un texte donné.
        Retire les espaces en début et fin de chaîne, met le texte en minuscules 
        et retire la ponctuation et les apostrophes.

        Parameters:
            texte: Le texte à traiter

        Returns:
            Le texte normalisé.
        """
        texte = texte.strip().lower()
        texte = re.sub(r"[^\w\s]", "", texte)
        return re.sub(r"'", " ", texte)
    
    def apply_substitutions(self, attributes: List[str], substitutions: pandas.DataFrame) -> None:
        """
        Applique des substitutions sur les attributs spécifiés de chaque document.

        Parameters:
            attributes: Liste des noms d'attributs à traiter (formuler "attr1.attr2" pour les attributs de type List[Other])
            substitutions: DataFrame contenant les mots à remplacer et leurs remplacements
        """
        print("Application des substitutions sur les attributs spécifiés...")
        
        mapping = {
            mot.lower(): remplacement
            for mot, remplacement in substitutions.itertuples(index=False)
        }
        pattern = re.compile(
            r'\b(' + '|'.join(map(re.escape, mapping.keys())) + r')\b',
            flags=re.IGNORECASE
        )
        def _replacer(match):
            # match.group(0) est le mot trouvé (dans la casse originale)
            key = match.group(0).lower()
            return mapping.get(key, match.group(0))
        
        # Applique les substitutions sur chaque document
        
        for doc in self.documents:
            for attr in attributes:
                if "." in attr:
                    attr1, attr2 = attr.split(".")
                    if hasattr(doc, attr1) and isinstance(getattr(doc, attr1), list):
                        for item in getattr(doc, attr1):
                            if hasattr(item, attr2) and isinstance(getattr(item, attr2), str):
                                texte = getattr(item, attr2)
                                setattr(item, attr2, pattern.sub(_replacer, texte))
                            else:
                                print(f"Avertissement: Attribut '{attr2}' n'est pas une string dans le document {doc.document_id}.")
                    else:
                        print(f"Avertissement: Attribut '{attr1}' n'est pas une liste dans le document {doc.document_id}.")
                else:
                    if hasattr(doc, attr) and isinstance(getattr(doc, attr), str):
                        texte = getattr(doc, attr)
                        setattr(doc, attr, pattern.sub(_replacer, texte))
                    else:
                        print(f"Avertissement: Attribut '{attr}' n'est pas une string dans le document {doc.document_id}.")
    
        self.clear_cache()
    
    def apply_filter(self, attributes: List[str], filter: Callable[[str], str]) -> None:
        """
        Applique la fonction "filter" sur les attributs spécifiés de chaque document.
        
        Parameters:
            attributes: Liste des noms d'attributs à traiter (formuler "attr1.attr2" pour les attributs de type List[Other])
        """
        print("Application du filtre sur les attributs spécifiés...")
        for doc in self.documents:
            for attr in attributes:
                if "." in attr:
                    attr1, attr2 = attr.split(".")
                    if hasattr(doc, attr1) and isinstance(getattr(doc, attr1), list):
                        for item in getattr(doc, attr1):
                            if hasattr(item, attr2) and isinstance(getattr(item, attr2), str):
                                texte = getattr(item, attr2)
                                setattr(item, attr2, filter(texte))
                            else:
                                print(f"Avertissement: Attribut '{attr2}' n'est pas une string dans le document {doc.document_id}.")
                    else:
                        print(f"Avertissement: Attribut '{attr1}' n'est pas une liste dans le document {doc.document_id}.")
                else:
                    if hasattr(doc, attr) and isinstance(getattr(doc, attr), str):
                        texte = getattr(doc, attr)
                        setattr(doc, attr, filter(texte))
                    else:
                        print(f"Avertissement: Attribut '{attr}' n'est pas une string dans le document {doc.document_id}.")
    
        self.clear_cache()
    