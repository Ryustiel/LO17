import json
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from openai import OpenAI

# --- Définition du Schéma de Sortie (Structure Pydantic) ---
class StructuredQuery(BaseModel):
    """
    Représentation structurée d'une requête de recherche d'articles,
    extraite d'une requête en langage naturel.
    """
    keywords: Optional[List[str]] = Field(
        description="Liste des mots-clés, sujets, thèmes ou entités nommées (personnes, lieux, organisations) principaux à rechercher dans le contenu des articles. Tous les termes doivent être présents (logique ET implicite), sauf si l'instruction 'OU' est explicitement utilisée dans la requête pour certains termes."
    )
    keywords_operator: Optional[Literal['AND', 'OR']] = Field(
        description="Opérateur logique à appliquer entre les éléments de la liste 'keywords'. Utiliser 'OR' si la requête contient des alternatives claires comme 'A ou B'."
    )
    rubriques: Optional[List[str]] = Field(
        description="Liste des rubriques ou sections spécifiques où chercher les articles. La recherche s'effectue dans L'UNE de ces rubriques (logique OU)."
    )
    excluded_keywords: Optional[List[str]] = Field(
        description="Liste des mots-clés ou sujets explicitement exclus de la recherche (ex: 'pas X', 'sauf Y', 'sans Z')."
    )
    excluded_rubriques: Optional[List[str]] = Field(
        description="Liste des rubriques explicitement exclues de la recherche."
    )
    date_start: Optional[str] = Field(
        description="Date de début (inclusive) de la période de recherche. Formats préférés: AAAA-MM-JJ, AAAA-MM, AAAA. Interpréter 'après X', 'depuis X', 'à partir de X'. Pour 'en AAAA', utiliser AAAA-01-01."
    )
    date_end: Optional[str] = Field(
        description="Date de fin (inclusive) de la période de recherche. Formats préférés: AAAA-MM-JJ, AAAA-MM, AAAA. Interpréter 'avant X', 'jusqu'à X'. Pour 'en AAAA', utiliser AAAA-12-31."
    )
    excluded_date_periods: Optional[List[str]] = Field(
        description="Liste des périodes spécifiques à EXCLURE de la recherche, même si elles tombent dans l'intervalle [date_start, date_end]. Formats: 'AAAA-MM-JJ/AAAA-MM-JJ', 'AAAA-MM', 'AAAA'. Ex: ['2012-06-01/2012-06-30', '2013-12']."
    )
    title_contains: Optional[List[str]] = Field(
        description="Liste de mots ou termes spécifiques qui doivent impérativement apparaître dans le titre de l'article (logique ET)."
    )
    has_image: Optional[bool] = Field(
        description="Booléen indiquant si l'article doit obligatoirement contenir une image (true) ou non (false/null)."
    )
    target_info: Literal['articles', 'rubriques'] = Field(
        description="Spécifie le type d'information principal demandé par l'utilisateur. 'articles' pour une liste d'articles (défaut), 'rubriques' si la question porte spécifiquement sur les rubriques contenant certains sujets."
    )

# 2. Initialize OpenAI Client
try:
    client = OpenAI(
        base_url="https://ia.beta.utc.fr/api", api_key=""
    )
    print(f"OpenAI client initialized (targeting base_url: {client.base_url}).")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    exit()

# 3. Define System Prompt
system_prompt_content = """
Instruction: Analyse la requête utilisateur suivante pour interroger une archive d'articles nommée ADIT. Extrais les critères de recherche pertinents.
Règles d'interprétation pour extraire les informations:
*   Le but est de générer une requête structurée pour une base de données.
*   Combine les différents types de critères (keywords, rubriques, date, titre, image) avec un 'ET' logique implicite, sauf indication contraire.
*   Si la requête utilise 'ou', 'soit...soit' pour des alternatives (ex: "articles sur A ou B", "rubrique X ou Y"), place ces alternatives ensemble dans la liste correspondante (keywords ou rubriques). S'il y a plusieurs mots-clés et que 'ou' est utilisé entre eux, utilise 'OR' pour keywords_operator. Sinon, utilise 'AND' (défaut).
*   Si la requête utilise des négations comme 'pas', 'sauf', 'sans', 'ne...pas', utilise les champs excluded_keywords ou excluded_rubriques pour ces termes exclus.
*   Interprète attentivement les expressions de date et de période : 'entre J1 et J2', 'après J', 'avant J', 'depuis AAAA', 'à partir de AAAA', 'en AAAA', 'le mois de M AAAA', 'l'année AAAA'. Détermine date_start et date_end. Normalise les dates au format AAAA-MM-JJ si possible, sinon AAAA-MM ou AAAA. Si seule une année est donnée (ex: 'en 2012'), utilise AAAA-01-01 pour date_start et AAAA-12-31 pour date_end. Pour 'après JJ/MM/AAAA', détermine la date de début appropriée (par exemple, le jour suivant ou le jour même selon l'usage commun). Pour 'à partir de AAAA', date_start est AAAA-01-01. Pour 'mois de Juin 2013', date_start=2013-06-01, date_end=2013-06-30.
*   Si des mots spécifiques sont requis explicitement dans le _titre_ (ex: "titre contient X", "dont le titre traite de Y"), utilise le champ title_contains. Ne mets pas ces mots dans keywords sauf s'ils sont aussi des sujets généraux.
*   Si la présence d'une _image_ est explicitement mentionnée comme requise ("avec image", "contenant une image"), règle has_image à true. Sinon, laisse-le à null ou false.
*   Si la question principale de l'utilisateur est de savoir "quelles rubriques" contiennent quelque chose (ex: "Dans quelles rubriques trouve-t-on..."), règle target_info à 'rubriques'. Sinon, laisse la valeur par défaut 'articles'.
*   Ignore les formules de politesse ("Je voudrais", "Afficher", "Donner", "Chercher", etc.) et concentre-toi sur les critères de recherche.
*   Si aucun critère d'un certain type n'est trouvé, l'outil omettra le champ correspondant ou le laissera à null.
*   Si la requête spécifie explicitement une EXCLUSION de période temporelle (ex: 'mais pas en juin', 'sauf décembre 2012', 'hormis la semaine du X au Y'), identifie cette période et ajoute-la à la liste excluded_date_periods. Essaie de normaliser au format 'AAAA-MM-JJ/AAAA-MM-JJ' si possible, sinon 'AAAA-MM' ou 'AAAA'. Par exemple, 'pas en juin 2012' devrait devenir '2012-06'. 'entre 2012 et 2014 sauf l'été 2013' pourrait générer date_start='2012-01-01', date_end='2014-12-31', excluded_date_periods=['2013-06-21/2013-09-22'].

Extrais les informations et structure-les en utilisant le schéma fourni. Ne génère que la structure de données demandée.
"""

# --- Fonction de Traitement de la Requête avec SDK OpenAI ---
def process_query_to_structured_openai(natural_query: str) -> Optional[dict]:
    """
    Prend une requête en langage naturel, l'envoie au client OpenAI
    utilisant responses.parse avec text_format=StructuredQuery
    pour obtenir directement un objet Pydantic.
    Retourne le résultat sous forme de dictionnaire (avec exclude_none appliqué).
    """
    try:
        messages = [
            {"role": "system", "content": system_prompt_content},
            {"role": "user", "content": natural_query}
        ]

        # Appel à l'API OpenAI pour obtenir une sortie structurée
        response = client.beta.chat.completions.parse(
            model="mistral-small3.1:latest",
            messages=messages,
            response_format=StructuredQuery
        )

        result_pydantic: StructuredQuery = response.choices[0].message.parsed

        if result_pydantic:
            return result_pydantic.model_dump(exclude_none=True)
        else:
            print(f"\n`response.output_parsed` est vide pour la requête: {natural_query}")
            return None

    except Exception as e:
        print(f"\nErreur lors de l'appel à client.responses.parse ou du parsing : {e}")
        return None

# --- Boucle Principale d'Interaction / Bloc de Test ---
if __name__ == "__main__":
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
        "Articles dont la rubrique est \"Horizon Enseignement\" mais qui ne parlent pas d’ingénieurs.", # Attention aux guillemets
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

    print(f"Début des tests sur {len(test_queries)} requêtes avec le SDK OpenAI direct...")
    successful_parses = 0
    failed_parses = 0

    # Boucle sur chaque requête de test
    for i, natural_query in enumerate(test_queries):
        print(f"\n--- Test {i+1}/{len(test_queries)} ---")
        print(f"Requête d'entrée: \"{natural_query}\"")
        if not natural_query:
            print("Requête vide, ignorée.")
            continue

        print("Traitement de la requête avec SDK OpenAI client.responses.parse...")
        # Appel de la nouvelle fonction
        structured_result = process_query_to_structured_openai(natural_query)

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
