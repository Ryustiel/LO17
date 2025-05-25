from typing import List, Dict, Set, Optional, Literal, Tuple, Union
import pydantic
import datetime
import calendar  # Utilise pour monthrange

from .document import Document
from .base.inverted_index import InvertedIndex
from .base.base_query import BaseQuery

from .scripts.query_parser import QueryParser


class Query(BaseQuery):
    """
    Représentation structurée d'une requête de recherche d'articles,
    extraite d'une requête en langage naturel.
    """
    content_terms: List[str] = pydantic.Field(
        default=[],
        description="Liste des mots-clés principaux à chercher dans le contenu."
    )
    content_operator: Literal['AND', 'OR'] = pydantic.Field(
        default='AND',
        description="Opérateur logique pour 'content_terms'."
    )
    rubric_terms: List[str] = pydantic.Field(
        default=[],
        description="Liste des rubriques à inclure. Supporte la recherche de sous-chaînes."
    )
    rubric_operator: Optional[Literal['AND', 'OR']] = pydantic.Field(
        default=None,
        description="Opérateur logique pour 'rubric_terms'. Si None et plusieurs termes, 'OR' est appliqué."
    )
    negated_content_terms: List[str] = pydantic.Field(
        default=[],
        description="Mots-clés à exclure du contenu. Chaque terme est une expression à rechercher via AND."
    )
    negated_rubric_terms: List[str] = pydantic.Field(
        default=[],
        description="Rubriques à exclure."
    )
    date_start: Optional[datetime.datetime] = pydantic.Field(
        default=None,
        description="Date de début (inclusive) pour la période de recherche."
    )
    date_end: Optional[datetime.datetime] = pydantic.Field(
        default=None,
        description="Date de fin (inclusive) pour la période de recherche."
    )
    excluded_date_periods: List[str] = pydantic.Field(
        default=[],
        description="Périodes spécifiques à exclure. Formats: 'AAAA-MM-JJ/AAAA-MM-JJ', 'AAAA-MM', 'AAAA'."
    )
    title_terms: List[str] = pydantic.Field(
        default=[],
        description="Termes requis dans le titre de l'article."
    )
    title_operator: Optional[Literal['AND', 'OR']] = pydantic.Field(
        default=None,
        description="Opérateur logique pour 'title_terms'. Si None et plusieurs termes, 'AND' est appliqué."
    )
    has_image: bool = pydantic.Field(
        default=False,
        description="Indique si l'article doit avoir une image."
    )
    target_info: Literal['articles', 'rubriques'] = pydantic.Field(
        default='articles',
        description="Type d'information principal demandé ('articles' ou 'rubriques')."
    )

    @classmethod
    def _parse_date_condition_value(cls, date_str: str) -> Optional[datetime.datetime]:
        """Tente de parser une chaîne de date (YYYY-MM-DD, YYYY-MM, ou YYYY) en datetime."""
        try:
            if len(date_str) == 10:  # YYYY-MM-DD
                return datetime.datetime.strptime(date_str, "%Y-%m-%d")
            elif len(date_str) == 7:  # YYYY-MM
                return datetime.datetime.strptime(date_str, "%Y-%m")
            elif len(date_str) == 4:  # YYYY
                return datetime.datetime.strptime(date_str, "%Y")
        except ValueError:
            return None
        return None

    @classmethod
    def _normalize_date_range(cls, dt: datetime.datetime, format_len: int) -> datetime.datetime:
        """Normalise une datetime à la fin de la période (jour, mois, année)."""
        if format_len == 10:  # YYYY-MM-DD
            return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif format_len == 7:  # YYYY-MM
            _, last_day = calendar.monthrange(dt.year, dt.month)
            return datetime.datetime(dt.year, dt.month, last_day, 23, 59, 59, 999999)
        elif format_len == 4:  # YYYY
            return datetime.datetime(dt.year, 12, 31, 23, 59, 59, 999999)
        return dt # Fallback

    @classmethod
    def build(cls, query_str: str) -> 'Query':
        """
        Construit un objet Query à partir d'une chaîne de requête utilisateur
        en utilisant QueryParser pour l'extraction initiale.
        """
        parser_output: dict = QueryParser().process_query(query_str)
        pydantic_input = {}

        pydantic_input['content_terms'] = parser_output.get('content_terms', [])
        pydantic_input['content_operator'] = parser_output.get('content_operator') or 'AND'
        pydantic_input['rubric_terms'] = parser_output.get('rubric_terms', [])
        pydantic_input['rubric_operator'] = parser_output.get('rubric_operator')
        pydantic_input['negated_content_terms'] = parser_output.get('negated_content_terms', [])
        pydantic_input['negated_rubric_terms'] = parser_output.get('negated_rubric_terms', [])
        pydantic_input['title_terms'] = parser_output.get('title_terms', [])
        pydantic_input['title_operator'] = parser_output.get('title_operator')
        pydantic_input['has_image'] = parser_output.get('has_image', False)

        pydantic_input['target_info'] = 'rubriques' if parser_output.get('return_fields') == ['rubric'] else 'articles'

        current_date_start: Optional[datetime.datetime] = None
        current_date_end: Optional[datetime.datetime] = None
        excluded_periods_list: List[str] = []

        date_conditions = parser_output.get('date_conditions', [])

        # Phase 1: Déterminer la plage globale date_start / date_end
        for condition in date_conditions:
            cond_type = condition.get('type')
            temp_ds: Optional[datetime.datetime] = None
            temp_de: Optional[datetime.datetime] = None

            if cond_type == 'exact_date':
                dt_val = cls._parse_date_condition_value(condition.get('date', ''))
                if dt_val:
                    temp_ds = dt_val
                    temp_de = cls._normalize_date_range(dt_val, 10) # 10 pour YYYY-MM-DD
            elif cond_type == 'year':
                year = condition.get('year')
                if year:
                    temp_ds = datetime.datetime(int(year), 1, 1)
                    temp_de = cls._normalize_date_range(temp_ds, 4) # 4 pour YYYY
            elif cond_type == 'month_year':
                year = condition.get('year')
                month = condition.get('month')
                if year and month:
                    year, month = int(year), int(month)
                    temp_ds = datetime.datetime(year, month, 1)
                    temp_de = cls._normalize_date_range(temp_ds, 7) # 7 pour YYYY-MM
            elif cond_type == 'range':
                ds_str = condition.get('from')
                de_str = condition.get('to')
                if ds_str: temp_ds = cls._parse_date_condition_value(ds_str)
                if de_str:
                    _temp_de = cls._parse_date_condition_value(de_str)
                    if _temp_de: temp_de = cls._normalize_date_range(_temp_de, len(de_str))
            elif cond_type == 'year_range':
                year_from = condition.get('from')
                year_to = condition.get('to')
                if year_from: temp_ds = datetime.datetime(int(year_from), 1, 1)
                if year_to: temp_de = cls._normalize_date_range(datetime.datetime(int(year_to), 1, 1), 4)
            elif cond_type == 'after':
                dt_val = cls._parse_date_condition_value(condition.get('date', ''))
                if dt_val: temp_ds = dt_val
            elif cond_type == 'after_year':
                year = condition.get('year')
                if year: temp_ds = datetime.datetime(int(year), 1, 1)
            elif cond_type == 'before':  # non-inclusive end
                dt_val = cls._parse_date_condition_value(condition.get('date', ''))
                if dt_val: temp_de = dt_val - datetime.timedelta(microseconds=1)
            elif cond_type == 'before_year':  # non-inclusive end
                year = condition.get('year')
                if year: temp_de = datetime.datetime(int(year) - 1, 12, 31, 23, 59, 59, 999999)

            if temp_ds:
                current_date_start = max(current_date_start, temp_ds) if current_date_start else temp_ds
            if temp_de:
                current_date_end = min(current_date_end, temp_de) if current_date_end else temp_de

        pydantic_input['date_start'] = current_date_start
        pydantic_input['date_end'] = current_date_end

        # Phase 2: Gérer les exclusions de date
        for condition in date_conditions:
            cond_type = condition.get('type')
            is_legacy_exclude_month = 'exclude_month' in condition and cond_type is None
            if cond_type == 'exclude_month' or is_legacy_exclude_month:
                if is_legacy_exclude_month:
                    month_to_exclude_value = condition.get('exclude_month')
                else:  # cond_type == 'exclude_month'
                    month_to_exclude_value = condition.get('month')
                year_for_excluded_month = condition.get('year')
                if month_to_exclude_value:
                    month_to_exclude = int(month_to_exclude_value)
                    if year_for_excluded_month:
                        excluded_periods_list.append(f"{int(year_for_excluded_month):04d}-{month_to_exclude:02d}")
                    elif current_date_start and current_date_end:
                        for year_iter in range(current_date_start.year, current_date_end.year + 1):
                            excl_period_month_start = datetime.datetime(year_iter, month_to_exclude, 1)
                            excl_period_month_end = cls._normalize_date_range(excl_period_month_start, 7)
                            if (excl_period_month_start <= current_date_end and
                                excl_period_month_end >= current_date_start):
                                excluded_periods_list.append(f"{year_iter:04d}-{month_to_exclude:02d}")
            elif cond_type == 'exclude_period':
                from_date_str = condition.get('from')
                to_date_str = condition.get('to')
                if from_date_str and to_date_str:
                    excluded_periods_list.append(f"{from_date_str}/{to_date_str}")
                elif from_date_str:
                    excluded_periods_list.append(from_date_str)

        pydantic_input['excluded_date_periods'] = list(set(excluded_periods_list))

        # Assurer que les dates ont un fuseau horaire (UTC par défaut si naïves)
        default_tz = datetime.timezone.utc
        if pydantic_input['date_start'] and pydantic_input['date_start'].tzinfo is None:
            pydantic_input['date_start'] = pydantic_input['date_start'].replace(tzinfo=default_tz)
        if pydantic_input['date_end'] and pydantic_input['date_end'].tzinfo is None:
            pydantic_input['date_end'] = pydantic_input['date_end'].replace(tzinfo=default_tz)

        return cls.model_validate(pydantic_input)

    @classmethod
    def llm_build(cls, query_str: str) -> 'Query':
        """
        Construit un objet Query à partir d'une chaîne de requête utilisateur
        en utilisant un modèle de langage (LLM) structuré.
        """
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
        ).with_structured_output(cls).invoke([
            SystemMessage(
                content=f"""
                Instruction: Analyse la requête utilisateur suivante pour interroger une archive d'articles nommée ADIT. Extrais les critères de recherche pertinents.

                Règles d'interprétation pour extraire les informations:
                - Le but est de générer une requête structurée pour une base de données.
                - Les champs renommés sont: `keywords` -> `content_terms`, `keywords_operator` -> `content_operator`, `rubriques` -> `rubric_terms`, `excluded_keywords` -> `negated_content_terms`, `excluded_rubriques` -> `negated_rubric_terms`, `title_contains` -> `title_terms`.
                - De nouveaux opérateurs `rubric_operator` et `title_operator` (AND/OR/None) ont été ajoutés. S'ils ne sont pas spécifiés et qu'il y a plusieurs termes, `rubric_operator` sera OR par défaut, et `title_operator` sera AND par default.
                - Combine les différents types de critères (content_terms, rubric_terms, date, title_terms, image) avec un 'ET' logique implicite, sauf indication contraire.
                - Si la requête utilise 'ou', 'soit...soit' pour des alternatives (ex: "articles sur A ou B", "rubrique X ou Y"), place ces alternatives ensemble dans la liste correspondante (`content_terms` ou `rubric_terms`). S'il y a plusieurs mots-clés et que 'ou' est utilisé entre eux, utilise 'OR' pour `content_operator` (ou `rubric_operator` / `title_operator` selon le champ). Sinon, `content_operator` est 'AND' par défaut. `rubric_operator` est `None` (sera OR si plusieurs termes) par défaut. `title_operator` est `None` (sera AND si plusieurs termes) par défaut.
                - Si la requête utilise des négations comme 'pas', 'sauf', 'sans', 'ne...pas', utilise les champs `negated_content_terms` ou `negated_rubric_terms` pour ces termes exclus.
                - Interprète attentivement les expressions de date et de période : 'entre J1 et J2', 'après J', 'avant J', 'depuis AAAA', 'à partir de AAAA', 'en AAAA', 'le mois de M AAAA', 'l'année AAAA'. Détermine `date_start` et `date_end`. Normalise les dates au format AAAA-MM-JJ si possible, sinon AAAA-MM ou AAAA. Si seule une année est donnée (ex: 'en 2012'), utilise AAAA-01-01 pour `date_start` et AAAA-12-31 pour `date_end`. Pour 'après JJ/MM/AAAA', détermine la date de début appropriée. Pour 'à partir de AAAA', date_start est AAAA-01-01. Pour 'mois de Juin 2013', date_start=2013-06-01, date_end=2013-06-30.
                - Si des mots spécifiques sont requis explicitement dans le *titre* (ex: "titre contient X", "dont le titre traite de Y"), utilise le champ `title_terms`. Ne mets pas ces mots dans `content_terms` sauf s'ils sont aussi des sujets généraux.
                - Si la présence d'une *image* est explicitement mentionnée comme requise ("avec image", "contenant une image"), règle `has_image` à `true`. Sinon, laisse-le à `false`.
                - Si la question principale de l'utilisateur est de savoir "quelles rubriques" contiennent quelque chose (ex: "Dans quelles rubriques trouve-t-on..."), règle `target_info` à 'rubriques'. Sinon, laisse la valeur par défaut 'articles'.
                - Ignore les formules de politesse.
                - Si la requête spécifie explicitement une EXCLUSION de période temporelle (ex: 'mais pas en juin', 'sauf décembre 2012', 'hormis la semaine du X au Y'), identifie cette période et ajoute-la à la liste `excluded_date_periods`. Essaie de normaliser au format 'AAAA-MM-JJ/AAAA-MM-JJ' si possible, sinon 'AAAA-MM' ou 'AAAA'. Par exemple, 'pas en juin 2012' devrait devenir '2012-06'. 'entre 2012 et 2014 sauf l'été 2013' pourrait générer date_start='2012-01-01', date_end='2014-12-31', excluded_date_periods=['2013-06-21/2013-09-22'].

                Requête utilisateur: "{query_str}"

                Extrais les informations et structure-les en utilisant l'outil fourni. Ne génère que la structure de données demandée.
            """)
        ])
        # Assurer que les dates du LLM sont aussi aware (si elles sont naïves)
        default_tz = datetime.timezone.utc
        if pydantic_query.date_start and pydantic_query.date_start.tzinfo is None:
            pydantic_query.date_start = pydantic_query.date_start.replace(tzinfo=default_tz)
        if pydantic_query.date_end and pydantic_query.date_end.tzinfo is None:
            pydantic_query.date_end = pydantic_query.date_end.replace(tzinfo=default_tz)
        return pydantic_query

    @staticmethod
    def _get_doc_ids_for_terms(
            terms: List[str],
            operator: Optional[Literal['AND', 'OR']],
            field_name: str,
            default_operator_if_none: Literal['AND', 'OR'],
            index: Dict[str, InvertedIndex],
            all_doc_ids_in_corpus: Set[str],
            debug: bool = False
    ) -> Set[str]:
        """Récupère les IDs de documents pour des termes donnés dans un champ indexé."""
        if not terms:
            return all_doc_ids_in_corpus

        field_idx: Optional[InvertedIndex] = None
        actual_field_name_used = field_name

        if field_name == 'content':
            field_idx = index.get('content')
            if not field_idx:
                field_idx = index.get('texte')
                if field_idx: actual_field_name_used = 'texte'
        elif field_name == 'title':
            field_idx = index.get('title')
            if not field_idx:
                field_idx = index.get('titre')
                if field_idx: actual_field_name_used = 'titre'
        else:
            field_idx = index.get(field_name)

        if not field_idx:
            if debug: print(f"Search_Helper: Index for field '{field_name}' (tried '{actual_field_name_used}') not found. No results for this criterion.")
            return set()

        effective_operator = operator
        if effective_operator is None:
            effective_operator = default_operator_if_none if len(terms) > 1 else 'AND'

        if effective_operator == 'AND':
            return set(field_idx.find_docs(terms))
        elif effective_operator == 'OR':
            current_term_doc_ids = set()
            for term in terms:
                current_term_doc_ids.update(field_idx.get(term, []))
            return current_term_doc_ids
        return set()

    @staticmethod
    def _parse_excluded_period_str(period_str: str, default_tz: datetime.tzinfo, debug: bool = False) -> Optional[
        Tuple[datetime.datetime, datetime.datetime]]:
        """
        Parse une chaîne de période exclue ("AAAA-MM-JJ/AAAA-MM-JJ", "AAAA-MM", "AAAA")
        en un tuple (start_datetime, end_datetime) timezone-aware.
        """
        start_dt: Optional[datetime.datetime] = None
        end_dt: Optional[datetime.datetime] = None

        try:
            if '/' in period_str:  # Range
                start_str, end_str = period_str.split('/', 1)
                start_dt = Query._parse_date_condition_value(start_str)
                _temp_end_dt = Query._parse_date_condition_value(end_str)
                if _temp_end_dt: end_dt = Query._normalize_date_range(_temp_end_dt, len(end_str))
            else:  # Single period
                start_dt = Query._parse_date_condition_value(period_str)
                if start_dt: end_dt = Query._normalize_date_range(start_dt, len(period_str))

            if start_dt and end_dt:
                if start_dt.tzinfo is None: start_dt = start_dt.replace(tzinfo=default_tz)
                if end_dt.tzinfo is None: end_dt = end_dt.replace(tzinfo=default_tz)
                return start_dt, end_dt
        except Exception as e:
            if debug: print(f"Error parsing excluded period string '{period_str}': {e}")
        return None

    def search(self, documents: Dict[str, Document], index: Dict[str, InvertedIndex], debug: bool = False) -> Union[List[Document], List[str]]:
        """
        Exécute une recherche basée sur les critères de la requête.

        Args:
            documents: Dictionnaire des documents par ID.
            index: Dictionnaire des index inversés par nom de champ ('content', 'rubric', 'title').
            debug: Active les messages de débogage.

        Returns:
            Une liste de Document objects ou une liste de chaînes de rubriques
            selon la valeur de `target_info`.
        """
        if not documents:
            return []

        all_doc_ids_in_corpus = set(documents.keys())
        candidate_doc_ids: Set[str] = all_doc_ids_in_corpus.copy()

        # 1. Filtres par termes positifs (Content, Rubric, Title)
        if self.content_terms:
            content_ids = self._get_doc_ids_for_terms(
                self.content_terms, self.content_operator, 'content', 'AND', index, all_doc_ids_in_corpus, debug
            )
            candidate_doc_ids.intersection_update(content_ids)
            if debug: print(f"Search: After content_terms: {len(candidate_doc_ids)} candidates.")

        if self.rubric_terms:
            # Note: La recherche par rubrique utilise une correspondance de sous-chaîne sur l'attribut `rubrique`
            # du document, et non un index inversé, pour permettre des recherches plus flexibles.
            rubric_matched_ids = set()
            effective_rubric_op = self.rubric_operator if self.rubric_operator is not None else ('OR' if len(self.rubric_terms) > 1 else 'AND')
            query_rubrics_lower = [term.lower() for term in self.rubric_terms]

            for doc_id in candidate_doc_ids.copy(): # Itérer sur une copie si des suppressions directes étaient envisagées
                doc = documents.get(doc_id)
                if not doc or not doc.rubrique:
                    continue
                doc_rubric_lower = doc.rubrique.lower()

                match = False
                if effective_rubric_op == 'OR':
                    if any(query_term in doc_rubric_lower for query_term in query_rubrics_lower):
                        match = True
                elif effective_rubric_op == 'AND':
                    if all(query_term in doc_rubric_lower for query_term in query_rubrics_lower):
                        match = True
                if match:
                    rubric_matched_ids.add(doc_id)

            candidate_doc_ids.intersection_update(rubric_matched_ids)
            if debug: print(f"Search: After rubric_terms: {len(candidate_doc_ids)} candidates.")

        if self.title_terms:
            title_ids = self._get_doc_ids_for_terms(
                self.title_terms, self.title_operator, 'title', 'AND', index, all_doc_ids_in_corpus, debug
            )
            candidate_doc_ids.intersection_update(title_ids)
            if debug: print(f"Search: After title_terms: {len(candidate_doc_ids)} candidates.")

        # 2. Filtres par termes négatifs
        if self.negated_content_terms:
            ids_to_exclude = set()
            neg_content_idx = index.get('content')
            if not neg_content_idx: # <--- AJOUT DE CETTE VÉRIFICATION ET FALLBACK
                neg_content_idx = index.get('texte')
            if neg_content_idx:
                for neg_expression in self.negated_content_terms:
                    sub_terms = [st.lower() for st in neg_expression.split()]
                    if sub_terms:
                        ids_to_exclude.update(neg_content_idx.find_docs(sub_terms))
            candidate_doc_ids.difference_update(ids_to_exclude)
            if debug: print(f"Search: After negated_content_terms: {len(candidate_doc_ids)} candidates.")

        if self.negated_rubric_terms:
            ids_to_exclude = set()
            query_neg_rubrics_lower = [term.lower() for term in self.negated_rubric_terms]
            for doc_id in candidate_doc_ids.copy():
                doc = documents.get(doc_id)
                if not doc or not doc.rubrique:
                    continue
                doc_rubric_lower = doc.rubric.lower()
                if any(neg_term in doc_rubric_lower for neg_term in query_neg_rubrics_lower):
                    ids_to_exclude.add(doc_id)
            candidate_doc_ids.difference_update(ids_to_exclude)
            if debug: print(f"Search: After negated_rubric_terms: {len(candidate_doc_ids)} candidates.")

        # 3. Filtres sur les attributs des documents
        final_results: List[Document] = []
        default_tz = datetime.timezone.utc

        for doc_id in candidate_doc_ids:
            doc = documents.get(doc_id)
            if not doc: continue

            if self.has_image and not (doc.images and any(img.url for img in doc.images if img.url)):
                if debug: print(f"Search: Doc {doc_id} excluded by has_image=True.")
                continue

            doc_date = doc.date
            if doc_date and doc_date.tzinfo is None:
                doc_date = doc_date.replace(tzinfo=default_tz)

            if self.date_start and (not doc_date or doc_date < self.date_start):
                if debug: print(f"Search: Doc {doc_id} excluded by date_start {self.date_start}.")
                continue

            if self.date_end and (not doc_date or doc_date > self.date_end):
                if debug: print(f"Search: Doc {doc_id} excluded by date_end {self.date_end}.")
                continue

            if doc_date and self.excluded_date_periods:
                excluded_by_period_flag = False
                for period_str in self.excluded_date_periods:
                    parsed_period = self._parse_excluded_period_str(period_str, default_tz)
                    if parsed_period and parsed_period[0] <= doc_date <= parsed_period[1]:
                        if debug: print(f"Search: Doc {doc_id} excluded by period '{period_str}'.")
                        excluded_by_period_flag = True
                        break
                if excluded_by_period_flag:
                    continue

            final_results.append(doc)

        if debug: print(f"Search: Final results count: {len(final_results)}")

        if self.target_info == 'rubriques':
            rubric_set: Set[str] = {doc_item.rubrique for doc_item in final_results if doc_item.rubrique}
            return sorted(list(rubric_set))
        else:
            final_results.sort(
                key=lambda d: d.date if d.date else datetime.datetime.min.replace(tzinfo=default_tz),
                reverse=True
            )
            return final_results