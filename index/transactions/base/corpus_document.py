from functools import cached_property
from typing import (
    List,
    Dict,
    Tuple,
    TypedDict,
    Optional,
    Union,
    Literal,
    Self,
)
from abc import abstractmethod, ABC
from pydantic import BaseModel

import re

class CorpusDocument(BaseModel, ABC):
    """
    Represents a document that belongs in a corpus.
    Provide metadata about that document.
    """
    @property
    @abstractmethod
    def corps_fields(self) -> Tuple[str]:
        """
        The fields that make up the "corpus" of the document.
        """
        pass

    @cached_property
    def corps(self) -> str:
        """
        A string representing the "semantic" component of the document.
        This will be used to represent the contents of the document and build an index.

        In the context of this project, it is the title and main body of the Document object, 
        but it could be something else.
        """
        # TODO (Maybe) : Add a cache to store the result of this method.
        return "\n".join([getattr(self, field, "") or "" for field in self.corps_fields])
    
    def tokens(self) -> Dict[str, int]:
        """
        List all the words occurring in this document and the number of times they occurred.

        Returns:
            A dictionary of words and their counts.
        """
        word_counts = {}
        # Utilise \w+, trouve directement toutes les séquences alphanumériques
        for word in re.findall(r"\w+", self.corps):
            cleaned_lower = word.lower()  # Met en minuscule
            word_counts[cleaned_lower] = word_counts.get(cleaned_lower, 0) + 1
        return word_counts

    @staticmethod
    def substituer_mots(texte: str, fichier_substitution: str) -> str:
        """
        Élimine ou remplace des mots dans un texte selon un fichier de substitution,
        en utilisant re.sub pour une meilleure gestion des limites de mots et des espaces.

        Args:
            texte: Le texte à traiter
            fichier_substitution: Chemin vers un fichier de substitution
                                (format: mot[tab]remplacement)

        Returns:
            Le texte avec les substitutions appliquées et les espaces nettoyés.
        """
        # Charger le dictionnaire de substitution (une seule fois idéalement,
        # mais ici on le recharge à chaque appel pour rester simple)
        # Dans CorpusClient.apply_substitutions, on précharge déjà, c'est mieux.
        # On pourrait passer le dictionnaire préchargé en argument ici.
        substitutions = {}
        mots_a_supprimer = []  # Mots à remplacer par ""
        try:
            with open(fichier_substitution, 'r', encoding='utf-8') as f:
                for ligne in f:
                    if ligne.strip():
                        parts = ligne.strip().split('\t')
                        if len(parts) >= 2:
                            mot = parts[0].strip()  # Assurer pas d'espaces autour
                            remplacement = parts[1].strip('"')  # Enlever les guillemets éventuels
                            if mot:  # Ignorer lignes vides ou mot vide
                                substitutions[mot] = remplacement
                                if remplacement == "":
                                    mots_a_supprimer.append(mot)
        except FileNotFoundError:
            # Gérer l'erreur ou laisser remonter comme dans CorpusClient
            print(f"Avertissement: Fichier substitution {fichier_substitution} non trouvé dans substituer_mots.")
            return texte  # Retourner le texte original si le fichier n'existe pas

        texte_modifie = texte

        # 1. Appliquer les remplacements spécifiques (non vides)
        for mot, remplacement in substitutions.items():
            if remplacement != "":
                # Utilise \b pour les limites de mots, ignore la casse
                pattern = r'\b' + re.escape(mot) + r'\b'
                try:
                    texte_modifie = re.sub(pattern, remplacement, texte_modifie, flags=re.IGNORECASE)
                except re.error as e:
                    print(f"Erreur regex pour le mot '{mot}': {e}")

        # 2. Appliquer les suppressions (remplacement par "")
        if mots_a_supprimer:
            # Crée un seul pattern pour tous les mots à supprimer
            # Utilise \b pour les limites de mots, ignore la casse
            pattern_suppression = r'\b(' + '|'.join(re.escape(m) for m in mots_a_supprimer) + r')\b'
            try:
                texte_modifie = re.sub(pattern_suppression, '', texte_modifie, flags=re.IGNORECASE)
            except re.error as e:
                print(f"Erreur regex pour la suppression groupée: {e}")

        # 3. Supprimer les apostrophes
        texte_modifie = texte_modifie.replace("'", " ")

        # 4. Nettoyer les espaces multiples et les espaces en début/fin
        texte_modifie = re.sub(r'\s+', ' ', texte_modifie).strip()

        return texte_modifie
