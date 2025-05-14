# index_builder.py
import os
import re
from collections import defaultdict
from typing import List, Dict, Callable, DefaultDict  # Set n'est pas utilisé ici
from datetime import datetime

# Importations depuis la structure de projet
from index.transactions.corpus import Corpus  # Remplacer CorpusClient par Corpus
from index.transactions.document import Document, Image
from data.backup.nlp_tools import TextNormalizerFunc  # Type de la fonction de normalisation

# Type alias pour la structure interne de l'index
# self.indexes = { 'index_nom': { term: { doc_id: frequency } } }
IndexDict = DefaultDict[str, DefaultDict[str, int]]


# Bonus: Méthode pour suggérer des améliorations (gardée telle quelle)
def suggest_improvements():
    print("\nSuggestions pour améliorer la qualité de l'indexation:")
    print(
        "- **Gestion des Mots Composés:** Utiliser des n-grammes (bi-grammes, tri-grammes) ou des techniques d'extraction de termes pour indexer des expressions comme 'intelligence artificielle'.")
    print(
        "- **Tokenisation Avancée:** Utiliser un tokenizer plus sophistiqué (comme celui de spaCy) qui gère mieux la ponctuation, les contractions, etc., au lieu de `re.findall(r'\w+')`.")
    print(
        "- **Filtrage Supplémentaire:** Après lemmatisation, certains mots très courts ou très fréquents (même s'ils ne sont pas dans l'anti-dictionnaire initial) pourraient être retirés si jugés peu informatifs.")
    print(
        "- **Index Positionnels:** Pour permettre des recherches d'expressions exactes ou de proximité, stocker la position (ou les positions) de chaque terme dans le document (`term -> doc_id -> [pos1, pos2, ...]`).")
    print(
        "- **Pondération TF-IDF dans l'Index:** Stocker le poids TF-IDF du terme dans le document au lieu (ou en plus) de la fréquence brute (TF). Nécessite un calcul préalable du TF-IDF sur les termes normalisés.")
    print(
        "- **Normalisation des Entités Nommées:** Détecter et normaliser les noms de personnes, lieux, organisations pour les indexer de manière cohérente.")
    print(
        "- **Gestion des Variantes/Synonymes:** Utiliser des thesaurus ou des embeddings de mots pour étendre les requêtes aux synonymes ou termes liés lors de la recherche (étape de recherche, pas d'indexation directe).")


class InvertedIndexBuilder:
    """
    Construit des fichiers d'index inversés à partir d'un objet Corpus
    et d'une fonction de normalisation de texte choisie.
    """

    def __init__(self, corpus_obj: Corpus, text_normalizer: TextNormalizerFunc, doc_id_field: str = 'fichier'):
        """
        Initialise le constructeur d'index.

        Args:
            corpus_obj: L'objet Corpus contenant la liste des documents.
            text_normalizer: La fonction à appliquer aux mots des champs texte (ex: get_spacy_lemmas).
            doc_id_field: L'attribut du document à utiliser comme ID (par défaut 'fichier').
        """
        self.corpus_obj = corpus_obj  # Changement de nom pour la clarté
        self.text_normalizer = text_normalizer
        self.doc_id_field = doc_id_field  # 'fichier' est correct via doc.document_id
        self.indexes: Dict[str, IndexDict] = {}

    def _get_doc_id(self, doc: Document) -> str:
        """Récupère l'ID du document de manière sécurisée."""
        # Utilise la propriété document_id de la classe Document, qui utilise self.fichier
        doc_id_val = doc.document_id

        if not doc_id_val:  # Devrait être géré par la logique de Document, mais double sécurité
            doc_id_val = f'doc_sans_id_{id(doc)}'  # Fallback très improbable

        # Échapper/remplacer caractères problématiques si l'ID peut en contenir (doc.fichier est un nom de fichier)
        # Les noms de fichiers sont généralement sûrs, mais on garde par prudence si la source de l'ID changeait.
        return str(doc_id_val).replace(' ', '_').replace(',', ';')

    def _add_to_index(self, index_name: str, term: str, doc_id: str):
        """Ajoute une occurrence d'un terme pour un document à un index spécifique."""
        if not term:  # Ignorer les termes vides (après normalisation ou strip)
            return

        # Initialise l'entrée pour l'index si elle n'existe pas
        if index_name not in self.indexes:
            self.indexes[index_name] = defaultdict(lambda: defaultdict(int))

        # Incrémente la fréquence du terme pour ce document
        self.indexes[index_name][term][doc_id] += 1

    def build_indexes(self, fields_to_index: List[str]):  # Default enlevé pour forcer la spécification dans main.py
        """
        Construit les index inversés pour les champs spécifiés.

        Args:
            fields_to_index: Liste des noms d'attributs des Documents à indexer.
        """
        print(f"Début de la construction des index pour les champs: {fields_to_index}")
        self.indexes = {}  # Réinitialiser pour une nouvelle construction

        # Champs textuels qui subiront la normalisation (tokenisation, lemmatisation/stemming)
        text_fields_to_normalize = {'titre', 'texte', 'titre_texte', 'images_legende'}
        # Champs qui seront mis en minuscule mais pas normalisés par text_normalizer
        # Utile pour les facettes comme 'rubrique', 'numero' si l'on veut une recherche insensible à la casse.
        fields_to_lower_case_only = {'rubrique', 'numero'}  # À AJUSTER SELON LES BESOINS

        combined_titre_texte_needed = 'titre_texte' in fields_to_index

        if not self.corpus_obj.documents:
            print("Avertissement: Aucun document dans l'objet Corpus. Impossible de construire les index.")
            return

        total_docs = len(self.corpus_obj.documents)
        for i, doc in enumerate(self.corpus_obj.documents):
            doc_id = self._get_doc_id(doc)

            # Préparer le contenu combiné titre+texte si nécessaire
            combined_content = ""
            if combined_titre_texte_needed:
                titre = getattr(doc, 'titre', "") or ""  # Robustesse si None
                texte = getattr(doc, 'texte', "") or ""
                combined_content = f"{titre}\n{texte}"

            for field_name_from_config in fields_to_index:
                current_index_target_name = field_name_from_config  # Nom de l'index (ex: 'date', 'rubrique')
                value_to_process = None

                if field_name_from_config == 'titre_texte':
                    value_to_process = combined_content
                    # Le nom de l'index sera automatiquement suffixé par _normalized car dans text_fields_to_normalize
                elif field_name_from_config == 'images_url':
                    images: List[Image] = getattr(doc, 'images', [])
                    for img in images:
                        if img.url:
                            # Les URLs ne sont typiquement pas normalisées ni mises en minuscule.
                            # Elles sont indexées telles quelles.
                            term_url = img.url.strip()
                            if term_url:
                                self._add_to_index('images_url', term_url, doc_id)
                    continue  # Traitement spécial pour images_url terminé
                elif field_name_from_config == 'images_legende':
                    images: List[Image] = getattr(doc, 'images', [])
                    # Concaténer toutes les légendes en un seul bloc de texte
                    value_to_process = "\n".join([img.legende for img in images if img.legende and img.legende.strip()])
                    # Sera normalisé car dans text_fields_to_normalize
                else:
                    value_to_process = getattr(doc, field_name_from_config, None)

                if value_to_process is None or (isinstance(value_to_process, str) and not value_to_process.strip()):
                    continue  # Passer au champ suivant si la valeur est None ou une chaîne vide/blanche

                # --- Traitement de la valeur et ajout à l'index ---
                if isinstance(value_to_process, datetime):  # Cas du champ 'date'
                    # Indexer la date au format YYYY-MM-DD pour tri et recherche par plage
                    term_date = value_to_process.strftime('%Y-%m-%d')
                    self._add_to_index(current_index_target_name, term_date, doc_id)

                elif isinstance(value_to_process, str):
                    if field_name_from_config in text_fields_to_normalize:
                        # Tokenisation, mise en minuscule, et normalisation (lemme/stem)
                        final_index_name = f"{field_name_from_config}_normalized"
                        # Tokenisation simple, peut être améliorée (ex: tokenizer spaCy complet)
                        tokens = re.findall(r'\w+', value_to_process.lower())
                        for token in tokens:
                            normalized_term = self.text_normalizer(token)
                            if normalized_term:  # S'assurer que le normaliseur n'a pas retourné vide
                                self._add_to_index(final_index_name, normalized_term, doc_id)
                    elif field_name_from_config in fields_to_lower_case_only:
                        # Pour les champs comme 'rubrique', 'numero' : strip et minuscule
                        term_facet = value_to_process.strip().lower()
                        if term_facet:
                            self._add_to_index(current_index_target_name, term_facet, doc_id)
                    else:
                        # Pour les autres champs string non normalisés et non listés pour lowercase only
                        # (ex: si on voulait garder la casse pour 'numero' ou un autre champ spécifique)
                        # Actuellement, tous les champs string non dans text_fields_to_normalize
                        # et pas dans fields_to_lower_case_only seraient indexés après strip.
                        # On va supposer que si ce n'est pas textuel normalisé, et pas explicitement en lowercase,
                        # on le prend tel quel (après strip).
                        # MAIS, pour la cohérence, il est souvent préférable de mettre en minuscule.
                        # Si on veut 'numero' tel quel: enlever 'numero' de fields_to_lower_case_only.
                        # Pour l'instant, on a 'rubrique' et 'numero' qui passent par fields_to_lower_case_only.
                        # S'il y avait d'autres champs string non couverts, ils atterriraient ici :
                        term_other_str = value_to_process.strip()
                        if term_other_str:
                            self._add_to_index(current_index_target_name, term_other_str, doc_id)

                elif isinstance(value_to_process, (int, float)):
                    # Convertir les nombres en chaînes pour l'indexation
                    self._add_to_index(current_index_target_name, str(value_to_process), doc_id)

                # elif isinstance(value_to_process, list): Gérer si un champ peut être une liste de strings simples

            if (i + 1) % 10 == 0 or (i + 1) == total_docs:
                print(f"  ... {i + 1}/{total_docs} documents traités pour l'indexation.")

        print("Construction des index terminée.")
        if not self.indexes:
            print("Avertissement: Aucun index n'a été généré. Vérifiez la configuration des champs et les documents.")

    def save_indexes(self, output_dir: str = "index_files"):
        """
        Sauvegarde chaque index construit dans un fichier séparé au format TSV.
        Format: term<TAB>doc_id1:freq1 doc_id2:freq2 ...

        Args:
            output_dir: Le répertoire où sauvegarder les fichiers d'index.
        """
        if not self.indexes:
            print("Aucun index n'a été construit, rien à sauvegarder.")
            return

        os.makedirs(output_dir, exist_ok=True)  # S'assurer que le répertoire de sortie existe
        print(f"Sauvegarde des fichiers d'index dans le répertoire: {output_dir}")

        for index_name, index_data in self.indexes.items():
            # Le nom du fichier est directement basé sur index_name (ex: 'rubrique', 'titre_normalized')
            filename = os.path.join(output_dir, f"index_{index_name}.tsv")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # Trier les termes pour un fichier plus lisible et pour des tests reproductibles
                    for term in sorted(index_data.keys()):
                        postings = index_data[term]  # C'est un dict {doc_id: freq}
                        # Trier les doc_ids pour la cohérence dans les fichiers de sortie
                        postings_str_parts = [f"{doc_id}:{freq}" for doc_id, freq in sorted(postings.items())]
                        postings_str = " ".join(postings_str_parts)
                        f.write(f"{term}\t{postings_str}\n")
                print(f"  - Index '{index_name}' sauvegardé dans {filename}")
            except IOError as e:
                print(f"Erreur lors de l'écriture du fichier d'index '{filename}': {e}")

        print("Sauvegarde des index terminée.")