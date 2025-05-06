
from typing import List, Optional

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
        for _, row in substitutions.iterrows():
            mot = row[0]
            remplacement = row[1]
            if isinstance(mot, str) and isinstance(remplacement, str):
                pattern = r'\b' + re.escape(mot) + r'\b'
                texte = re.sub(pattern, remplacement, texte, flags=re.IGNORECASE)
        return texte
    
    def apply_substitutions(self, attributes: List[str], substitutions: pandas.DataFrame) -> None:
        """
        Applique des substitutions sur les attributs spécifiés de chaque document.

        Parameters:
            attributes: Liste des noms d'attributs à traiter (formuler "attr1.attr2" pour les attributs de type List[Other])
            substitutions: DataFrame contenant les mots à remplacer et leurs remplacements
        """
        print("Application des substitutions sur les attributs spécifiés...")
        for doc in self.documents:
            for attr in attributes:
                if "." in attr:
                    attr1, attr2 = attr.split(".")
                    if hasattr(doc, attr1) and isinstance(getattr(doc, attr1), list):
                        for item in getattr(doc, attr1):
                            if hasattr(item, attr2) and isinstance(getattr(item, attr2), str):
                                texte = getattr(item, attr2)
                                texte_modifie = self.substitution(texte, substitutions)
                                setattr(item, attr2, texte_modifie)
                            else:
                                print(f"Avertissement: Attribut '{attr2}' n'est pas une string dans le document {doc.document_id}.")
                    else:
                        print(f"Avertissement: Attribut '{attr1}' n'est pas une liste dans le document {doc.document_id}.")
                else:
                    if hasattr(doc, attr) and isinstance(getattr(doc, attr), str):
                        texte = getattr(doc, attr)
                        texte_modifie = self.substitution(texte, substitutions)
                        setattr(doc, attr, texte_modifie)
                    else:
                        print(f"Avertissement: Attribut '{attr}' n'est pas une string dans le document {doc.document_id}.")
    
    def apply_standardization(self, attributes: List[str]) -> None:
        """
        Applique strip et lowercase sur les attributs spécifiés de chaque document.
        
        Parameters:
            attributes: Liste des noms d'attributs à traiter (formuler "attr1.attr2" pour les attributs de type List[Other])
        """
        print("Application de la normalisation sur les attributs spécifiés...")
        for doc in self.documents:
            for attr in attributes:
                if "." in attr:
                    attr1, attr2 = attr.split(".")
                    if hasattr(doc, attr1) and isinstance(getattr(doc, attr1), list):
                        for item in getattr(doc, attr1):
                            if hasattr(item, attr2) and isinstance(getattr(item, attr2), str):
                                texte = getattr(item, attr2)
                                texte_modifie = texte.strip().lower()
                                setattr(item, attr2, texte_modifie)
                            else:
                                print(f"Avertissement: Attribut '{attr2}' n'est pas une string dans le document {doc.document_id}.")
                    else:
                        print(f"Avertissement: Attribut '{attr1}' n'est pas une liste dans le document {doc.document_id}.")
                else:
                    if hasattr(doc, attr) and isinstance(getattr(doc, attr), str):
                        texte = getattr(doc, attr)
                        texte_modifie = texte.strip().lower()
                        setattr(doc, attr, texte_modifie)
                    else:
                        print(f"Avertissement: Attribut '{attr}' n'est pas une string dans le document {doc.document_id}.")
    