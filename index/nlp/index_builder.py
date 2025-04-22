# index_builder.py
import os
import re
from collections import defaultdict
from typing import List, Dict, Callable, DefaultDict, Set
from datetime import datetime


# Importations depuis la structure de projet
from index.clients.corpus_client import CorpusClient
from index.transactions.document import Document, Image
from index.nlp.nlp_tools import TextNormalizerFunc # Type de la fonction de normalisation

# Type alias pour la structure interne de l'index
# index = { term: { doc_id: frequency } }
IndexDict = DefaultDict[str, DefaultDict[str, int]]


# Bonus: Méthode pour suggérer des améliorations
def suggest_improvements():
    print("\nSuggestions pour améliorer la qualité de l'indexation:")
    print("- **Gestion des Mots Composés:** Utiliser des n-grammes (bi-grammes, tri-grammes) ou des techniques d'extraction de termes pour indexer des expressions comme 'intelligence artificielle'.")
    print("- **Tokenisation Avancée:** Utiliser un tokenizer plus sophistiqué (comme celui de spaCy) qui gère mieux la ponctuation, les contractions, etc., au lieu de `re.findall(r'\w+')`.")
    print("- **Filtrage Supplémentaire:** Après lemmatisation, certains mots très courts ou très fréquents (même s'ils ne sont pas dans l'anti-dictionnaire initial) pourraient être retirés si jugés peu informatifs.")
    print("- **Index Positionnels:** Pour permettre des recherches d'expressions exactes ou de proximité, stocker la position (ou les positions) de chaque terme dans le document (`term -> doc_id -> [pos1, pos2, ...]`).")
    print("- **Pondération TF-IDF dans l'Index:** Stocker le poids TF-IDF du terme dans le document au lieu (ou en plus) de la fréquence brute (TF). Nécessite un calcul préalable du TF-IDF sur les termes normalisés.")
    print("- **Normalisation des Entités Nommées:** Détecter et normaliser les noms de personnes, lieux, organisations pour les indexer de manière cohérente.")
    print("- **Gestion des Variantes/Synonymes:** Utiliser des thesaurus ou des embeddings de mots pour étendre les requêtes aux synonymes ou termes liés lors de la recherche (étape de recherche, pas d'indexation directe).")


class InvertedIndexBuilder:
    """
    Construit des fichiers d'index inversés à partir d'un CorpusClient
    et d'une fonction de normalisation de texte choisie.
    """
    def __init__(self, corpus_client: CorpusClient, text_normalizer: TextNormalizerFunc, doc_id_field: str = 'fichier'):
        """
        Initialise le constructeur d'index.

        Args:
            corpus_client: Le client corpus contenant les documents (idéalement filtrés).
            text_normalizer: La fonction à appliquer aux mots des champs texte (ex: get_spacy_lemmas).
            doc_id_field: L'attribut du document à utiliser comme ID.
        """
        self.client = corpus_client
        self.text_normalizer = text_normalizer
        self.doc_id_field = doc_id_field
        self.indexes: Dict[str, IndexDict] = {} # Stocke les index construits: {'index_name': IndexDict}

    def _get_doc_id(self, doc: Document) -> str:
        """Récupère l'ID du document de manière sécurisée."""
        doc_id = getattr(doc, self.doc_id_field, None)
        # S'assurer que l'ID est une chaîne simple utilisable dans un fichier
        if not doc_id:
            doc_id = f'doc_sans_id_{id(doc)}'
        # Échapper ou remplacer les caractères problématiques si nécessaire (ex: espaces, virgules)
        return str(doc_id).replace(' ', '_').replace(',', ';')

    def _add_to_index(self, index_name: str, term: str, doc_id: str):
        """Ajoute une occurrence d'un terme pour un document à un index spécifique."""
        if not term: # Ignorer les termes vides
            return
        # Initialise l'entrée pour l'index si elle n'existe pas
        if index_name not in self.indexes:
            self.indexes[index_name] = defaultdict(lambda: defaultdict(int))
        # Incrémente la fréquence du terme pour ce document
        self.indexes[index_name][term][doc_id] += 1

    def build_indexes(self, fields_to_index: List[str] = ['numero', 'date', 'rubrique', 'titre', 'texte', 'images_url', 'images_legende']):
        """
        Construit les index inversés pour les champs spécifiés.
        Les champs texte ('titre', 'texte') seront normalisés.

        Args:
            fields_to_index: Liste des noms d'attributs des Documents à indexer.
                             Des noms spéciaux comme 'images_url', 'images_legende', 'titre_texte' sont possibles.
        """
        print(f"Début de la construction des index pour les champs: {fields_to_index}")
        self.indexes = {} # Réinitialiser les index

        text_fields_to_normalize = {'titre', 'texte', 'titre_texte', 'images_legende'}
        combined_titre_texte_needed = 'titre_texte' in fields_to_index

        total_docs = len(self.client.documents)
        for i, doc in enumerate(self.client.documents):
            doc_id = self._get_doc_id(doc)

            # Préparer le contenu combiné si nécessaire
            combined_content = ""
            if combined_titre_texte_needed:
                titre = getattr(doc, 'titre', "") or ""
                texte = getattr(doc, 'texte', "") or ""
                combined_content = f"{titre}\n{texte}"

            for field in fields_to_index:
                index_name = field # Nom par défaut de l'index
                value = None

                if field == 'titre_texte':
                    value = combined_content
                    index_name = "titre_texte_normalized" # Indiquer la normalisation
                elif field == 'images_url':
                    # Cas spécial pour les URLs d'images
                    images: List[Image] = getattr(doc, 'images', [])
                    for img in images:
                        if img.url:
                             # Pas de normalisation de texte pour les URLs
                            self._add_to_index('images_url', img.url.strip(), doc_id)
                    continue # Traitement terminé pour ce champ spécial
                elif field == 'images_legende':
                    # Cas spécial pour les légendes d'images
                    images: List[Image] = getattr(doc, 'images', [])
                    value = "\n".join([img.legende for img in images if img.legende])
                    index_name = "images_legende_normalized" # Sera normalisé
                else:
                    value = getattr(doc, field, None)

                if value is None:
                    continue # Passer au champ suivant si la valeur est None

                # --- Traitement de la valeur ---
                if isinstance(value, datetime):
                    # Indexer la date au format YYYY-MM-DD pour tri lexicographique
                    term = value.strftime('%Y-%m-%d')
                    self._add_to_index(index_name, term, doc_id)
                elif isinstance(value, str):
                    if field in text_fields_to_normalize:
                         # Appliquer la tokenisation et la normalisation
                        index_name = f"{field}_normalized" # Marquer comme normalisé
                        tokens = re.findall(r'\w+', value.lower()) # Tokeniser et minuscule
                        for token in tokens:
                            normalized_term = self.text_normalizer(token)
                            if normalized_term: # Vérifier si la normalisation n'a pas retourné vide
                                self._add_to_index(index_name, normalized_term, doc_id)
                    else:
                         # Indexer la chaîne telle quelle (ou après nettoyage simple)
                         # Pour 'rubrique', 'numero', etc.
                         term = value.strip()
                         if term: # Ignorer les chaînes vides après strip
                             # Optionnel : Mettre en minuscule pour la cohérence ?
                             # term = term.lower()
                             self._add_to_index(index_name, term, doc_id)
                # Ajouter d'autres types si nécessaire (ex: int, float)
                elif isinstance(value, (int, float)):
                     self._add_to_index(index_name, str(value), doc_id)

            if (i + 1) % 100 == 0 or (i + 1) == total_docs:
                print(f"  ... {i+1}/{total_docs} documents traités pour l'indexation.")

        print("Construction des index terminée.")

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

        os.makedirs(output_dir, exist_ok=True)
        print(f"Sauvegarde des fichiers d'index dans le répertoire: {output_dir}")

        for index_name, index_data in self.indexes.items():
            filename = os.path.join(output_dir, f"index_{index_name}.tsv")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # Trier les termes pour un fichier plus lisible/prédictible
                    for term in sorted(index_data.keys()):
                        postings = index_data[term]
                        # Format: doc_id1:freq1 doc_id2:freq2 ...
                        # Trier les doc_ids pour la cohérence
                        postings_str = " ".join([f"{doc_id}:{freq}" for doc_id, freq in sorted(postings.items())])
                        f.write(f"{term}\t{postings_str}\n")
                print(f"  - Index '{index_name}' sauvegardé dans {filename}")
            except IOError as e:
                print(f"Erreur lors de l'écriture du fichier d'index '{filename}': {e}")

        print("Sauvegarde des index terminée.")
