# main.py (ou orchestrator.py, si c'est le nom de ton script principal)
import os
import time
from typing import List

# Importations depuis la structure de projet
from index.clients.bs4_parser import BS4Parser
from index.transactions.document import Document
from index.transactions.corpus import Corpus
from data.backup import nlp_tools  # Importer le module pour vérifier nlp_spacy
from data.backup.nlp_tools import LemmatizerComparer, get_normalizer
from data.backup.index_builder import InvertedIndexBuilder

# --- Configuration ---
# Utiliser des chemins relatifs par rapport à l'emplacement de ce script,
# ou des chemins absolus si nécessaire.
# Si ce script est dans index/nlp/, et data est deux niveaux au-dessus:
BASE_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_SCRIPT_DIR, "..", ".."))  # Ajuster si la structure est différente

DATA_FOLDER = os.path.join(PROJECT_ROOT, "data", "BULLETINS")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")  # Tous les outputs iront ici

FILTERED_XML_FILE = os.path.join(OUTPUT_DIR, "corpus_filtre.xml")
ANTI_DICT_FILE = os.path.join(OUTPUT_DIR, "anti_dictionnaire.txt")
INDEX_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "index_files")
COMPARISON_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "lemma_comparison")

PROCESS_LIMIT = 100  # None pour tout traiter

FIELDS_TO_INDEX = [
    'numero', 'date', 'rubrique', 'titre', 'texte',
    'titre_texte', 'images_url', 'images_legende'
]

# --- Début du Script ---
if __name__ == "__main__":

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(INDEX_OUTPUT_DIR, exist_ok=True)
    os.makedirs(COMPARISON_OUTPUT_DIR, exist_ok=True)

    start_time = time.time()

    # Vérification initiale de spaCy pour un feedback rapide
    if nlp_tools.nlp_spacy is None:
        print("AVERTISSEMENT IMPORTANT: Le modèle spaCy ('fr_core_news_sm') n'a pas été chargé.")
        print("  Veuillez l'installer dans votre environnement virtuel (.venv) avec :")
        print("  python -m spacy download fr_core_news_sm")
        print("  Les fonctionnalités dépendant de spaCy (lemmatisation, comparaison) seront affectées.")

    # 1. Chargement et Parsing Initial
    print(f"1. Chargement et parsing des fichiers depuis: {DATA_FOLDER}")
    if not os.path.isdir(DATA_FOLDER):
        print(f"Erreur: Le dossier de données '{DATA_FOLDER}' n'existe pas. Vérifiez le chemin.")
        exit()

    parser = BS4Parser()
    raw_documents: List[Document] = parser.process_folder(DATA_FOLDER, limit=PROCESS_LIMIT)

    if not raw_documents:
        print("Aucun document trouvé ou traité. Arrêt.")
        exit()
    print(f"{len(raw_documents)} documents bruts chargés.")

    corpus_obj = Corpus(documents=raw_documents)
    print(f"Objet Corpus créé avec {len(corpus_obj.documents)} documents.")

    # 2. Création et Application de l'Anti-dictionnaire
    print(f"\n2. Gestion de l'anti-dictionnaire: {ANTI_DICT_FILE}")
    can_apply_anti_dict = False
    if hasattr(corpus_obj, 'anti_dict') and callable(getattr(corpus_obj, 'anti_dict')):
        can_apply_anti_dict = True
        if not os.path.exists(ANTI_DICT_FILE):
            print(f"Fichier anti-dictionnaire '{ANTI_DICT_FILE}' non trouvé. Création...")
            try:
                mots_pour_anti_dict = corpus_obj.anti_dict()  # Supposé retourner List[str]
                with open(ANTI_DICT_FILE, "w", encoding="utf-8") as f_anti:
                    for mot in mots_pour_anti_dict:
                        f_anti.write(f"{mot}\t\n")
                print(f"Anti-dictionnaire créé : {ANTI_DICT_FILE} avec {len(mots_pour_anti_dict)} entrées.")
            except Exception as e:
                print(f"Erreur lors de la création de l'anti-dictionnaire : {e}")
                can_apply_anti_dict = False
        else:
            print(f"Le fichier anti-dictionnaire existe déjà : {ANTI_DICT_FILE}")
    else:
        print("Avertissement: Méthode 'anti_dict' non trouvée sur l'objet Corpus.")
        print("L'anti-dictionnaire ne sera pas généré ni appliqué.")

    if can_apply_anti_dict:
        if hasattr(corpus_obj, 'apply_substitutions') and callable(getattr(corpus_obj, 'apply_substitutions')):
            print("Application des substitutions de l'anti-dictionnaire au corpus...")
            # La méthode apply_substitutions de ton Corpus devrait gérer les logs internes
            corpus_obj.apply_substitutions(ANTI_DICT_FILE)
            print("Substitutions de l'anti-dictionnaire (potentiellement) appliquées.")  # Message plus neutre
        else:
            print("Avertissement: Méthode 'apply_substitutions' non trouvée sur l'objet Corpus.")
    else:
        print("Skipping application de l'anti-dictionnaire.")

    # 3. Sauvegarde du Corpus Filtré en XML
    print(f"\n3. Sauvegarde du corpus traité en XML: {FILTERED_XML_FILE}")
    # Utilisation de model_dump_xml_str_pretty comme dans le notebook
    # Le `root_tag` est géré par le paramètre `tags` de `model_dump_xml_str_pretty`.
    # Si la classe Corpus doit avoir le tag racine "corpusFiltre":
    storage_tags = {"Corpus": "corpusFiltre", "documents": "bulletins", "Document": "bulletin", "Image": "image"}
    try:
        xml_output_str = corpus_obj.model_dump_xml_str_pretty(tags=storage_tags)
        with open(FILTERED_XML_FILE, "w", encoding="utf-8") as f_xml:
            f_xml.write(xml_output_str)
        print(f"Corpus sauvegardé dans {FILTERED_XML_FILE}")
    except AttributeError:
        print("Erreur: La méthode 'model_dump_xml_str_pretty' n'est pas disponible sur l'objet Corpus.")
        print("Vérifiez que votre classe Corpus hérite bien de XMLBaseModel et que la méthode est correcte.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du corpus en XML : {e}")

    # 4. Analyse comparative de la Lemmatisation/Stemming
    print("\n4. Analyse comparative de la lemmatisation (spaCy vs Snowball)")
    if nlp_tools.nlp_spacy is None and nlp_tools.stemmer_snowball is None:
        print("SpaCy et Snowball ne sont pas chargés. Impossible de faire la comparaison.")
    else:
        lemmatizer_comparer = LemmatizerComparer(corpus_obj.documents)
        comparison_df = lemmatizer_comparer.generate_lemma_stem_mappings()  # Gère déjà les cas où spaCy ou Snowball manquent

        if not comparison_df.empty:
            lemmatizer_comparer.save_comparison_file(comparison_df, output_dir=COMPARISON_OUTPUT_DIR)
            lemmatizer_comparer.get_stats(comparison_df)
            print(f"\n--> Fichiers de comparaison générés dans '{COMPARISON_OUTPUT_DIR}'.")
            print("--> Choisissez la méthode ('spacy', 'snowball', ou 'none') pour l'indexation.")
        else:
            print("Aucune donnée de comparaison de lemmatisation générée.")

    # 5. Choix de la méthode de normalisation et Création des Index Inversés
    CHOSEN_NORMALIZER_METHOD = 'spacy'  # ou 'snowball' ou 'none'
    print(f"\n5. Création des index inversés avec la normalisation: '{CHOSEN_NORMALIZER_METHOD}'")

    # get_normalizer gère les cas où l'outil demandé n'est pas chargé
    normalizer_function = get_normalizer(CHOSEN_NORMALIZER_METHOD)

    index_builder = InvertedIndexBuilder(
        corpus_obj=corpus_obj,  # CORRECTION ICI: corpus_client -> corpus_obj
        text_normalizer=normalizer_function,
        doc_id_field='fichier'
    )

    index_builder.build_indexes(fields_to_index=FIELDS_TO_INDEX)
    index_builder.save_indexes(output_dir=INDEX_OUTPUT_DIR)
    print(f"Index sauvegardés dans le répertoire: {INDEX_OUTPUT_DIR}")

    # 6. Bonus: Suggestions d'amélioration
    if hasattr(index_builder, 'suggest_improvements') and callable(getattr(index_builder, 'suggest_improvements')):
        print("\n6. Suggestions d'amélioration pour l'indexation:")
        index_builder.suggest_improvements()

    end_time = time.time()
    print(f"\nTraitement complet terminé en {end_time - start_time:.2f} secondes.")