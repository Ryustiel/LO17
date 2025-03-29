
from typing import List
from ..base.base_corpus import BaseCorpus
from abc import abstractmethod
import pandas as pd
import re


class CorpusPostProcessing(BaseCorpus):
    """
    A couple methods to post process a corpus of documents.
    """
    
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
        # Dans Corpus.apply_substitutions, on précharge déjà, c'est mieux.
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
            # Gérer l'erreur ou laisser remonter comme dans Corpus
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

    def apply_substitutions(self, anti_dict_path: str):
        """
        Applique les substitutions de l'anti-dictionnaire directement aux
        attributs des objets Document en mémoire, basé sur doc.corps_fields.

        Args:
            anti_dict_path: Chemin vers le fichier anti-dictionnaire (mot\t"").
        """
        print(f"Application des substitutions depuis {anti_dict_path} sur {len(self.documents)} documents...")
        modification_count = 0
        # Pré-charger les substitutions pour l'efficacité
        substitutions = {}
        try:
            with open(anti_dict_path, 'r', encoding='utf-8') as f:
                for ligne in f:
                    if ligne.strip():
                        parts = ligne.strip().split('\t')
                        if len(parts) >= 2:
                            mot = parts[0]
                            remplacement = parts[1].strip('"')
                            substitutions[mot] = remplacement
        except FileNotFoundError:
            print(
                f"Erreur critique: Fichier anti-dictionnaire '{anti_dict_path}' non trouvé. Aucune substitution appliquée.")
            return  # Arrêter si le fichier n'existe pas

        if not substitutions:
            print("Avertissement: Le fichier anti-dictionnaire est vide ou n'a pas pu être lu correctement.")
            # Continuer quand même pour invalider le cache si nécessaire ? Ou retourner ?
            # Pour l'instant, on continue mais on prévient.

        for i, doc in enumerate(self.documents):
            doc_modified = False
            # Itérer sur les champs définis comme faisant partie du 'corps' sémantique
            for field_name in doc.corps_fields:
                if hasattr(doc, field_name):
                    original_text = getattr(doc, field_name)
                    # Vérifier que c'est bien une chaîne et qu'elle n'est pas vide
                    if isinstance(original_text, str) and original_text:
                        # Utiliser la méthode statique pour appliquer les substitutions
                        modified_text = self.substituer_mots(original_text, anti_dict_path)

                        # Mettre à jour l'attribut de l'objet si le texte a changé
                        if modified_text != original_text:
                            setattr(doc, field_name, modified_text)
                            doc_modified = True

            if doc_modified:
                modification_count += 1
                doc.clear_cache()

            # Affichage de la progression
            if (i + 1) % 100 == 0 or i == len(self.documents) - 1:
                print(f"  ... {i + 1}/{len(self.documents)} documents traités.")

        print(f"Substitutions appliquées. {modification_count} documents ont été modifiés.")
        if modification_count > 0:
            print("Le cache des documents a été correctement invalidé pour les documents modifiés.")
            