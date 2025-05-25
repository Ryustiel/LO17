import unittest
import os
import pandas
from typing import Dict, Set
from index.transactions.corpus import Corpus
from index.transactions.document import Document
from index.transactions.query import Query
from index.transactions.base.inverted_index import InvertedIndex

# --- Configuration des tests ---
# Utilise le dossier 'output' relatif au script de test actuel.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#Delete \tests from the path
BASE_DIR = os.path.dirname(BASE_DIR)  # Remonte d'un niveau pour atteindre le dossier racine du projet
DATA_FOLDER = os.path.join(BASE_DIR,"output")

XML_INITIAL_FILE = os.path.join(DATA_FOLDER,"corpus_initial.xml")
TEXTE_INDEX_FILE = os.path.join(DATA_FOLDER, "index_files", "texte_index.xml")
TITRE_INDEX_FILE = os.path.join(DATA_FOLDER, "index_files", "titre_index.xml")

missing_files = []
for f_path in [XML_INITIAL_FILE, TEXTE_INDEX_FILE, TITRE_INDEX_FILE]:
    if not os.path.exists(f_path):
        missing_files.append(f_path)


@unittest.skipIf(missing_files, f"Données de test manquantes: {', '.join(missing_files)}. Vérifiez les chemins.")
class TestQuerySearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Charge les données (corpus et index) une seule fois pour tous les tests de cette classe.
        """
        cls.INDEX: Dict[str, InvertedIndex] = {}
        try:
            # Charger l'index de contenu
            df_texte = pandas.read_csv(TEXTE_INDEX_FILE, sep="\t", encoding="utf-8", keep_default_na=False,
                                       na_values=['_NaN_', '_None_'])
            cls.INDEX["content"] = InvertedIndex.from_dataframe(df_texte)

            # Charger l'index de titre
            df_titre = pandas.read_csv(TITRE_INDEX_FILE, sep="\t", encoding="utf-8", keep_default_na=False,
                                       na_values=['_NaN_', '_None_'])
            cls.INDEX["title"] = InvertedIndex.from_dataframe(df_titre)
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Fichier d'index non trouvé, skip des tests: {e}")
        except Exception as e:  # Pour tout autre problème de chargement d'index
            raise unittest.SkipTest(f"Erreur chargement index: {e}")

        cls.STORAGE_TAGS = {"Corpus": "corpus", "documents": "bulletins", "Document": "bulletin", "Image": "image"}
        try:
            with open(XML_INITIAL_FILE, "r", encoding="utf-8") as f:
                if hasattr(Corpus, 'model_validate_xml'):
                    cls.CORPUS_DATA = Corpus.model_validate_xml(f.read(), tags=cls.STORAGE_TAGS)
                else:  # Fallback si model_validate_xml n'est pas défini (pour la simulation)
                    print("WARN: Corpus.model_validate_xml non trouvé, utilisation d'une structure Corpus vide.")
                    cls.CORPUS_DATA = Corpus(documents=[])
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Fichier de corpus non trouvé, skip des tests: {e}")
        except Exception as e:  # Pour tout autre problème de chargement de corpus
            raise unittest.SkipTest(f"Erreur chargement corpus: {e}")

        cls.documents_dict_for_search: Dict[str, Document] = {
            doc.document_id: doc for doc in cls.CORPUS_DATA.documents if doc.document_id
        }

        if not cls.documents_dict_for_search:
            print("WARN: Aucun document chargé dans documents_dict_for_search. Les tests pourraient échouer.")

    def _run_search_test(self, query_str: str, expected_ids_or_rubrics: Set[str], target_is_rubrics: bool = False,
                         debug_query: bool = False):
        """
        Méthode d'aide pour exécuter une requête et comparer les résultats.
        """
        query_obj = Query.build(query_str)
        if debug_query:
            print(f"\nQuery string: {query_str}")
            print(f"Parsed Query object: {query_obj.model_dump_json(indent=2)}")

        expected_target_info = 'rubriques' if target_is_rubrics else 'articles'
        self.assertEqual(query_obj.target_info, expected_target_info,
                         f"Pour '{query_str}', target_info attendu '{expected_target_info}' mais obtenu '{query_obj.target_info}'")

        results = query_obj.search(self.documents_dict_for_search, index=self.INDEX, debug=debug_query)

        if target_is_rubrics:
            actual_results_set = set(results)  # results est déjà List[str]
        else:
            actual_results_set = {doc.document_id for doc in results}  # results est List[Document]

        try:
            self.assertSetEqual(actual_results_set, expected_ids_or_rubrics)
        except AssertionError:
            missing = expected_ids_or_rubrics - actual_results_set
            extra = actual_results_set - expected_ids_or_rubrics
            msg = (
                f"\n--- Différence pour la requête: '{query_str}' ---\n"
                f"- Manquants (attendus, pas trouvés): {missing}\n"
                f"- En trop (trouvés, pas attendus): {extra}\n"
                f"---\n"
            )
            print(msg)
            raise

    def test_etats_unis_date_range(self):
        query_str = "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les etatsunis ?"
        expected_doc_ids = {"72932.htm"}
        self._run_search_test(query_str, expected_doc_ids)

    def test_annee_rubrique_contenu(self):
        query_str = "Je veux les articles de 2014 et de la rubrique Focus et parlant de la santé"
        expected_doc_ids = {"75458.htm", "75459.htm", "76507.htm"}
        self._run_search_test(query_str, expected_doc_ids)

    def test_rubriques_nutrition_vins(self):
        query_str = "Je souhaite les rubriques des articles parlant de nutrition ou de vin."
        expected_rubrics = {"Focus", "Au coeur des régions", "Du côté des pôles", "Actualité Innovation",
                            "Actualités Innovations", "Evénement"}
        self._run_search_test(query_str, expected_rubrics, target_is_rubrics=True)

    def test_serious_game_realite_virtuelle_aucun(self):
        query_str = "Article traitant des Serious Game et de la réalité virtuelle."
        expected_doc_ids = set()  # Aucun document ne valide cette requête
        self._run_search_test(query_str, expected_doc_ids)

    def test_image_titre_croissance(self):
        query_str = "Je voudrais les articles avec des images dont le titre contient le mot croissance."
        expected_doc_ids = {"68390.htm"}
        self._run_search_test(query_str, expected_doc_ids)

    def test_cnrs_grandes_ecoles_sauf_centrale(self):
        query_str = "Liste des articles qui parlent soit du cnr, soit des grand ecole, mais pas de centrale pari."
        expected_doc_ids = {
            "67068.htm", "67071.htm", "67383.htm", "67385.htm", "67387.htm", "67390.htm", "67391.htm",
            "67556.htm", "67558.htm", "67795.htm", "67799.htm", "67800.htm", "67802.htm", "67937.htm",
            "67939.htm", "67943.htm", "67944.htm", "67945.htm", "68276.htm", "68277.htm", "68278.htm",
            "68280.htm", "68281.htm", "68384.htm", "68385.htm", "68388.htm", "68389.htm", "68390.htm",
            "68393.htm", "68638.htm", "68639.htm", "68641.htm", "68642.htm", "68644.htm", "68645.htm",
            "68646.htm", "68883.htm", "68886.htm", "68887.htm", "68889.htm", "69177.htm", "69178.htm",
            "69180.htm", "69181.htm", "69182.htm", "69183.htm", "69184.htm", "69185.htm", "69186.htm",
            "69533.htm", "69539.htm", "69540.htm", "69541.htm", "69542.htm", "69814.htm", "69816.htm",
            "69819.htm", "69820.htm", "70161.htm", "70163.htm", "70168.htm", "70420.htm", "70422.htm",
            "70423.htm", "70424.htm", "70425.htm", "70743.htm", "70744.htm", "70745.htm", "70747.htm",
            "70748.htm", "70914.htm", "70916.htm", "70922.htm", "70923.htm", "71358.htm", "71361.htm",
            "71362.htm", "71363.htm", "71612.htm", "71615.htm", "71835.htm", "71838.htm", "71841.htm",
            "71843.htm", "72114.htm", "72119.htm", "72121.htm", "72397.htm", "72398.htm", "72632.htm",
            "72633.htm", "72634.htm", "72635.htm", "72637.htm", "72932.htm", "72934.htm", "72939.htm",
            "72940.htm", "73182.htm", "73183.htm", "73185.htm", "73186.htm", "73188.htm", "73189.htm",
            "73190.htm", "73431.htm", "73434.htm", "73436.htm", "73683.htm", "73685.htm", "73687.htm",
            "73688.htm", "73877.htm", "73882.htm", "73883.htm", "74170.htm", "74173.htm", "74175.htm",
            "74450.htm", "74452.htm", "74455.htm", "74750.htm", "74752.htm", "75063.htm", "75065.htm",
            "75066.htm", "75067.htm", "75070.htm", "75071.htm", "75457.htm", "75458.htm", "75460.htm",
            "75463.htm", "75464.htm", "75790.htm", "75791.htm", "75794.htm", "75796.htm", "76208.htm",
            "76210.htm", "76513.htm"
        }
        self._run_search_test(query_str, expected_doc_ids)  # , debug_query=True)

    def test_rubrique_focus_actualites_chercheurs_paris(self):
        query_str = "Je souhaites avoir tout les articles donc la rubrique est focus ou Actualités Innovations et qui contiennent les mots chercheur et pari."
        expected_doc_ids = {
            "67068.htm", "67795.htm", "68638.htm", "69178.htm", "70421.htm", "70422.htm", "70424.htm",
            "70914.htm", "71612.htm", "71835.htm", "71837.htm", "71841.htm", "72113.htm", "72393.htm",
            "72932.htm", "72933.htm", "73431.htm", "75063.htm", "75065.htm", "75788.htm","73184.htm"
        }
        self._run_search_test(query_str, expected_doc_ids)

    def test_date_1dec2012_rubrique_actualites_innovations_rien(self):
        query_str = "Je voudrais les articles qui datent du 1 décembre 2012 et dont la rubrique est Actualités Innovations."
        expected_doc_ids = set()  # Rien
        self._run_search_test(query_str, expected_doc_ids)

    def test_entre_2012_2013_sauf_juin(self):
        query_str = "Je voudrais tous les bulletins écrits entre 2012 et 2013 mais pas au mois de juin"
        expected_doc_ids = {
            "68881.htm", "68882.htm", "68883.htm", "68884.htm", "68885.htm", "68886.htm", "68887.htm",
            "68888.htm", "68889.htm", "69177.htm", "69178.htm", "69179.htm", "69180.htm", "69181.htm",
            "69182.htm", "69183.htm", "69184.htm", "69185.htm", "69186.htm", "69533.htm", "69534.htm",
            "69535.htm", "69536.htm", "69537.htm", "69538.htm", "69539.htm", "69540.htm", "69541.htm",
            "69542.htm", "69543.htm", "69811.htm", "69812.htm", "69813.htm", "69814.htm", "69815.htm",
            "69816.htm", "69817.htm", "69818.htm", "69819.htm", "69820.htm", "69821.htm", "70161.htm",
            "70162.htm", "70163.htm", "70164.htm", "70165.htm", "70166.htm", "70167.htm", "70168.htm",
            "70169.htm", "70170.htm", "70743.htm", "70744.htm", "70745.htm", "70746.htm", "70747.htm",
            "70748.htm", "70749.htm", "70751.htm", "70752.htm", "70753.htm", "70914.htm", "70915.htm",
            "70916.htm", "70917.htm", "70918.htm", "70919.htm", "70920.htm", "70921.htm", "70922.htm",
            "70923.htm", "71357.htm", "71358.htm", "71359.htm", "71360.htm", "71361.htm", "71362.htm",
            "71363.htm", "71366.htm", "71612.htm", "71614.htm", "71615.htm", "71616.htm", "71617.htm",
            "71618.htm", "71619.htm", "71620.htm", "71621.htm", "71835.htm", "71836.htm", "71837.htm",
            "71838.htm", "71839.htm", "71840.htm", "71841.htm", "71842.htm", "71843.htm", "71845.htm",
            "72113.htm", "72114.htm", "72115.htm", "72116.htm", "72117.htm", "72118.htm", "72119.htm",
            "72120.htm", "72121.htm", "72122.htm", "72392.htm", "72393.htm", "72394.htm", "72395.htm",
            "72396.htm", "72397.htm", "72398.htm", "72399.htm", "72400.htm", "72401.htm", "72629.htm",
            "72630.htm", "72631.htm", "72632.htm", "72633.htm", "72634.htm", "72635.htm", "72636.htm",
            "72637.htm", "72932.htm", "72933.htm", "72934.htm", "72935.htm", "72936.htm", "72938.htm",
            "72939.htm", "72940.htm", "73683.htm", "73684.htm", "73685.htm", "73686.htm", "73687.htm",
            "73688.htm", "73689.htm", "73690.htm", "73691.htm", "73875.htm", "73876.htm", "73877.htm",
            "73878.htm", "73879.htm", "73880.htm", "73881.htm", "73882.htm", "73883.htm", "73884.htm",
            "74167.htm", "74168.htm", "74169.htm", "74170.htm", "74171.htm", "74172.htm", "74173.htm",
            "74174.htm", "74175.htm", "74176.htm", "74449.htm", "74450.htm", "74451.htm", "74452.htm",
            "74453.htm", "74454.htm", "74455.htm", "74456.htm", "74457.htm", "74744.htm", "74745.htm",
            "74746.htm", "74747.htm", "74748.htm", "74749.htm", "74750.htm", "74751.htm", "74752.htm","72937.htm","73435.htm",
            '73434.htm', '73436.htm', '73430.htm', '73438.htm', '73437.htm', '73431.htm', '73432.htm', '73433.htm'
        }
        self._run_search_test(query_str, expected_doc_ids)  # , debug_query=True)

    def test_changement_climatique_apres_29092011(self):
        query_str = "Je cherche les articles sur le changement et climatique publiés après 29/09/2011"
        expected_doc_ids = {
            "67939.htm", "68278.htm", "68283.htm", "68389.htm", "68645.htm", "68882.htm", "69182.htm",
            "69533.htm", "69535.htm", "69811.htm", "69814.htm", "69816.htm", "69817.htm", "70745.htm",
            "70916.htm", "70920.htm", "71363.htm", "71617.htm", "71621.htm", "71837.htm", "71838.htm",
            "73183.htm", "73434.htm", "73688.htm", "73877.htm", "73880.htm", "75458.htm", "75463.htm",
            "76213.htm", "67803.htm", "67794.htm"
        }
        self._run_search_test(query_str, expected_doc_ids)  # , debug_query=True)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
