
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
    keywords: List[str] = pydantic.Field(
        default=[],
        description="Liste des mots-clés, sujets, thèmes ou entités nommées (personnes, lieux, organisations) principaux à rechercher dans le contenu des articles. Tous les termes doivent être présents (logique ET implicite), sauf si l'instruction 'OU' est explicitement utilisée dans la requête pour certains termes."
    )
    keywords_operator: Literal['AND', 'OR'] = pydantic.Field(
        default='AND', # Par défaut 'ET' pour les mots-clés
        description="Opérateur logique à appliquer entre les éléments de la liste 'keywords'. Utiliser 'OR' si la requête contient des alternatives claires comme 'A ou B'."
    )
    rubriques: List[str] = pydantic.Field(
        default=[],
        description="Liste des rubriques ou sections spécifiques où chercher les articles. La recherche s'effectue dans L'UNE de ces rubriques (logique OU)."
    )
    excluded_keywords: List[str] = pydantic.Field(
        default=[],
        description="Liste des mots-clés ou sujets explicitement exclus de la recherche (ex: 'pas X', 'sauf Y', 'sans Z')."
    )
    excluded_rubriques: List[str] = pydantic.Field(
        default=[],
        description="Liste des rubriques explicitement exclues de la recherche."
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
    title_contains: List[str] = pydantic.Field(
        default=[],
        description="Liste de mots ou termes spécifiques qui doivent impérativement apparaître dans le titre de l'article (logique ET)."
    )
    has_image: bool = pydantic.Field(
        default=False,
        description="Booléen indiquant si l'article doit obligatoirement contenir une image (true) ou non (false/null)."
    )
    target_info: Literal['articles', 'rubriques'] = pydantic.Field(
        default='articles',
        description="Spécifie le type d'information principal demandé par l'utilisateur. 'articles' pour une liste d'articles (défaut), 'rubriques' si la question porte spécifiquement sur les rubriques contenant certains sujets."
    )

    # ========== BUILD ==========

    @classmethod
    def build(cls, query: str) -> 'Query':
        
        from langchain_core.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        validated_pydantic: "Query" = (
            PromptTemplate(
                template = """
                    Instruction: Analyse la requête utilisateur suivante pour interroger une archive d'articles nommée ADIT. Extrais les critères de recherche pertinents.

                    Règles d'interprétation pour extraire les informations:
                    - Le but est de générer une requête structurée pour une base de données.
                    - Combine les différents types de critères (keywords, rubriques, date, titre, image) avec un 'ET' logique implicite, sauf indication contraire.
                    - Si la requête utilise 'ou', 'soit...soit' pour des alternatives (ex: "articles sur A ou B", "rubrique X ou Y"), place ces alternatives ensemble dans la liste correspondante (`keywords` ou `rubriques`). S'il y a plusieurs mots-clés et que 'ou' est utilisé entre eux, utilise 'OR' pour `keywords_operator`. Sinon, utilise 'AND' (défaut).
                    - Si la requête utilise des négations comme 'pas', 'sauf', 'sans', 'ne...pas', utilise les champs `excluded_keywords` ou `excluded_rubriques` pour ces termes exclus.
                    - Interprète attentivement les expressions de date et de période : 'entre J1 et J2', 'après J', 'avant J', 'depuis AAAA', 'à partir de AAAA', 'en AAAA', 'le mois de M AAAA', 'l'année AAAA'. Détermine `date_start` et `date_end`. Normalise les dates au format AAAA-MM-JJ si possible, sinon AAAA-MM ou AAAA. Si seule une année est donnée (ex: 'en 2012'), utilise AAAA-01-01 pour `date_start` et AAAA-12-31 pour `date_end`. Pour 'après JJ/MM/AAAA', détermine la date de début appropriée (par exemple, le jour suivant ou le jour même selon l'usage commun). Pour 'à partir de AAAA', date_start est AAAA-01-01. Pour 'mois de Juin 2013', date_start=2013-06-01, date_end=2013-06-30.
                    - Si des mots spécifiques sont requis explicitement dans le *titre* (ex: "titre contient X", "dont le titre traite de Y"), utilise le champ `title_contains`. Ne mets pas ces mots dans `keywords` sauf s'ils sont aussi des sujets généraux.
                    - Si la présence d'une *image* est explicitement mentionnée comme requise ("avec image", "contenant une image"), règle `has_image` à `true`. Sinon, laisse-le à `null` ou `false`.
                    - Si la question principale de l'utilisateur est de savoir "quelles rubriques" contiennent quelque chose (ex: "Dans quelles rubriques trouve-t-on..."), règle `target_info` à 'rubriques'. Sinon, laisse la valeur par défaut 'articles'.
                    - Ignore les formules de politesse ("Je voudrais", "Afficher", "Donner", "Chercher", etc.) et concentre-toi sur les critères de recherche.
                    - Si aucun critère d'un certain type n'est trouvé, l'outil omettra le champ correspondant ou le laissera à `null`.
                    - Si la requête spécifie explicitement une EXCLUSION de période temporelle (ex: 'mais pas en juin', 'sauf décembre 2012', 'hormis la semaine du X au Y'), identifie cette période et ajoute-la à la liste `excluded_date_periods`. Essaie de normaliser au format 'AAAA-MM-JJ/AAAA-MM-JJ' si possible, sinon 'AAAA-MM' ou 'AAAA'. Par exemple, 'pas en juin 2012' devrait devenir '2012-06'. 'entre 2012 et 2014 sauf l'été 2013' pourrait générer date_start='2012-01-01', date_end='2014-12-31', excluded_date_periods=['2013-06-21/2013-09-22'].

                    Requête utilisateur: "{query}"

                    Extrais les informations et structure-les en utilisant l'outil fourni. Ne génère que la structure de données demandée.
                """
            )
            | ChatOpenAI(
                base_url="https://ia.beta.utc.fr/api",
                temperature=0, 
                model="mistral-small3.1:latest", 
                api_key=os.getenv("UTC_API_KEY")
            ).with_structured_output(cls)
        ).invoke(
            {"query": query}
        )
        return validated_pydantic
    
    # ========== SEARCH ==========
    
    def search(self, documents: Dict[str, Document], index: Dict[str, InvertedIndex], debug=False) -> List[Document]:
        
        results: Set[str] = set()
        
        if self.keywords:
            if self.keywords_operator == "AND":
                results = set(
                    index["texte"].find_docs(self.keywords)
                )
            else:
                # add list elements to set
                for keyword in self.keywords:
                    results.update(
                        index["texte"].find_docs([keyword])
                    )
        else:
            results = set(documents.keys())
            
        if self.excluded_keywords:
            for keyword in self.excluded_keywords:
                results.difference_update(
                    index["texte"].find_docs([keyword])
                )
                
        if self.title_contains:
            results.intersection_update(
                index["titre"].find_docs(self.title_contains)
            )

        for doc_id in results.copy():
            
            if self.has_image and not documents[doc_id].images:
                results.remove(doc_id)
                if debug: print("Removed", doc_id, "no image")
                continue
            
            if self.rubriques:
                if not any(rubrique in documents[doc_id].rubrique.lower() for rubrique in self.rubriques):
                    results.remove(doc_id)
                    if debug: print("Removed", doc_id, "rubrique is not required")
                    continue

            if any(rubrique in documents[doc_id].rubrique.lower() for rubrique in self.excluded_rubriques):
                results.remove(doc_id)
                if debug: print("Removed", doc_id, "rubrique is excluded")
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
            
            # XXX : Target info ignored
        
        return [documents[doc_id] for doc_id in results]
