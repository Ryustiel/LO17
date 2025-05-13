import json
from typing import List, Optional, Literal

# --- LangChain / OpenAI Imports ---
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException # For specific error handling if needed

# 2. Initialize OpenAI Model (Using LangChain)
try:
    model = ChatOpenAI(base_url="https://ia.beta.utc.fr/api",temperature=0, model="mistral-small3.1:latest", api_key="")
    print(f"LangChain ChatOpenAI model initialized ({model.model_name}).")
except Exception as e:
    print(f"Error initializing ChatOpenAI model: {e}")
    print("Please check your API key and OpenAI account status.")
    exit()

# --- Définition du Schéma de Sortie (Structure Pydantic) ---
class StructuredQuery(BaseModel):
    """
    Représentation structurée d'une requête de recherche d'articles,
    extraite d'une requête en langage naturel.
    """
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Liste des mots-clés, sujets, thèmes ou entités nommées (personnes, lieux, organisations) principaux à rechercher dans le contenu des articles. Tous les termes doivent être présents (logique ET implicite), sauf si l'instruction 'OU' est explicitement utilisée dans la requête pour certains termes."
    )
    keywords_operator: Optional[Literal['AND', 'OR']] = Field(
        default='AND', # Par défaut 'ET' pour les mots-clés
        description="Opérateur logique à appliquer entre les éléments de la liste 'keywords'. Utiliser 'OR' si la requête contient des alternatives claires comme 'A ou B'."
    )
    rubriques: Optional[List[str]] = Field(
        default=None,
        description="Liste des rubriques ou sections spécifiques où chercher les articles. La recherche s'effectue dans L'UNE de ces rubriques (logique OU)."
    )
    excluded_keywords: Optional[List[str]] = Field(
        default=None,
        description="Liste des mots-clés ou sujets explicitement exclus de la recherche (ex: 'pas X', 'sauf Y', 'sans Z')."
    )
    excluded_rubriques: Optional[List[str]] = Field(
        default=None,
        description="Liste des rubriques explicitement exclues de la recherche."
    )
    date_start: Optional[str] = Field(
        default=None,
        description="Date de début (inclusive) de la période de recherche. Formats préférés: AAAA-MM-JJ, AAAA-MM, AAAA. Interpréter 'après X', 'depuis X', 'à partir de X'. Pour 'en AAAA', utiliser AAAA-01-01."
    )
    date_end: Optional[str] = Field(
        default=None,
        description="Date de fin (inclusive) de la période de recherche. Formats préférés: AAAA-MM-JJ, AAAA-MM, AAAA. Interpréter 'avant X', 'jusqu'à X'. Pour 'en AAAA', utiliser AAAA-12-31."
    )
    excluded_date_periods: Optional[List[str]] = Field(
        default=None,
        description="Liste des périodes spécifiques à EXCLURE de la recherche, même si elles tombent dans l'intervalle [date_start, date_end]. Formats: 'AAAA-MM-JJ/AAAA-MM-JJ', 'AAAA-MM', 'AAAA'. Ex: ['2012-06-01/2012-06-30', '2013-12']."
    )
    title_contains: Optional[List[str]] = Field(
        default=None,
        description="Liste de mots ou termes spécifiques qui doivent impérativement apparaître dans le titre de l'article (logique ET)."
    )
    has_image: Optional[bool] = Field(
        default=None,
        description="Booléen indiquant si l'article doit obligatoirement contenir une image (true) ou non (false/null)."
    )
    target_info: Literal['articles', 'rubriques'] = Field(
        default='articles',
        description="Spécifie le type d'information principal demandé par l'utilisateur. 'articles' pour une liste d'articles (défaut), 'rubriques' si la question porte spécifiquement sur les rubriques contenant certains sujets."
    )

# 3. Set up a parser and inject instructions into the prompt template.
parser = PydanticOutputParser(pydantic_object=StructuredQuery)

# 4. Create the Prompt Template
prompt_template_string = """
Instruction: Analyse la requête utilisateur suivante pour interroger une archive d'articles nommée ADIT. Extrais les critères de recherche pertinents et structure-les strictement en JSON conformément au schéma JSON fourni ci-dessous.

Règles d'interprétation pour remplir le schéma:
- Le but est de générer une requête structurée pour une base de données.
- Combine les différents types de critères (keywords, rubriques, date, titre, image) avec un 'ET' logique implicite, sauf indication contraire.
- Si la requête utilise 'ou', 'soit...soit' pour des alternatives (ex: "articles sur A ou B", "rubrique X ou Y"), place ces alternatives ensemble dans la liste correspondante (`keywords` ou `rubriques`). S'il y a plusieurs mots-clés et que 'ou' est utilisé entre eux, utilise 'OR' pour `keywords_operator`. Sinon, utilise 'AND' (défaut).
- Si la requête utilise des négations comme 'pas', 'sauf', 'sans', 'ne...pas', utilise les champs `excluded_keywords` ou `excluded_rubriques` pour ces termes exclus.
- Interprète attentivement les expressions de date et de période : 'entre J1 et J2', 'après J', 'avant J', 'depuis AAAA', 'à partir de AAAA', 'en AAAA', 'le mois de M AAAA', 'l'année AAAA'. Détermine `date_start` et `date_end`. Normalise les dates au format AAAA-MM-JJ si possible, sinon AAAA-MM ou AAAA. Si seule une année est donnée (ex: 'en 2012'), utilise AAAA-01-01 pour `date_start` et AAAA-12-31 pour `date_end`. Pour 'après JJ/MM/AAAA', date_start est JJ/MM/AAAA (assumant inclusif, ou +1 jour si explicitement exclusif). Pour 'à partir de AAAA', date_start est AAAA-01-01. Pour 'mois de Juin 2013', date_start=2013-06-01, date_end=2013-06-30.
- Si des mots spécifiques sont requis explicitement dans le *titre* (ex: "titre contient X", "dont le titre traite de Y"), utilise le champ `title_contains`. Ne mets pas ces mots dans `keywords` sauf s'ils sont aussi des sujets généraux.
- Si la présence d'une *image* est explicitement mentionnée comme requise ("avec image", "contenant une image"), règle `has_image` à `true`. Sinon, laisse-le à `null` ou `false`.
- Si la question principale de l'utilisateur est de savoir "quelles rubriques" contiennent quelque chose (ex: "Dans quelles rubriques trouve-t-on..."), règle `target_info` à 'rubriques'. Sinon, laisse la valeur par défaut 'articles'.
- Ignore les formules de politesse ("Je voudrais", "Afficher", "Donner", "Chercher", etc.) et concentre-toi sur les critères de recherche.
- Si aucun critère d'un certain type n'est trouvé, omet simplement le champ correspondant ou laisse-le à `null` dans le JSON final.
- Si la requête spécifie explicitement une EXCLUSION de période temporelle (ex: 'mais pas en juin', 'sauf décembre 2012', 'hormis la semaine du X au Y'), identifie cette période et ajoute-la à la liste `excluded_date_periods`. Essaie de normaliser au format 'AAAA-MM-JJ/AAAA-MM-JJ' si possible, sinon 'AAAA-MM' ou 'AAAA'. Par exemple, 'pas en juin 2012' devrait devenir '2012-06'. 'entre 2012 et 2014 sauf l'été 2013' pourrait générer date_start='2012-01-01', date_end='2014-12-31', excluded_date_periods=['2013-06-21/2013-09-22'].

{format_instructions}

Requête utilisateur: "{query}"

Génère UNIQUEMENT le JSON structuré correspondant à la requête, sans aucun texte ou explication avant ou après. Ne retourne que l'objet JSON lui-même.
"""

prompt = PromptTemplate(
    template=prompt_template_string,
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# 5. Create the LangChain Chain
chain = prompt | model | parser
print("LangChain chain created (prompt | model | parser).")

# --- Fonction de Traitement de la Requête (Modifiée pour LangChain) ---

def process_query_to_structured(natural_query: str) -> Optional[dict]:
    """
    Prend une requête en langage naturel, l'envoie à la chaîne LangChain
    (qui utilise OpenAI et JsonOutputParser) pour obtenir une sortie JSON
    structurée selon le modèle Pydantic StructuredQuery.
    Retourne le résultat sous forme de dictionnaire.
    """
    try:
        result_dict = chain.invoke({"query": natural_query})
        try:
            validated_model = StructuredQuery.model_validate(result_dict)
            return validated_model.model_dump(exclude_none=True)
        except Exception as dump_err:
            print(f"\nWarning: Erreur lors de la finalisation Pydantic après parsing réussi.")
            print(f"Erreur de validation/dump finale: {dump_err}")
            print(f"Dictionnaire brut du parser: {result_dict}")
            return result_dict

    except OutputParserException as parse_err:
        print(f"\nErreur: Problème lors du parsing/validation de la sortie LLM.")
        if hasattr(parse_err, 'llm_output'):
             print(f"Sortie brute du LLM ayant causé l'erreur:\n---\n{parse_err.llm_output}\n---")
        elif hasattr(parse_err, 'observation'):
             print(f"Observation du parser:\n---\n{parse_err.observation}\n---")
        else:
             print(f"Erreur de parsing: {parse_err}")

        return None
    except Exception as e:
        print(f"\nErreur inattendue lors de l'exécution de la chaîne LangChain : {e}")
        return None


# --- Boucle Principale d'Interaction / Bloc de Test ---
if __name__ == "__main__":
    # Liste des requêtes à tester (copiée depuis l'annexe)
    test_queries = [
        "Afficher la liste des articles qui parlent des systèmes embarqués dans la rubrique Horizons Enseignement.",
        "Je voudrais les articles qui parlent de cuisine moléculaire.",
        "Quels sont les articles sur la réalité virtuelle ?",
        "Je voudrais les articles qui parlent d’airbus ou du projet Taxibot.",
        "Je voudrais les articles qui parlent du tennis.",
        "Je voudrais les articles traitant de la Lune.",
        "Quels sont les articles parus entre le 3 mars 2013 et le 4 mai 2013 évoquant les Etats-Unis ?",
        "Afficher les articles de la rubrique en direct des laboratoires.",
        "Je veux les articles de la rubrique Focus parlant d’innovation.",
        "Quels sont les articles parlant de la Russie ou du Japon ?",
        "Je voudrais les articles de 2011 sur l’enseignement.",
        "Je voudrais les articles dont le titre contient le mot chimie.",
        "Je veux les articles de 2014 et de la rubrique Focus et parlant de la santé.",
        "Je souhaite les rubriques des articles parlant de nutrition ou de vins.",
        "Je cherche les recherches sur l’aéronautique.",
        "Article traitant des Serious Game et de la réalité virtuelle.",
        "Quels sont les articles traitant d’informatique ou de reseaux.",
        "je voudrais les articles de la rubrique Focus mentionnant un laboratoire.",
        "quels sont les articles publiés au mois de novembre 2011 portant sur de la recherche.",
        "je veux des articles sur la plasturgie.",
        "quels articles portent à la fois sur les nanotechnologies et les microsatellites.",
        "je voudrais les articles liés à la recherche scientifique publiés en Février 2010.",
        "Donner les articles qui parlent d’apprentissage et de la rubrique Horizons Enseignement.",
        "Chercher les articles dans le domaine industriel et datés à partir de 2012.",
        "Nous souhaitons obtenir les articles du mois de Juin 2013 et parlant du cerveau.",
        "Rechercher tous les articles sur le CNRS et l’innovation à partir de 2013.",
        "Je cherche des articles sur les avions.",
        "Donner les articles qui portent sur l’alimentation de l’année 2013.",
        "Articles dont le titre traite du Tara Oceans Polar Circle.",
        "Je veux des articles parlant de smartphones.",
        "Quels sont les articles parlant de projet européen de l’année 2014 ?",
        "Afficher les articles de la rubrique A lire.",
        "Je veux les articles parlant de Neurobiologie.",
        "Quels sont les articles possédant le mot France ?",
        "Articles écrits en Décembre 2012 qui parlent de l’environnement ?",
        "Quels sont les articles contenant les mots voitures et électrique ?",
        "Je voudrais les articles avec des images dont le titre contient le mot croissance.",
        "Quels sont les articles qui parlent de microbiologie ?",
        "J’aimerais la liste des articles écrits après janvier 2014 et qui parlent d’informatique ou de télécommunications.",
        "Je veux les articles de 2012 qui parlent de l’écologie en France.",
        "Quels articles parlent de réalité virtuelle ?",
        "Dans quelles rubriques trouve-t-on des articles sur l’alimentation ?",
        "Liste des articles qui parlent soit du CNRS, soit des grandes écoles, mais pas de Centrale Paris.",
        "J’aimerais un article qui parle de biologie et qui date d’après le 2 juillet 2012 ?",
        "Quels sont les articles qui parlent d’innovations technologiques ?",
        "Je cherche les articles dont le titre contient le mot performants.",
        "Je voudrais tout les articles provenant de la rubrique événement et contenant le mot congres dans le titre.",
        "Je cherche les articles à propos des fleurs ou des arbres.",
        "Je souhaites avoir tout les articles donc la rubrique est focus ou Actualités Innovations et qui contiennent les mots chercheurs et paris.",
        "Je veux les articles qui parlent du sénégal.",
        "Je voudrais les articles qui parlent d’innovation.",
        "je voudrais les articles dont le titre contient le mot europe.",
        "je voudrais les articles qui contiennent les mots Ecole et Polytechnique.",
        "Je cherche les articles provenant de la rubrique en direct des laboratoires.",
        "Je voudrais les articles qui datent du 1 décembre 2012 et dont la rubrique est Actualités Innovations.",
        "Dans quels articles Laurent Lagrost est-il cité ?",
        "Quels articles évoquent la ville de Grenoble ?",
        "Articles parlant de drones.",
        "Articles parlant de molécules.",
        "Articles contenant une image.",
        "Articles parlant d’université.",
        "Lister tous les articles dont la rubrique est Focus et qui ont des images.",
        "Quels sont les articles dont le titre évoque la recherche ?",
        "Articles dont la rubrique est \"Horizon Enseignement\" mais qui ne parlent pas d’ingénieurs.",
        "Tous les articles dont la rubrique est \"En direct des laboratoires\" ou \"Focus\" et qui évoquent la médecine.",
        "Je voudrais tous les bulletins écrits entre 2012 et 2013 mais pas au mois de juin.",
        "Quels sont les articles dont le titre contient le terme \"marché\" et le mot \"projet\" ?",
        "je voudrais les articles dont le titre contient le mot 3D.",
        "je veux voir les articles de la rubrique Focus et publiés entre 30/08/2011 et 29/09/2011.",
        "Je cherche les articles sur le Changement climatique publiés après 29/09/2011.",
        "Quels articles parlent d’aviation et ont été publiés en 2015 ?",
        "Quels sont les articles de la rubrique évènement qui parlent de la ville de Paris ?",
        "Je veux les articles impliquant le CNRS et qui parlent de chimie.",
        "Trouver les articles qui mentionnent Fink.",
        "Quels articles parlent de la France et de l’Allemagne ?",
        "Je veux les articles parlant de l’Argentine ou du Brésil.",
        "Je veux les articles qui parlent de l’hydravion.",
        "Je veux les articles qui parlent du fauteuil roulant et qui ont pour rubrique Actualité Innovation.",
        "Je veux les articles qui sont écrits en 2012 et parlent du « chrono-environnement ».",
        "Quels sont les articles qui parlent des robots et des chirurgiens ?",
        "Je veux les articles qui parlent des systmes embarqués et non pas la robotique.",
        "Je cherche les articles qui parlent des alimentations ou des agricultures.",
        "Quels sont les articles dont le titre contient le mot histoire ?"
    ]

    print(f"Début des tests sur {len(test_queries)} requêtes avec LangChain/OpenAI...")

    successful_parses = 0
    failed_parses = 0

    # Boucle sur chaque requête de test
    for i, natural_query in enumerate(test_queries):
        print(f"\n--- Test {i+1}/{len(test_queries)} ---")
        print(f"Requête d'entrée: \"{natural_query}\"")

        if not natural_query:
            print("Requête vide, ignorée.")
            continue

        print("Traitement de la requête avec LangChain...")
        structured_result = process_query_to_structured(natural_query)

        if structured_result:
            print("\nRequête structurée générée (JSON):")
            print(json.dumps(structured_result, indent=2, ensure_ascii=False))
            successful_parses += 1
        else:
            print("-> Impossible de générer une requête structurée pour cette entrée.")
            failed_parses += 1

    print("\n--- Fin des tests ---")
    print(f"Analyses réussies: {successful_parses}")
    print(f"Analyses échouées: {failed_parses}")