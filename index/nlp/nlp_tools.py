# nlp_tools.py
import spacy
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
import re
from typing import List, Dict, Tuple, Callable
import os

from index.transactions.base.corpus_document import CorpusDocument

# Charger les modèles une seule fois
try:
    nlp_spacy = spacy.load("fr_core_news_sm")
    print("Modèle spaCy 'fr_core_news_sm' chargé.")
except OSError:
    print("Erreur: Modèle spaCy 'fr_core_news_sm' non trouvé.")
    print("Veuillez l'installer avec : python -m spacy download fr_core_news_sm")
    nlp_spacy = None

try:
    stemmer_snowball = SnowballStemmer('french')
    print("Stemmer Snowball (français) chargé.")
except Exception as e:
    print(f"Erreur lors du chargement du stemmer Snowball: {e}")
    stemmer_snowball = None

# --- Fonctions de base ---

def get_spacy_lemmas(word: str) -> str:
    """Retourne le lemme d'un mot en utilisant spaCy."""
    if not nlp_spacy or not word:
        return word # Retourne le mot original si spaCy n'est pas chargé ou le mot est vide
    # Traiter le mot (même s'il est unique) comme un petit document
    doc = nlp_spacy(word.lower()) # Mettre en minuscule pour la lemmatisation
    # Prendre le lemme du premier token (il ne devrait y en avoir qu'un)
    if doc and len(doc) > 0:
        return doc[0].lemma_
    return word # Fallback

def get_snowball_stem(word: str) -> str:
    """Retourne la racine d'un mot en utilisant Snowball."""
    if not stemmer_snowball or not word:
        return word # Retourne le mot original si Snowball n'est pas chargé ou le mot est vide
    return stemmer_snowball.stem(word.lower()) # Mettre en minuscule pour le stemming

# --- Classe pour la comparaison ---

class LemmatizerComparer:
    """
    Compare spaCy et Snowball sur un corpus et génère des rapports.
    Utilise les fonctions get_spacy_lemmas et get_snowball_stem.
    """
    def __init__(self, documents: List['CorpusDocument']):
        """
        Initialise avec la liste des documents (après filtrage anti-dict).
        """
        self.documents = documents
        self._word_list_cache = None

    def _get_unique_words(self) -> List[str]:
        """
        Extrait et met en cache la liste des mots uniques (minuscules)
        provenant des champs 'corps_fields' de tous les documents.
        """
        if self._word_list_cache is not None:
            return self._word_list_cache

        print("Extraction des mots uniques du corpus pour la comparaison...")
        unique_words = set()
        for i, doc in enumerate(self.documents):
            # Utilise la propriété 'corps' qui combine les champs pertinents
            text_content = doc.corps
            if text_content:
                # Tokenisation simple pour la comparaison
                tokens = re.findall(r'\w+', text_content.lower())
                unique_words.update(tokens)
            if (i + 1) % 100 == 0:
                 print(f"  ... {i+1}/{len(self.documents)} documents scannés.")

        self._word_list_cache = sorted(list(unique_words))
        print(f"Extraction terminée. {len(self._word_list_cache)} mots uniques trouvés.")
        return self._word_list_cache

    def generate_lemma_stem_mappings(self) -> pd.DataFrame:
        """
        Génère un DataFrame contenant le mot original, son lemme spaCy et sa racine Snowball.

        Returns:
            pd.DataFrame: DataFrame avec colonnes ['mot', 'lemme_spacy', 'racine_snowball']
        """
        if not nlp_spacy or not stemmer_snowball:
            print("Erreur: spaCy ou Snowball n'est pas correctement initialisé.")
            return pd.DataFrame(columns=['mot', 'lemme_spacy', 'racine_snowball'])

        words = self._get_unique_words()
        data = []
        print("Génération des lemmes (spaCy) et racines (Snowball)...")
        total_words = len(words)
        for i, word in enumerate(words):
            lemma = get_spacy_lemmas(word)
            stem = get_snowball_stem(word)
            data.append({'mot': word, 'lemme_spacy': lemma, 'racine_snowball': stem})
            if (i + 1) % 500 == 0 or (i + 1) == total_words:
                print(f"  ... {i+1}/{total_words} mots traités.")

        df = pd.DataFrame(data)
        print("Génération terminée.")
        return df

    def save_comparison_file(self, df: pd.DataFrame, output_dir: str = ".", filename_prefix: str = "lemma_comparison") -> Dict[str, str]:
        """
        Sauvegarde les mappings mot -> lemme et mot -> racine dans des fichiers séparés.

        Args:
            df (pd.DataFrame): DataFrame généré par generate_lemma_stem_mappings.
            output_dir (str): Répertoire de sortie.
            filename_prefix (str): Préfixe pour les noms de fichiers.

        Returns:
            Dict[str, str]: Dictionnaire des chemins des fichiers créés.
        """
        if df.empty:
            print("DataFrame vide, aucun fichier de comparaison sauvegardé.")
            return {}

        os.makedirs(output_dir, exist_ok=True)

        paths = {}

        # Fichier spaCy: mot -> lemme
        spacy_filename = os.path.join(output_dir, f"{filename_prefix}_spacy.tsv")
        try:
            df_spacy = df[['mot', 'lemme_spacy']].drop_duplicates()
            df_spacy.to_csv(spacy_filename, sep='\t', index=False, header=False, encoding='utf-8')
            paths['spacy'] = spacy_filename
            print(f"Fichier de mapping spaCy sauvegardé dans : {spacy_filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier spaCy: {e}")

        # Fichier Snowball: mot -> racine
        snowball_filename = os.path.join(output_dir, f"{filename_prefix}_snowball.tsv")
        try:
            df_snowball = df[['mot', 'racine_snowball']].drop_duplicates()
            df_snowball.to_csv(snowball_filename, sep='\t', index=False, header=False, encoding='utf-8')
            paths['snowball'] = snowball_filename
            print(f"Fichier de mapping Snowball sauvegardé dans : {snowball_filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier Snowball: {e}")

        # Fichier Comparatif complet
        comparison_filename = os.path.join(output_dir, f"{filename_prefix}_full.csv")
        try:
            df.to_csv(comparison_filename, sep=',', index=False, encoding='utf-8')
            paths['full_comparison'] = comparison_filename
            print(f"Fichier de comparaison complet sauvegardé dans : {comparison_filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier de comparaison complet: {e}")


        return paths

    def get_stats(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Calcule des statistiques simples sur les lemmes/racines générés.

        Args:
            df (pd.DataFrame): DataFrame généré par generate_lemma_stem_mappings.

        Returns:
            Dict[str, int]: Dictionnaire de statistiques.
        """
        if df.empty:
            return {
                "total_mots_uniques": 0,
                "lemmes_spacy_uniques": 0,
                "racines_snowball_uniques": 0,
                "mots_non_changes_spacy": 0,
                "mots_non_changes_snowball": 0,
            }

        total_mots = len(df)
        unique_lemmas = df['lemme_spacy'].nunique()
        unique_stems = df['racine_snowball'].nunique()
        not_changed_spacy = df[df['mot'] == df['lemme_spacy']].shape[0]
        not_changed_snowball = df[df['mot'] == df['racine_snowball']].shape[0]

        stats = {
            "total_mots_uniques": total_mots,
            "lemmes_spacy_uniques": unique_lemmas,
            "racines_snowball_uniques": unique_stems,
            "mots_non_changes_spacy": not_changed_spacy,
            "mots_non_changes_snowball": not_changed_snowball,
        }
        print("\nStatistiques Comparatives:")
        for key, value in stats.items():
            print(f"- {key}: {value}")
        print(f"- Taux de réduction (spaCy): {1 - unique_lemmas / total_mots:.2%}" if total_mots else "N/A")
        print(f"- Taux de réduction (Snowball): {1 - unique_stems / total_mots:.2%}" if total_mots else "N/A")

        return stats

# --- Fonctions utilitaires pour l'indexation ---
# Type alias pour la fonction de normalisation de texte choisie
TextNormalizerFunc = Callable[[str], str]

def get_normalizer(method: str) -> TextNormalizerFunc:
    """Retourne la fonction de normalisation appropriée ('spacy', 'snowball', ou 'none')."""
    if method == 'spacy':
        print("Utilisation de la lemmatisation spaCy pour l'indexation.")
        return get_spacy_lemmas
    elif method == 'snowball':
        print("Utilisation du stemming Snowball pour l'indexation.")
        return get_snowball_stem
    else: # 'none' or anything else
        print("Aucune lemmatisation/stemming appliquée pour l'indexation (mots originaux).")
        return lambda word: word.lower() # Simple mise en minuscule