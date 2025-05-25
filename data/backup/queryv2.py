
from typing import List, Dict, Set, Optional, Literal
import pydantic, datetime

from .document import Document
from .base.inverted_index import InvertedIndex
from .base.base_query import BaseQuery

class Query(BaseQuery):
    """
    Représentation structurée d'une requête de recherche d'articles,
    extraite d'une requête en langage naturel.
    """
    content_terms: List[str] = pydantic.Field(
        default=[],
        description="Liste des mots-clés, sujets, thèmes ou entités nommées (personnes, lieux, organisations) principaux à rechercher dans le contenu des articles. Tous les termes doivent être présents (logique ET implicite), sauf si l'instruction 'OU' est explicitement utilisée dans la requête pour certains termes."
    )
    content_operator: Literal['AND', 'OR'] = pydantic.Field(
        default='AND', # Par défaut 'ET' pour les mots-clés
        description="Opérateur logique à appliquer entre les éléments de la liste 'content_terms'. Utiliser 'OR' si la requête contient des alternatives claires comme 'A ou B'."
    )
    title_terms: List[str] = pydantic.Field(
        default=[],
        description="Liste de mots ou termes spécifiques qui doivent impérativement apparaître dans le titre de l'article (logique ET)."
    )
    title_operator: Literal['AND', 'OR'] = pydantic.Field(
        default='AND', # Par défaut 'ET' pour les mots-clés
        description="Opérateur logique à appliquer entre les éléments de la liste 'title_terms'. Utiliser 'OR' si la requête contient des alternatives claires comme 'A ou B'."
    )
    rubric_terms: List[str] = pydantic.Field(
        default=[],
        description="Liste des rubric_terms ou sections spécifiques où chercher les articles. La recherche s'effectue dans L'UNE de ces rubric_terms (logique OU)."
    )
    rubric_operator: Literal['AND', 'OR'] = pydantic.Field(
        default='AND', # Par défaut 'ET' pour les mots-clés
        description="Opérateur logique à appliquer entre les éléments de la liste 'rebric_terms'. Utiliser 'OR' si la requête contient des alternatives claires comme 'A ou B'."
    )
    negated_content_terms: List[str] = pydantic.Field(
        default=[],
        description="Liste des mots-clés ou sujets explicitement exclus de la recherche (ex: 'pas X', 'sauf Y', 'sans Z')."
    )
    negated_rubric_terms: List[str] = pydantic.Field(
        default=[],
        description="Rubriques exclues. ('excluded_rubriques' dans l'ancien modèle)"
    )
    date_start: Optional[datetime.datetime] = pydantic.Field(
        default=None,
        description="Date de début (inclusive) de la période de recherche. Formats préférés: AAAA-MM-JJ, AAAA-MM, AAAA. Interpréter 'après X', 'depuis X', 'à partir de X'. Pour 'en AAAA', utiliser AAAA-01-01."
    )
    date_end: Optional[datetime.datetime] = pydantic.Field(
        default=None,
        description="Date de fin (inclusive) de la période de recherche. Formats préférés: AAAA-MM-JJ, AAAA-MM, AAAA. Interpréter 'avant X', 'jusqu'à X'. Pour 'en AAAA', utiliser AAAA-12-31."
    )
    excluded_date_periods: List[str] = pydantic.Field(
        default=[],
        description="Liste des périodes spécifiques à EXCLURE de la recherche, même si elles tombent dans l'intervalle [date_start, date_end]. Formats: 'AAAA-MM-JJ/AAAA-MM-JJ', 'AAAA-MM', 'AAAA'. Ex: ['2012-06-01/2012-06-30', '2013-12']."
    )
    has_image: bool = pydantic.Field(
        default=False,
        description="Booléen indiquant si l'article doit obligatoirement contenir une image (true) ou non (false/null)."
    )
    target_info: Literal['articles', 'rubric_terms'] = pydantic.Field(
        default='articles',
        description="Spécifie le type d'information principal demandé par l'utilisateur. 'articles' pour une liste d'articles (défaut), 'rubric_terms' si la question porte spécifiquement sur les rubric_terms contenant certains sujets."
    )

    # ========== BUILD ==========
    
    @classmethod
    def build(cls, query: str) -> 'Query':
        from .scripts.query_parser import QueryParser
        query_json: dict = QueryParser().process_query(query)
        return cls.model_validate(query_json)

    @classmethod
    def llm_build(cls, query: str) -> 'Query':
        
        from langchain_core.messages import SystemMessage
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        pydantic_query: "Query" = ChatOpenAI(
            base_url="https://ia.beta.utc.fr/api",
            temperature=0, 
            model="mistral-small3.1:latest", 
            api_key=os.getenv("UTC_API_KEY")
        ).with_structured_output(cls).invoke(
            [
                SystemMessage(content = f"""
                    Instruction: Analyse la requête utilisateur suivante pour interroger une archive d'articles nommée ADIT. Extrais les critères de recherche pertinents.

                    Règles d'interprétation pour extraire les informations:
                    - Le but est de générer une requête structurée pour une base de données.
                    - Combine les différents types de critères (content_terms, rubric_terms, date, titre, image) avec un 'ET' logique implicite, sauf indication contraire.
                    - Si la requête utilise 'ou', 'soit...soit' pour des alternatives (ex: "articles sur A ou B", "rubrique X ou Y"), place ces alternatives ensemble dans la liste correspondante (`content_terms` ou `rubric_terms`). S'il y a plusieurs mots-clés et que 'ou' est utilisé entre eux, utilise 'OR' pour `content_operator`. Sinon, utilise 'AND' (défaut).
                    - Si la requête utilise des négations comme 'pas', 'sauf', 'sans', 'ne...pas', utilise les champs `negated_content_terms` ou `excluded_rubric_terms` pour ces termes exclus.
                    - Interprète attentivement les expressions de date et de période : 'entre J1 et J2', 'après J', 'avant J', 'depuis AAAA', 'à partir de AAAA', 'en AAAA', 'le mois de M AAAA', 'l'année AAAA'. Détermine `date_start` et `date_end`. Normalise les dates au format AAAA-MM-JJ si possible, sinon AAAA-MM ou AAAA. Si seule une année est donnée (ex: 'en 2012'), utilise AAAA-01-01 pour `date_start` et AAAA-12-31 pour `date_end`. Pour 'après JJ/MM/AAAA', détermine la date de début appropriée (par exemple, le jour suivant ou le jour même selon l'usage commun). Pour 'à partir de AAAA', date_start est AAAA-01-01. Pour 'mois de Juin 2013', date_start=2013-06-01, date_end=2013-06-30.
                    - Si des mots spécifiques sont requis explicitement dans le *titre* (ex: "titre contient X", "dont le titre traite de Y"), utilise le champ `title_terms`. Ne mets pas ces mots dans `content_terms` sauf s'ils sont aussi des sujets généraux.
                    - Si la présence d'une *image* est explicitement mentionnée comme requise ("avec image", "contenant une image"), règle `has_image` à `true`. Sinon, laisse-le à `null` ou `false`.
                    - Si la question principale de l'utilisateur est de savoir "quelles rubric_terms" contiennent quelque chose (ex: "Dans quelles rubric_terms trouve-t-on..."), règle `target_info` à 'rubric_terms'. Sinon, laisse la valeur par défaut 'articles'.
                    - Ignore les formules de politesse ("Je voudrais", "Afficher", "Donner", "Chercher", etc.) et concentre-toi sur les critères de recherche.
                    - Si aucun critère d'un certain type n'est trouvé, l'outil omettra le champ correspondant ou le laissera à `null`.
                    - Si la requête spécifie explicitement une EXCLUSION de période temporelle (ex: 'mais pas en juin', 'sauf décembre 2012', 'hormis la semaine du X au Y'), identifie cette période et ajoute-la à la liste `excluded_date_periods`. Essaie de normaliser au format 'AAAA-MM-JJ/AAAA-MM-JJ' si possible, sinon 'AAAA-MM' ou 'AAAA'. Par exemple, 'pas en juin 2012' devrait devenir '2012-06'. 'entre 2012 et 2014 sauf l'été 2013' pourrait générer date_start='2012-01-01', date_end='2014-12-31', excluded_date_periods=['2013-06-21/2013-09-22'].

                    Requête utilisateur: "{query}"

                    Extrais les informations et structure-les en utilisant l'outil fourni. Ne génère que la structure de données demandée.
                """
                )
            ]
        )
        return pydantic_query
    
    # ========== SEARCH ==========
    
    def search(self, documents: Dict[str, Document], index: Dict[str, InvertedIndex], debug=False) -> List[Document]:
        
        results: Set[str] = set()
        
        if self.content_terms:
            if self.content_operator == "AND":
                results = set(
                    index["texte"].find_docs(self.content_terms)
                )
            else:
                # add list elements to set
                for keyword in self.content_terms:
                    results.update(
                        index["texte"].find_docs([keyword])
                    )
        else:
            results = set(documents.keys())
            
        if self.negated_content_terms:
            for keyword in self.negated_content_terms:
                results.difference_update(
                    index["texte"].find_docs([keyword])
                )
                
        if self.title_terms:
            results.intersection_update(
                index["titre"].find_docs(self.title_terms)
            )

        for doc_id in results.copy():
            
            if self.has_image and not documents[doc_id].images:
                results.remove(doc_id)
                if debug: print("Removed", doc_id, "no image")
                continue
            
            if self.rubric_terms:
                if not any(rubrique in documents[doc_id].rubrique.lower() for rubrique in self.rubric_terms):
                    results.remove(doc_id)
                    if debug: print("Removed", doc_id, "rubrique is not required")
                    continue
                if any(rubrique in documents[doc_id].rubrique.lower() for rubrique in self.negated_rubric_terms):
                    results.remove(doc_id)
                    if debug: print("Removed", doc_id, "rubrique is negated")
                    continue
                
            if self.date_start and documents[doc_id].date.astimezone(self.date_start.tzinfo) < self.date_start:
                results.remove(doc_id)
                if debug: print("Removed", doc_id, "too old")
                continue
                
            if self.date_end and documents[doc_id].date.astimezone(self.date_end.tzinfo) > self.date_end:
                results.remove(doc_id)
                if debug: print("Removed", doc_id, "too recent")
                continue
                
            if self.excluded_date_periods:
                for period in self.excluded_date_periods:
                    if "/" in period:    
                        start, end = period.split('/')
                        start = datetime.datetime.strptime(start, "%Y-%m-%d") if '-' in start else datetime.datetime.strptime(start, "%Y")
                        end = datetime.datetime.strptime(end, "%Y-%m-%d") if '-' in end else datetime.datetime.strptime(end, "%Y")
                    else:
                        start = datetime.datetime.strptime(period, "%Y-%m") if '-' in period else datetime.datetime.strptime(period, "%Y")
                        end = start
                        
                    # Contrairement aux tests precedents, pas besoin de timezone (dates au format YYYY-MM-DD)
                    if documents[doc_id].date >= start and documents[doc_id].date <= end:
                        results.remove(doc_id)
                        print("Removed", doc_id, "not in time period", start, end)
                        continue
            
            # XXX : Target info ignored == return articles otherwise
        
        return [documents[doc_id] for doc_id in results]
