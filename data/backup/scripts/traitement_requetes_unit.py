# traitements_requetes_unit.py
import unittest
import json
from traitement_requetes import QueryParser


class TestProcessQuery(unittest.TestCase):
    maxDiff = None  # Pour voir les différences complètes en cas d'échec

    def assertQuery(self, query_input, expected_output):
        """Helper method to run a query and assert its output."""
        parser = QueryParser()
        actual_output = parser.process_query(query_input)

        # Trier les listes de termes pour une comparaison stable
        for key in ["content_terms", "title_terms", "rubric_terms", "negated_content_terms", "negated_rubric_terms"]:
            if key in actual_output and actual_output[key]:
                actual_output[key].sort()
            if key in expected_output and expected_output[key]:
                expected_output[key].sort()

        # Trier date_conditions pour une comparaison stable
        # Convertir chaque dictionnaire en une chaîne JSON triée par clé pour le tri
        if "date_conditions" in actual_output and actual_output["date_conditions"]:
            actual_output["date_conditions"].sort(key=lambda x: json.dumps(x, sort_keys=True))
        if "date_conditions" in expected_output and expected_output["date_conditions"]:
            expected_output["date_conditions"].sort(key=lambda x: json.dumps(x, sort_keys=True))

        # Trier return_fields si c'est une liste
        if "return_fields" in actual_output and isinstance(actual_output["return_fields"], list):
            actual_output["return_fields"].sort()
        if "return_fields" in expected_output and isinstance(expected_output["return_fields"], list):
            expected_output["return_fields"].sort()

        self.assertEqual(actual_output, expected_output)

    def test_requete_01_ok(self):
        query = "Afficher la liste des articles qui parlent des systèmes embarqués dans la rubrique Horizons Enseignement."
        expected = {
            "content_terms": ["systèmes embarqués"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["horizons enseignement"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_02_ok(self):
        query = "Je voudrais les articles qui parlent de cuisine moléculaire."
        expected = {
            "content_terms": ["cuisine moléculaire"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_03_ok(self):
        query = "Quels sont les articles sur la réalité virtuelle ?"
        expected = {
            "content_terms": ["réalité virtuelle"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_04_ok(self):
        query = "Je voudrais les articles qui parlent d’airbus ou du projet Taxibot."
        expected = {
            "content_terms": ["airbus", "projet taxibot"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_05_ok(self):
        query = "Je voudrais les articles qui parlent du tennis."
        expected = {
            "content_terms": ["tennis"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_06_ok(self):
        query = "Je voudrais les articles traitant de la Lune."
        expected = {
            "content_terms": ["lune"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_07_ok(self):
        query = "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les Etats-Unis ?"
        expected = {
            "content_terms": ["etats-unis"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "range",
                    "from": "2013-03-03",
                    "to": "2013-05-04"
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_08_ok(self):
        query = "Afficher les articles de la rubrique en direct des laboratoires."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["en direct des laboratoires"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_09_ok(self):
        query = "Je veux les articles de la rubrique Focus parlant d’innovation."
        expected = {
            "content_terms": ["innovation"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["focus"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_10_ok(self):
        query = "Quels sont les articles parlant de la Russie ou du Japon ?"
        expected = {
            "content_terms": ["japon", "russie"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_11_ok(self):
        query = "Je voudrais les articles de 2011 sur l’enseignement."
        expected = {
            "content_terms": ["enseignement"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "year",
                    "year": 2011
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_12_ok(self):
        query = "Je voudrais les articles dont le titre contient le mot chimie."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["chimie"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_13_ok(self):
        query = "Je veux les articles de 2014 et de la rubrique Focus et parlant de la santé."
        expected = {
            "content_terms": ["santé"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["focus"],
            "rubric_operator": None,
            "date_conditions": [{"type": "year", "year": 2014}],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_14_ok(self):
        query = "Je souhaite les rubriques des articles parlant de nutrition ou de vins."
        expected = {
            "content_terms": ["nutrition", "vins"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": ["rubric"],
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_15_ok(self):
        query = "Je cherche les recherches sur l’aéronautique."
        expected = {
            "content_terms": ["aéronautique"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_16_ok(self):
        query = "Article traitant des Serious Game et de la réalité virtuelle."
        expected = {
            "content_terms": ["réalité virtuelle", "serious game"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_17_ok(self):
        query = "Quels sont les articles traitant d’informatique ou de reseaux."
        expected = {
            "content_terms": ["informatique", "reseaux"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_18_ok(self):
        query = "je voudrais les articles de la rubrique Focus mentionnant un laboratoire."
        expected = {
            "content_terms": ["laboratoire"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["focus"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_19_ok(self):
        query = "quels sont les articles publiés au mois de novembre 2011 portant sur de la recherche."
        expected = {
            "content_terms": ["recherche"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "month_year",
                    "month": 11,
                    "year": 2011
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_20_ok(self):
        query = "je veux des articles sur la plasturgie."
        expected = {
            "content_terms": ["plasturgie"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_21_ok(self):
        query = "quels articles portent à la fois sur les nanotechnologies et les microsatellites."
        expected = {
            "content_terms": ["microsatellites", "nanotechnologies"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_22_ok(self):
        query = "je voudrais les articles liés à la recherche scientifique publiés en Février 2010."
        expected = {
            "content_terms": ["recherche scientifique"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "month_year",
                    "month": 2,
                    "year": 2010
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_23_ok(self):
        query = "Donner les articles qui parlent d’apprentissage et de la rubrique Horizons Enseignement."
        expected = {
            "content_terms": ["apprentissage"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["horizons enseignement"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_24_ok(self):
        query = "Chercher les articles dans le domaine industriel et datés à partir de 2012."
        expected = {
            "content_terms": ["industriel"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "after_year",
                    "year": 2012
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_25_ok(self):
        query = "Nous souhaitons obtenir les articles du mois de Juin 2013 et parlant du cerveau."
        expected = {
            "content_terms": ["cerveau"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "month_year",
                    "month": 6,
                    "year": 2013
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_26_ok(self):
        query = "Rechercher tous les articles sur le CNRS et l’innovation à partir de 2013."
        expected = {
            "content_terms": ["cnrs", "innovation"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "after_year",
                    "year": 2013
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_27_ok(self):
        query = "Je cherche des articles sur les avions."
        expected = {
            "content_terms": ["avions"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_28_ok(self):
        query = "Donner les articles qui portent sur l’alimentation de l’année 2013."
        expected = {
            "content_terms": ["alimentation"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "year",
                    "year": 2013
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_29_ok(self):
        query = "Articles dont le titre traite du Tara Oceans Polar Circle."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["tara oceans polar circle"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_30_ok(self):
        query = "Je veux des articles parlant de smartphones."
        expected = {
            "content_terms": ["smartphones"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_31_ok(self):
        query = "Quels sont les articles parlant de projet européen de l’année 2014 ?"
        expected = {
            "content_terms": ["projet européen"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "year",
                    "year": 2014
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_32_ok(self):
        query = "Afficher les articles de la rubrique A lire."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["a lire"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_33_ok(self):
        query = "Je veux les articles parlant de Neurobiologie."
        expected = {
            "content_terms": ["neurobiologie"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_34_ok(self):
        query = "Quels sont les articles possédant le mot France ?"
        expected = {
            "content_terms": ["france"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_35_ok(self):
        query = "Articles écrits en Décembre 2012 qui parlent de l’environnement ?"
        expected = {
            "content_terms": ["environnement"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "month_year",
                    "month": 12,
                    "year": 2012
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_36_ok(self):
        query = "Quels sont les articles contenant les mots voitures et électrique ?"
        expected = {
            "content_terms": ["électrique", "voitures"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_37_ok(self):
        query = "Je voudrais les articles avec des images dont le titre contient le mot croissance."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["croissance"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": True,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_38_ok(self):
        query = "Quels sont les articles qui parlent de microbiologie ?"
        expected = {
            "content_terms": ["microbiologie"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_39_ok(self):
        query = "J’aimerais la liste des articles écrits après janvier 2014 et qui parlent d’informatique ou de télécommunications."
        expected = {
            "content_terms": ["informatique", "télécommunications"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [{"type": "after", "date": "2014-01-01"}],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_40_ok(self):
        query = "Je veux les articles de 2012 qui parlent de l’écologie en France."
        expected = {
            "content_terms": ["écologie en france"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "year",
                    "year": 2012
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_41_ok(self):
        query = "Quels articles parlent de réalité virtuelle ?"
        expected = {
            "content_terms": ["réalité virtuelle"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_42_ok(self):
        query = "Dans quelles rubriques trouve-t-on des articles sur l’alimentation ?"
        expected = {
            "content_terms": ["alimentation"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": ["rubric"],
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_43_ok(self):
        query = "Liste des articles qui parlent soit du CNRS, soit des grandes écoles, mais pas de Centrale Paris."
        expected = {
            "content_terms": ["cnrs", "grandes écoles"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": ["centrale paris"],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_44_ok(self):
        query = "J’aimerais un article qui parle de biologie et qui date d’après le 2 juillet 2012 ?"
        expected = {
            "content_terms": ["biologie"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [{"type": "after", "date": "2012-07-02"}],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_45_ok(self):
        query = "Quels sont les articles qui parlent d’innovations technologiques ?"
        expected = {
            "content_terms": ["innovations technologiques"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_46_ok(self):
        query = "Je cherche les articles dont le titre contient le mot performants."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["performants"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_47_ok(self):
        query = "Je voudrais tout les articles provenant de la rubrique événement et contenant le mot congres dans le titre."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["congres"],
            "title_operator": None,
            "rubric_terms": ["événement"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_48_ok(self):
        query = "Je cherche les articles à propos des fleurs ou des arbres."
        expected = {
            "content_terms": ["arbres", "fleurs"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_49_ok(self):
        query = "Je souhaites avoir tout les articles donc la rubrique est focus ou Actualités Innovations et qui contiennent les mots chercheurs et paris."
        expected = {
            "content_terms": ["chercheurs", "paris"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["actualités innovations", "focus"],
            "rubric_operator": "OR",
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_50_ok(self):
        query = "Je veux les articles qui parlent du sénégal."
        expected = {
            "content_terms": ["sénégal"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_51_ok(self):
        query = "Je voudrais les articles qui parlent d’innovation."
        expected = {
            "content_terms": ["innovation"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_52_ok(self):
        query = "je voudrais les articles dont le titre contient le mot europe."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["europe"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_53_ok(self):
        query = "je voudrais les articles qui contiennent les mots Ecole et Polytechnique."
        expected = {
            "content_terms": ["ecole", "polytechnique"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_54_ok(self):
        query = "Je cherche les articles provenant de la rubrique en direct des laboratoires."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["en direct des laboratoires"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_55_ok(self):
        query = "Je voudrais les articles qui datent du 1 décembre 2012 et dont la rubrique est Actualités Innovations."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["actualités innovations"],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "exact_date",
                    "date": "2012-12-01"
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_56_ok(self):
        query = "Dans quels articles Laurent Lagrost est-il cité ?"
        expected = {
            "content_terms": ["laurent lagrost"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_57_ok(self):
        query = "Quels articles évoquent la ville de Grenoble ?"
        expected = {
            "content_terms": ["ville de grenoble"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_58_ok(self):
        query = "Articles parlant de drones."
        expected = {
            "content_terms": ["drones"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_59_ok(self):
        query = "Articles parlant de molécules."
        expected = {
            "content_terms": ["molécules"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_60_ok(self):
        query = "Articles contenant une image."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": True,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_61_ok(self):
        query = "Articles parlant d’université."
        expected = {
            "content_terms": ["université"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_62_ok(self):
        query = "Lister tous les articles dont la rubrique est Focus et qui ont des images."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["focus"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": True,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_63_ok(self):
        query = "Quels sont les articles dont le titre évoque la recherche ?"
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["recherche"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_64_ok(self):
        query = "Articles dont la rubrique est \"Horizon Enseignement\" mais qui ne parlent pas d’ingénieurs."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["horizon enseignement"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": ["ingénieurs"],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_65_ok(self):
        query = "Tous les articles dont la rubrique est \"En direct des laboratoires\" ou \"Focus\" et qui évoquent la médecine."
        expected = {
            "content_terms": ["médecine"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["en direct des laboratoires", "focus"],
            "rubric_operator": "OR",
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_66_ok(self):
        query = "Je voudrais tous les bulletins écrits entre 2012 et 2013 mais pas au mois de juin."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {"exclude_month": 6},
                {"type": "year_range", "from": 2012, "to": 2013}
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_67_ok(self):
        query = "Quels sont les articles dont le titre contient le terme \"marché\" et le mot \"projet\" ?"
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["marché", "projet"],
            "title_operator": "AND",
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_68_ok(self):
        query = "je voudrais les articles dont le titre contient le mot 3D."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["3d"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_69_ok(self):
        query = "je veux voir les articles de la rubrique Focus et publiés entre 30/08/2011 et 29/09/2011."
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["focus"],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "range",
                    "from": "2011-08-30",
                    "to": "2011-09-29"
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_70_ok(self):
        query = "Je cherche les articles sur le Changement climatique publiés après 29/09/2011."
        expected = {
            "content_terms": ["changement climatique"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "after",
                    "date": "2011-09-29"
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_71_ok(self):
        query = "Quels articles parlent d’aviation et ont été publiés en 2015 ?"
        expected = {
            "content_terms": ["aviation"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "year",
                    "year": 2015
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_72_ok(self):
        query = "Quels sont les articles de la rubrique évènement qui parlent de la ville de Paris ?"
        expected = {
            "content_terms": ["ville de paris"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["événement"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_73_ok(self):
        query = "Je veux les articles impliquant le CNRS et qui parlent de chimie."
        expected = {
            "content_terms": ["chimie", "cnrs"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_74_ok(self):
        query = "Trouver les articles qui mentionnent Fink."
        expected = {
            "content_terms": ["fink"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_75_ok(self):
        query = "Quels articles parlent de la France et de l’Allemagne ?"
        expected = {
            "content_terms": ["allemagne", "france"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_76_ok(self):
        query = "Je veux les articles parlant de l’Argentine ou du Brésil."
        expected = {
            "content_terms": ["argentine", "brésil"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_77_ok(self):
        query = "Je veux les articles qui parlent de l’hydravion."
        expected = {
            "content_terms": ["hydravion"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_78_ok(self):
        query = "Je veux les articles qui parlent du fauteuil roulant et qui ont pour rubrique Actualité Innovation."
        expected = {
            "content_terms": ["fauteuil roulant"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": ["actualité innovation"],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_79_ok(self):
        query = "Je veux les articles qui sont écrits en 2012 et parlent du « chrono-environnement »."
        expected = {
            "content_terms": ["chrono-environnement"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [
                {
                    "type": "year",
                    "year": 2012
                }
            ],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_80_ok(self):
        query = "Quels sont les articles qui parlent des robots et des chirurgiens ?"
        expected = {
            "content_terms": ["chirurgiens", "robots"],
            "content_operator": "AND",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_81_ok(self):
        query = "Je veux les articles qui parlent des systmes embarqués et non pas la robotique."
        expected = {
            "content_terms": ["systmes embarqués"],
            "content_operator": None,
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": ["robotique"],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_82_ok(self):
        query = "Je cherche les articles qui parlent des alimentations ou des agricultures."
        expected = {
            "content_terms": ["agricultures", "alimentations"],
            "content_operator": "OR",
            "title_terms": [],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)

    def test_requete_83_ok(self):
        query = "Quels sont les articles dont le titre contient le mot histoire ?"
        expected = {
            "content_terms": [],
            "content_operator": None,
            "title_terms": ["histoire"],
            "title_operator": None,
            "rubric_terms": [],
            "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "negated_rubric_terms": [],
            "has_image": False,
            "return_fields": None,
            "raw_query": query
        }
        self.assertQuery(query, expected)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)