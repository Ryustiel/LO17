# nlp_tools.py
import spacy
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
import re
from typing import List, Dict, Tuple, Callable, Optional  # Tuple n'est pas utilisé directement ici, mais OK
import os

# Importe BaseDocument, la classe de base pour tes documents
from index.transactions.base.base_document import BaseDocument

# Si tu préfères utiliser le type concret Document, ce serait :
# from index.transactions.document import Document

# Charger les modèles spaCy et Snowball une seule fois
try:
    nlp_spacy = spacy.load("fr_core_news_sm")
    print("Modèle spaCy 'fr_core_news_sm' chargé.")
except OSError:
    print("Erreur: Modèle spaCy 'fr_core_news_sm' non trouvé.")
    print("Veuillez l'installer avec : python -m spacy download fr_core_news_sm")
    nlp_spacy = None  # Important pour les vérifications ultérieures

try:
    stemmer_snowball = SnowballStemmer('french')
    print("Stemmer Snowball (français) chargé.")
except Exception as e:  # Peut être plus spécifique si NLTK lève une exception particulière
    print(f"Erreur lors du chargement du stemmer Snowball: {e}")
    stemmer_snowball = None  # Important


# --- Fonctions de base pour la normalisation ---

def get_spacy_lemmas(word: str) -> str:
    """Retourne le lemme d'un mot en utilisant spaCy (après mise en minuscule)."""
    if not nlp_spacy or not word.strip():  # Vérifier aussi si word est vide/blanc
        return word
        # spaCy fonctionne mieux sur du texte déjà en minuscules pour la lemmatisation française simple
    doc = nlp_spacy(word.lower())
    if doc and len(doc) > 0:
        return doc[0].lemma_
    return word  # Fallback si spaCy ne retourne rien


def get_snowball_stem(word: str) -> str:
    """Retourne la racine d'un mot en utilisant Snowball (après mise en minuscule)."""
    if not stemmer_snowball or not word.strip():  # Vérifier aussi si word est vide/blanc
        return word
    return stemmer_snowball.stem(word.lower())


# --- Classe pour la comparaison des méthodes de normalisation ---

class LemmatizerComparer:
    """
    Compare la lemmatisation spaCy et le stemming Snowball sur un corpus.
    Utilise les fonctions get_spacy_lemmas et get_snowball_stem.
    """

    def __init__(self, documents: List[BaseDocument]):  # CHANGEMENT ICI: CorpusDocument -> BaseDocument
        """
        Initialise avec la liste des documents.
        Chaque document doit fournir une propriété 'corps'.
        """
        self.documents = documents
        self._word_list_cache: Optional[List[str]] = None  # Cache pour les mots uniques

    def _get_unique_words(self) -> List[str]:
        """
        Extrait (et met en cache) la liste des mots uniques (en minuscules)
        provenant de la propriété 'corps' de tous les documents.
        """
        if self._word_list_cache is not None:
            return self._word_list_cache

        print("Extraction des mots uniques du corpus pour la comparaison...")
        unique_words: set[str] = set()
        doc_count = len(self.documents)
        for i, doc in enumerate(self.documents):
            # La propriété 'corps' est définie dans BaseDocument
            # et implémentée dans Document pour combiner titre et texte.
            text_content = doc.corps
            if text_content:
                # Tokenisation simple (séquences alphanumériques) pour la comparaison
                tokens = re.findall(r'\w+', text_content.lower())
                unique_words.update(tokens)

            if (i + 1) % 200 == 0 or (i + 1) == doc_count:  # Ajuster la fréquence du log si besoin
                print(f"  ... {i + 1}/{doc_count} documents scannés pour mots uniques.")

        self._word_list_cache = sorted(list(unique_words))
        print(f"Extraction terminée. {len(self._word_list_cache)} mots uniques trouvés.")
        return self._word_list_cache

    def generate_lemma_stem_mappings(self) -> pd.DataFrame:
        """
        Génère un DataFrame pandas: ['mot', 'lemme_spacy', 'racine_snowball'].
        """
        if not nlp_spacy or not stemmer_snowball:
            # Message d'erreur plus précis si l'un des deux manque.
            missing_tools = []
            if not nlp_spacy: missing_tools.append("spaCy")
            if not stemmer_snowball: missing_tools.append("Snowball stemmer")
            print(f"Erreur: {', '.join(missing_tools)} non initialisé(s) correctement.")
            return pd.DataFrame(columns=['mot', 'lemme_spacy', 'racine_snowball'])

        words = self._get_unique_words()
        if not words:
            print("Aucun mot unique trouvé dans le corpus pour générer les mappings.")
            return pd.DataFrame(columns=['mot', 'lemme_spacy', 'racine_snowball'])

        data = []
        print("Génération des lemmes (spaCy) et racines (Snowball) pour les mots uniques...")
        total_words = len(words)
        for i, word in enumerate(words):
            lemma = get_spacy_lemmas(word)  # Utilise déjà word.lower() à l'intérieur
            stem = get_snowball_stem(word)  # Utilise déjà word.lower() à l'intérieur
            data.append({'mot': word, 'lemme_spacy': lemma, 'racine_snowball': stem})

            if (i + 1) % 1000 == 0 or (i + 1) == total_words:  # Ajuster fréquence du log
                print(f"  ... {i + 1}/{total_words} mots uniques traités.")

        df = pd.DataFrame(data)
        print("Génération des mappings terminée.")
        return df

    def save_comparison_file(self, df: pd.DataFrame, output_dir: str = ".",
                             filename_prefix: str = "lemma_comparison") -> Dict[str, str]:
        """
        Sauvegarde les mappings mot->lemme et mot->racine dans des fichiers TSV,
        et le DataFrame complet dans un CSV.
        """
        if df.empty:
            print("DataFrame de comparaison vide, aucun fichier sauvegardé.")
            return {}

        os.makedirs(output_dir, exist_ok=True)
        paths: Dict[str, str] = {}

        # Fichier spaCy: mot<TAB>lemme_spacy (sans en-tête)
        spacy_filename = os.path.join(output_dir, f"{filename_prefix}_spacy.tsv")
        try:
            # Sélectionner et dédoublonner sur la base de ('mot', 'lemme_spacy')
            # car un mot peut avoir le même lemme mais apparaître plusieurs fois si on ne dédoublonne pas.
            # Cependant, generate_lemma_stem_mappings travaille déjà sur des mots uniques.
            # df[['mot', 'lemme_spacy']] est suffisant ici si 'mot' est déjà unique.
            df_spacy = df[['mot', 'lemme_spacy']].drop_duplicates().sort_values(by='mot')
            df_spacy.to_csv(spacy_filename, sep='\t', index=False, header=False, encoding='utf-8')
            paths['spacy'] = spacy_filename
            print(f"Fichier de mapping spaCy sauvegardé : {spacy_filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier spaCy ({spacy_filename}): {e}")

        # Fichier Snowball: mot<TAB>racine_snowball (sans en-tête)
        snowball_filename = os.path.join(output_dir, f"{filename_prefix}_snowball.tsv")
        try:
            df_snowball = df[['mot', 'racine_snowball']].drop_duplicates().sort_values(by='mot')
            df_snowball.to_csv(snowball_filename, sep='\t', index=False, header=False, encoding='utf-8')
            paths['snowball'] = snowball_filename
            print(f"Fichier de mapping Snowball sauvegardé : {snowball_filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier Snowball ({snowball_filename}): {e}")

        # Fichier Comparatif complet (CSV avec en-têtes)
        comparison_filename = os.path.join(output_dir, f"{filename_prefix}_full.csv")
        try:
            # df est déjà le dataframe complet, pas besoin de resélectionner des colonnes
            df.sort_values(by='mot').to_csv(comparison_filename, sep=',', index=False, encoding='utf-8')
            paths['full_comparison'] = comparison_filename
            print(f"Fichier de comparaison complet sauvegardé : {comparison_filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier de comparaison complet ({comparison_filename}): {e}")

        return paths

    def get_stats(self, df: pd.DataFrame) -> Dict[str, any]:  # 'any' pour les pourcentages
        """
        Calcule et affiche des statistiques sur les lemmes/racines générés.
        """
        if df.empty:
            print("DataFrame vide, statistiques non calculables.")
            return {
                "total_mots_uniques": 0, "lemmes_spacy_uniques": 0, "racines_snowball_uniques": 0,
                "mots_non_changes_spacy": 0, "mots_non_changes_snowball": 0,
                "taux_reduction_spacy": "N/A", "taux_reduction_snowball": "N/A",
            }

        total_mots = len(df['mot'].unique())  # df['mot'] devrait déjà être unique si généré par _get_unique_words
        unique_lemmas = df['lemme_spacy'].nunique()
        unique_stems = df['racine_snowball'].nunique()

        # Compter où le mot original est identique à sa forme normalisée
        not_changed_spacy = df[df['mot'] == df['lemme_spacy']].shape[0]
        not_changed_snowball = df[df['mot'] == df['racine_snowball']].shape[0]

        taux_reduc_spacy = (1 - unique_lemmas / total_mots) if total_mots > 0 else 0
        taux_reduc_snowball = (1 - unique_stems / total_mots) if total_mots > 0 else 0

        stats = {
            "total_mots_uniques": total_mots,
            "lemmes_spacy_uniques": unique_lemmas,
            "racines_snowball_uniques": unique_stems,
            "mots_non_changes_spacy": not_changed_spacy,
            "mots_non_changes_snowball": not_changed_snowball,
            "taux_reduction_spacy": f"{taux_reduc_spacy:.2%}",
            "taux_reduction_snowball": f"{taux_reduc_snowball:.2%}",
        }
        print("\nStatistiques Comparatives de Normalisation:")
        for key, value in stats.items():
            print(f"- {key.replace('_', ' ').capitalize()}: {value}")

        return stats


# --- Fonctions utilitaires pour l'indexation et la recherche ---

# Type alias pour la fonction de normalisation de texte (utilisée par InvertedIndexBuilder et QueryParser)
TextNormalizerFunc = Callable[[str], str]


def get_normalizer(method: str) -> TextNormalizerFunc:
    """
    Retourne la fonction de normalisation appropriée ('spacy', 'snowball', ou 'none')
    pour l'indexation ou le traitement des requêtes.
    """
    if method == 'spacy':
        if nlp_spacy is None:
            print("Avertissement: spaCy n'est pas chargé. Normalisation 'spacy' demandée, fallback sur 'none'.")
            return lambda word: word.lower()  # Fallback sécurisé
        print("Utilisation de la lemmatisation spaCy pour la normalisation.")
        return get_spacy_lemmas
    elif method == 'snowball':
        if stemmer_snowball is None:
            print(
                "Avertissement: Snowball stemmer n'est pas chargé. Normalisation 'snowball' demandée, fallback sur 'none'.")
            return lambda word: word.lower()  # Fallback sécurisé
        print("Utilisation du stemming Snowball pour la normalisation.")
        return get_snowball_stem
    elif method == 'none':
        print("Aucune lemmatisation/stemming appliquée (mots en minuscules uniquement).")
        return lambda word: word.lower()  # Simple mise en minuscule
    else:
        print(f"Méthode de normalisation '{method}' non reconnue. Fallback sur 'none'.")
        return lambda word: word.lower()