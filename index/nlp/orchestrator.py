# main.py
import os
import time
from typing import List

# Importations depuis la structure de projet
from index.clients.bs4_parser import BS4Parser
from index.clients.corpus_client import CorpusClient
from index.transactions.document import Document
from index.nlp.nlp_tools import LemmatizerComparer, get_normalizer # Outils NLP
from index.nlp.index_builder import InvertedIndexBuilder # Constructeur d'index

# --- Configuration ---
DATA_FOLDER = "../../data/BULLETINS" # À ADAPTER
OUTPUT_DIR = "output"
FILTERED_XML_FILE = os.path.join(OUTPUT_DIR, "corpus_filtre.xml")
ANTI_DICT_FILE = "output/anti_dictionnaire.txt" # Chemin vers l'anti-dictionnaire
INDEX_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "index_files")
COMPARISON_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "lemma_comparison")

# Limite pour le développement/test (mettre None pour tout traiter)
PROCESS_LIMIT = 100 # None

# Champs à indexer
FIELDS_TO_INDEX = [
    'numero',
    'date',      # Sera indexé comme YYYY-MM-DD
    'rubrique',  # Indexé tel quel (ou en minuscule)
    'titre',     # Sera normalisé (lemmatisé/stemmé)
    'texte',     # Sera normalisé (lemmatisé/stemmé)
    'titre_texte', # Combiné et normalisé
    'images_url', # URLs des images
    'images_legende' # Légendes normalisées
]

# --- Début du Script ---
if __name__ == "__main__":

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    start_time = time.time()

    # 1. Chargement et Parsing Initial
    print(f"1. Chargement et parsing des fichiers depuis: {DATA_FOLDER}")
    parser = BS4Parser() # Utilise le parser existant

    # Alternative 1: Si from_folder fonctionne avec le client générique
    # try:
    #     corpus_client = CorpusClient.from_folder(parser, DATA_FOLDER, limit=PROCESS_LIMIT)
    # except TypeError as e:
    #     print(f"Erreur au chargement: {e}")
    #     print("BS4Parser retourne-t-il des objets héritant de CorpusDocument ?")
    #     exit()

    # Alternative 2: Chargement manuel (plus sûr si from_folder est strict)
    print("Chargement via process_folder...")
    raw_documents: List[Document] = parser.process_folder(DATA_FOLDER, limit=PROCESS_LIMIT)
    print(f"{len(raw_documents)} documents chargés.")
    if not raw_documents:
        print("Aucun document trouvé ou traité. Arrêt.")
        exit()
    # Vérification du type (si nécessaire)
    # if not isinstance(raw_documents[0], CorpusDocument):
    #      print("Erreur: Les objets retournés par le parser n'héritent pas de CorpusDocument.")
    #      exit()
    corpus_client = CorpusClient(raw_documents)
    print(f"CorpusClient créé avec {len(corpus_client.documents)} documents.")

    # 2. Vérification/Création et Application de l'anti-dictionnaire
    print(f"\n2. Anti-dictionnaire: {ANTI_DICT_FILE}")
    if os.path.exists(ANTI_DICT_FILE):
        print(f"Le fichier anti-dictionnaire existe déjà. Application des substitutions...")
    else:
        print(f"Fichier anti-dictionnaire '{ANTI_DICT_FILE}' non trouvé. Création automatique...")
        from index.clients.corpus_client import CorpusTFIDFCalculator

        # Paramètres pour la génération de l'anti-dictionnaire
        IDF_THRESHOLD = 0.1  # Seuil IDF pour identifier les mots trop fréquents

        # Créer le calculateur TFIDF
        tfidf_calculator = CorpusTFIDFCalculator(corpus_client)

        # Générer l'anti-dictionnaire
        anti_dict_file = tfidf_calculator.generate_anti_dict(
            idf_threshold=IDF_THRESHOLD,
            output_file=ANTI_DICT_FILE
        )
        print(f"Anti-dictionnaire créé: {anti_dict_file}")

    # Appliquer les substitutions
    print("Application des substitutions...")
    corpus_client.apply_substitutions(ANTI_DICT_FILE)

    # 3. Sauvegarde du Corpus Filtré en XML (selon l'énoncé TD)
    print(f"\n3. Sauvegarde du corpus filtré en XML: {FILTERED_XML_FILE}")
    corpus_client.save_to_xml(FILTERED_XML_FILE, root_tag="corpusFiltre")

    # 4. Analyse comparative de la Lemmatisation/Stemming
    print("\n4. Analyse comparative de la lemmatisation (spaCy vs Snowball)")
    lemmatizer_comparer = LemmatizerComparer(corpus_client.documents)
    comparison_df = lemmatizer_comparer.generate_lemma_stem_mappings()

    if not comparison_df.empty:
        # Sauvegarde des fichiers pour analyse manuelle
        lemmatizer_comparer.save_comparison_file(comparison_df, output_dir=COMPARISON_OUTPUT_DIR)
        # Affichage des statistiques
        lemmatizer_comparer.get_stats(comparison_df)
        print(f"\n--> Analysez les fichiers dans '{COMPARISON_OUTPUT_DIR}' ({COMPARISON_OUTPUT_DIR}/lemma_comparison_spacy.tsv, ..._snowball.tsv, ..._full.csv)")
        print("--> Choisir la méthode ('spacy' ou 'snowball') qui semble la plus adaptée pour le corpus.")
    else:
        print("Aucune donnée de comparaison générée (corpus vide après filtrage?).")

    # 5. Choix de la méthode et Création des Index Inversés
    # !!!!! IMPORTANT !!!!!
    # Modifier cette ligne en fonction de l'analyse des fichiers générés
    CHOSEN_NORMALIZER_METHOD = 'spacy' # ou 'snowball' ou 'none'
    # !!!!!!!!!!

    print(f"\n5. Création des index inversés avec la méthode choisie: '{CHOSEN_NORMALIZER_METHOD}'")
    normalizer_function = get_normalizer(CHOSEN_NORMALIZER_METHOD)

    # Création du builder d'index
    index_builder = InvertedIndexBuilder(
        corpus_client=corpus_client,
        text_normalizer=normalizer_function,
        doc_id_field='fichier' # Assurez-vous que c'est le bon champ ID
    )

    # Construction des index en mémoire
    index_builder.build_indexes(fields_to_index=FIELDS_TO_INDEX)

    # Sauvegarde des index dans des fichiers
    index_builder.save_indexes(output_dir=INDEX_OUTPUT_DIR)

    # 6. Bonus: Suggestions d'amélioration
    #print("\n6. Suggestions d'amélioration")
    #index_builder.suggest_improvements()

    # --- Fin du Script ---
    end_time = time.time()
    print(f"\nTraitement terminé en {end_time - start_time:.2f} secondes.")