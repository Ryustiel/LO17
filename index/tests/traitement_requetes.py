import re
from datetime import datetime

# --- Constantes globales et utilitaires ---
OP_AND = "AND"
OP_OR = "OR"

DATE_TYPE_RANGE = "range"
DATE_TYPE_AFTER = "after"
DATE_TYPE_AFTER_YEAR = "after_year"
DATE_TYPE_EXACT_DATE = "exact_date"
DATE_TYPE_YEAR_RANGE = "year_range"
DATE_TYPE_MONTH_YEAR = "month_year"
DATE_TYPE_YEAR = "year"
DATE_EXCLUDE_MONTH = "exclude_month"

RETURN_FIELD_RUBRIC = "rubric"

EMPTY_STRING = ""
REGEX_FLAGS_I = re.IGNORECASE

# --- Données brutes pour QueryParserConfig (sorties de la classe pour lisibilité) ---
_MODULE_RAW_KNOWN_RUBRICS = [
    "horizons enseignement", "en direct des laboratoires", "focus",
    "a lire", "actualités innovations", "actualité innovation", "événement"
]

_MODULE_GENERAL_CLEANUP_REGEX_PATTERNS = [
    r"^(?:j’aimerais\s+(?:la\s+liste\s+des\s+articles|des\s+articles|un\s+article)\s+écrits\s+et\s+qui\s+parle(?:nt)?\s+(?:de|d'))\s*",
    r"^(?:j’aimerais\s+(?:la\s+liste\s+des\s+articles|des\s+articles|un\s+article)\s+qui\s+parle(?:nt)?\s+(?:de|d'))\s*",
    r"^(?:j’aimerais\s+(?:la\s+liste\s+des\s+articles|un\s+article)\s+écrits)\s*",
    r"^(?:quels\s+articles\s+|article\s+|articles\s+)?port(?:ent|e)\s+(?:[aà]\s+la\s+fois\s+)?sur\s*",
    r"^(?:article\s+traitant\s+des|articles\s+traitant\s+des|article\s+traitant\s+de|articles\s+traitant\s+de)\s+",
    r"^(?:recherches\s+sur|recherche\s+sur)\s+",
    r"^(?:portant\s+sur\s*(?:de\s*la)?)\s*",
    r"^(?:parle(?:nt)?|parlant|trait(?:e|ant))\s+(?:d'|des|de|du)\s*",
    r"^(?:écrits\s+et\s+qui\s+parle(?:nt)?\s+(?:de|d'))\s*",
    r"^(?:évoquant|évoque|évoquent)\s+",
    r"^(?:contenant|contient|contiennent)\s+(?:les\s+mots|le\s+mot)?\s*",
    r"^(?:possédant|possèdent|possède)\s+le\s+mot\s*",
    r"^(?:mentionnant|mentionnent|mentionne)\s*",
    r"^(?:impliquant|implique|impliquent)\s*",
    r"^(?:liés\s+[aà]|lié\s+[aà])\s*",
    r"^(?:sur|d[u']|des|de\s+la|de\s+l'|de)\s+",
    r"^(?:l'|le\s+|la\s+|les\s+)", r"^(?:un\s+|une\s+)", r"^(?:aux\s+|au\s+)",
    r"^(?:[aà]\s+propos\s+(?:des|de\s+la|de\s+l'|du|de))\s*",
    r"^(?:le\s+mot|les\s+mots|le\s+terme|les\s+termes)\s*",
    r"^(?:[aà]\s+la\s+fois\s+sur|[aà]\s+la\s+fois)\s*", r"^(?:soit\s+du|soit\s+des|soit)\s*",
    r"^(?:dans\s+le\s+domaine\s+(?:de|d'))\s*", r"^(?:dans\s+le\s+domaine)\s*",
    r"^(?:publiés\s+en|publié\s+en|publiés|publié|écrits\s+en|écrit\s+en|écrits|écrit|parus\s+en|parus|paru)(?:\s+|$)",
    r"^(?:sont\s+écrits|est\s+écrit|ont\s+été\s+publiés|a\s+été\s+publié)(?:\s+|$)",
    r"^(?:datés\s+[aà]\s+partir\s+de|datés|[aà]\s+partir)\s*",
    r"^(?:afficher\s+la\s+liste\s+des\s+articles|afficher\s+les\s+articles)\s*",
    r"^(?:qui\s+parle(?:nt)?\s*(?:d'|de|des|du))(?!\s*soit)\s*",
    r"^(?:qui\s+(?:contiennent\s+les\s+mots|contient\s+le\s+mot))\s*",
    r"^(?:qui\s+(?:sont\s+écrits\s+en|sont\s+écrits|est\s+écrit\s+en|est\s+écrit))\s*",
    r"^(?:qui\s+ont\s+pour)\s*",
    r"^(?:est-il\s+cité|sont-ils\s+cités|est-elle\s+citée|sont-elles\s+citées|est\s+cité)\s*\??$",
    r"^(?:et|ou|qui|la|dont\s+(?:la|le|les|l'))\s+",
    r"\s+dans\s+le\s+titre\s*$", r"\s+du\s+titre\s*$", r"\s+dans\s+le\s+contenu\s*$",
    r"\s+[aà]\s+partir\s*$",
    r"\s+(?:est-il\s+cité|sont-ils\s+cités|est-elle\s+citée|sont-elles\s+citées|est\s+cité)\s*\??$",
    r"^[aà]\s+",
]

_MODULE_JUNK_WORDS_IF_ALONE = [
    "le", "la", "les", "des", "du", "d", "l", "et", "ou", "qui", "sont", "est", "un", "une",
    "de", "dans", "par", "pour", "sur", "dont", "afficher", "articles", "article",
    "avec", "mot", "terme", "mots", "termes", "mois", "donc", "ont",
    "bulletins", "contenu", "titre", "rubrique", "publiés", "parus", "écrits", "datés",
    "provenant", "partir", "depuis", "après", "avant", "entre", "pendant", "année",
    "jour", "donner", "chercher", "liste", "lister", "trouver",
    "parlent", "parlant", "traitant", "évoquant", "contenant", "mentionnant", "impliquant",
    "tous", "tout", "lesquels", "lequel", "laquelle", "actu", "été", "propos",
    "à", "a"
]

_MODULE_GENERIC_INTRO_STRINGS_TO_STRIP = [
    "j’aimerais la liste des articles écrits et qui parlent de",
    "j’aimerais la liste des articles écrits", "j’aimerais un article qui parle de",
    "j’aimerais la liste des articles qui parlent de", "j’aimerais la liste des articles",
    "j’aimerais un article", "afficher la liste des articles", "quels sont les articles",
    "je voudrais les articles", "je voudrais tous les articles", "je voudrais tout les articles",
    "je veux les articles", "je veux des articles", "quels articles", "afficher les articles",
    "articles", "je cherche les articles", "je cherche des articles", "donner les articles",
    "chercher les articles", "nous souhaitons obtenir les articles", "rechercher tous les articles",
    "liste des articles", "lister tous les articles", "trouver les articles", "je veux voir les articles",
    "tous les articles", "dans quels articles", "je voudrais les bulletins", "je voudrais tous les bulletins",
    "je souhaites avoir tout les articles donc", "je souhaites avoir tout les articles",
    "je souhaite les", "je cherche les recherches sur",
]

_MODULE_CONTENT_INTRO_REGEX_PATTERNS_TO_STRIP = [
    r"^(?:quels\s+articles\s+|article\s+|articles\s+)?port(?:ent|e)\s+(?:[aà]\s+la\s+fois\s+)?sur\s*",
    r"^(?:article\s+traitant\s+des|articles\s+traitant\s+des|article\s+traitant\s+de|articles\s+traitant\s+de)\s+",
    r"^(?:recherches\s+sur|recherche\s+sur)\s*",
    r"^(?:portant\s+sur\s*(?:de\s*la)?)\s*",
    r"^(?:et\s+)?(?:parle(?:nt)?|parlant)\s*(?:d'|des|de|du)\s*",
    r"^(?:trait(?:e|ant))\s*(?:d'|des|de|du)\s*",
    r"^(?:[eé]voquant|[eé]voque|[eé]voquent)\s+",
    r"^(?:contenant|contient|contiennent)\s+(?:les\s+mots|le\s+mot)?\s*",
    r"^(?:poss[eè]dant|poss[eè]dent|poss[eè]de)\s+le\s+mot\s*",
    r"^(?:mentionnant|mentionnent|mentionne)\s*",
    r"^(?:impliquant|implique|impliquent)\s*",
    r"^(?:liés\s+[aà]|lié\s+[aà])\s*",
    r"^(?:[aà]\s+propos\s+(?:des|de\s+la|de\s+l'|du|de))\s*",
    r"^(?:qui\s+)?parle(?:nt)?\s+(?=soit\s)",
    r"^(?:qui\s+parle(?:nt)?\s*(?:d'|de|des|du))\s*",
    r"^(?:qui\s+(?:contiennent\s+les\s+mots|contient\s+le\s+mot))\s*",
    r"^(?:[eé]crits\s+et\s+qui\s+parle(?:nt)?\s+(?:de|d'))\s*",
    r"^(?:dans\s+le\s+domaine\s*(?:de|des|du|d'|de la|de l')?)\s*",
]


def normalize_apostrophes_globally(text: str | None) -> str | None:
    """
    Normalise les apostrophes (ex: `’` -> `'`) et gère les entrées `None`.
    """
    if text is None:
        return None
    return text.replace("’", "'").replace("‘", "'").replace("‛", "'")


def _prepare_raw_patterns_for_config(raw_patterns_list: list[str]) -> list[str]:
    """
    Prépare les patterns bruts: normalise apostrophes, filtre `None`, trie par longueur.
    Utilisé pour initialiser les constantes dans QueryParserConfig.
    """
    normalized_patterns = [normalize_apostrophes_globally(p) for p in raw_patterns_list]
    valid_patterns = [p for p in normalized_patterns if isinstance(p, str)]
    return sorted(valid_patterns, key=len, reverse=True)


class QueryParserConfig:
    """
    Configuration pour `QueryParser`.
    Centralise constantes, listes de mots et regex pré-compilées.
    """
    STRIP_CHARS_ALL = " .,;?!:'\""
    STRIP_CHARS_PUNCTUATION_ONLY = " .,;?!:"
    _PREPARED_RAW_KNOWN_RUBRICS = _prepare_raw_patterns_for_config(_MODULE_RAW_KNOWN_RUBRICS)

    def __init__(self):
        """Initialise la configuration avec les dictionnaires et regex nécessaires."""
        self.MONTHS_FR = {
            "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
            "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
            "decembre": 12
        }
        self.MONTHS_FR_RE_PATTERN = "|".join(self.MONTHS_FR.keys())
        self.MAX_MONTH_NAME_LEN = max(len(m) for m in self.MONTHS_FR.keys()) if self.MONTHS_FR else 0

        self.E_ACCENTS_TRANSLATION_TABLE = str.maketrans("éèêë", "eeee")

        # Map des rubriques normalisées vers leur forme canonique.
        self.CANONICAL_RUBRICS_MAP = {
            normalize_apostrophes_globally(raw_rubric.lower()).translate(self.E_ACCENTS_TRANSLATION_TABLE): raw_rubric
            for raw_rubric in _MODULE_RAW_KNOWN_RUBRICS
        }

        # Liste de rubriques connues, normalisées et triées pour la construction de regex.
        self.NORMALIZED_KNOWN_RUBRICS_FOR_PATTERN = [r.lower() for r in self._PREPARED_RAW_KNOWN_RUBRICS]

        self.KNOWN_RUBRICS_IMPLICIT_RE_PATTERN = "|".join(
            re.escape(r) for r in self.NORMALIZED_KNOWN_RUBRICS_FOR_PATTERN
        ) if self.NORMALIZED_KNOWN_RUBRICS_FOR_PATTERN else EMPTY_STRING

        self.COMPILED_GENERAL_CLEANUP_PATTERNS = [
            re.compile(p, flags=REGEX_FLAGS_I) for p in
            _prepare_raw_patterns_for_config(_MODULE_GENERAL_CLEANUP_REGEX_PATTERNS)
        ]

        self.JUNK_WORDS_SET = set(_MODULE_JUNK_WORDS_IF_ALONE)

        self.GENERIC_INTRO_PHRASES_TO_STRIP = _prepare_raw_patterns_for_config(
            [p.lower() for p in _MODULE_GENERIC_INTRO_STRINGS_TO_STRIP]
        )

        self.COMPILED_CONTENT_INTRO_PHRASES_TO_STRIP = [
            re.compile(p, flags=REGEX_FLAGS_I) for p in
            _prepare_raw_patterns_for_config(_MODULE_CONTENT_INTRO_REGEX_PATTERNS_TO_STRIP)
        ]
        self.REGEX_FLAGS_I = REGEX_FLAGS_I


class QueryParser:
    """
    Analyseur de requêtes en langage naturel (français).
    Transforme une chaîne de requête en une structure de données pour la recherche.
    """

    NORMALIZE_CONTEXT_STRICT_RUBRIC = "strict_rubric"  # Contexte pour normalisation stricte de rubriques.

    # Fragments Regex pour la capture de termes de rubrique.
    _RUBRIC_TERM_CAPTURE_PATTERN = r"(\"(?:[^\"]+)\"|(?:[\w'-]+(?:[\s][\w'-]+){0,3}?))"
    _RUBRIC_LOOKAHEAD_PATTERN = r"(?=\s+et\s+(?:la\s+|de\s+la\s+|dans\s+la\s+)?rubrique|\s+ou\s+(?:la\s+|de\s+la\s+|dans\s+la\s+)?rubrique|\s+et|\s+ou|\s+qui|\s+parlant|\s+mentionnant|\s+contenant|publiés\s+en|écrit\s+en|paru\s+en|$|,|\.|\?|!|\(|\s+dans\s+le\s+domaine)"

    def __init__(self):
        """Initialise le parser avec sa configuration."""
        self.config = QueryParserConfig()

    def _get_normalized_rubric_lookup_key(self, rubric_name: str | None) -> str | None:
        """Génère une clé normalisée (minuscules, sans accents/apostrophes) pour une rubrique."""
        if not rubric_name:
            return None
        normalized_name = normalize_apostrophes_globally(rubric_name.lower())
        if normalized_name is None:
            return None
        return normalized_name.translate(self.config.E_ACCENTS_TRANSLATION_TABLE)

    def get_canonical_rubric(self, rubric_name: str | None) -> str | None:
        """Retourne le nom canonique d'une rubrique à partir d'une variante."""
        if not rubric_name:
            return None
        normalized_lookup_key = self._get_normalized_rubric_lookup_key(rubric_name)
        return self.config.CANONICAL_RUBRICS_MAP.get(normalized_lookup_key, rubric_name)

    @staticmethod
    def _iterative_regex_cleanup(text: str | None,
                                 compiled_patterns: list[re.Pattern],
                                 strip_chars_for_each_sub: str,
                                 strip_chars_after_iteration: str) -> str | None:
        """Applique itérativement des regex de nettoyage sur un texte."""
        if not text:
            return text
        current_text = text
        while True:
            text_before_iteration = current_text
            for compiled_re_pattern in compiled_patterns:
                current_text = compiled_re_pattern.sub(EMPTY_STRING, current_text, count=1).strip(
                    strip_chars_for_each_sub)
                if not current_text:
                    break
            if not current_text:
                break
            current_text = current_text.strip(strip_chars_after_iteration)
            if current_text == text_before_iteration:
                break
        return current_text

    def normalize_str(self, s: str | None, context: str = "generic") -> str | None:
        """
        Normalise une chaîne: apostrophes, guillemets, ponctuation, regex, mots parasites.
        Le `context` peut influencer le niveau de nettoyage (ex: `NORMALIZE_CONTEXT_STRICT_RUBRIC`).
        """
        if not s:
            return s

        s_original_case = s
        current_text = normalize_apostrophes_globally(s)
        if current_text is None: return None

        current_text = current_text.replace("«", '"').replace("»", '"')
        current_text = current_text.strip(" \"'")
        current_text = current_text.strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)

        if context != self.NORMALIZE_CONTEXT_STRICT_RUBRIC:
            current_text = self._iterative_regex_cleanup(
                current_text,
                self.config.COMPILED_GENERAL_CLEANUP_PATTERNS,
                self.config.STRIP_CHARS_ALL,
                self.config.STRIP_CHARS_ALL
            )
            if current_text:
                current_text = current_text.strip(self.config.STRIP_CHARS_ALL)

        if not current_text:
            return None

        s_lower = current_text.lower()
        if context != self.NORMALIZE_CONTEXT_STRICT_RUBRIC:
            words_in_s_lower = s_lower.split()
            if words_in_s_lower and all(word in self.config.JUNK_WORDS_SET for word in words_in_s_lower):
                is_title_case_significant_original = s_original_case.istitle() and \
                                                     len(s_original_case) > 1 and \
                                                     s_original_case.lower() == s_lower
                is_upper_case_significant_original = s_original_case.isupper() and len(s_original_case) > 1

                if not (is_title_case_significant_original or is_upper_case_significant_original):
                    return None
        return current_text if current_text else None

    def parse_date_text(self, day_str: str | None, month_str: str | None, year_str: str) -> str | None:
        """Convertit jour, mois (français), année en format "YYYY-MM-DD"."""
        try:
            year = int(year_str)
            month_str_norm = None
            if month_str:
                month_str_lower = month_str.lower()
                month_str_norm = normalize_apostrophes_globally(month_str_lower)

            month = self.config.MONTHS_FR.get(month_str_norm, 1) if month_str_norm else 1
            day = int(day_str) if day_str else 1

            if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
                return None
            datetime(year, month, day) # Valide la date (ex: 30 février)
            return f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, KeyError, TypeError, AttributeError):
            return None

    @staticmethod
    def _parse_slash_date_to_iso(date_str_slashed: str | None) -> str | None:
        """Convertit une date "JJ/MM/AAAA" en "YYYY-MM-DD"."""
        if not date_str_slashed:
            return None
        try:
            return datetime.strptime(date_str_slashed, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None

    def _remove_and_cleanup_match_from_text(self, text: str, match_obj: re.Match) -> str:
        """Supprime un match regex du texte et nettoie les connecteurs orphelins."""
        text_after_removal = text[:match_obj.start()] + text[match_obj.end():]
        text_after_removal = re.sub(r"^\s*(et|ou|puis|donc|qui|[aà]|de|des|du)\s+", EMPTY_STRING, text_after_removal,
                                    flags=self.config.REGEX_FLAGS_I)
        text_after_removal = re.sub(r"\s+(et|ou)\s*$", EMPTY_STRING, text_after_removal,
                                    flags=self.config.REGEX_FLAGS_I)
        return text_after_removal.strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)

    def _apply_patterns_iteratively_and_extract(self, query_work: str,
                                                patterns_actions_list: list[tuple[str, callable]],
                                                process_match_callback: callable) -> str:
        """
        Applique itérativement une liste de (pattern, action) pour extraire des données.
        Modifie `query_work` en supprimant les parties traitées.
        """
        current_query_text = query_work
        while True:
            found_match_in_this_pass = False
            for pattern_str, action_lambda in patterns_actions_list:
                match = re.search(pattern_str, current_query_text, flags=self.config.REGEX_FLAGS_I)
                if match:
                    try:
                        extracted_data = action_lambda(match.groups(), self)
                        if process_match_callback(extracted_data): # Si le callback valide et traite les données
                            current_query_text = self._remove_and_cleanup_match_from_text(current_query_text, match)
                            found_match_in_this_pass = True
                            break # Recommence avec la liste de patterns sur le texte modifié
                    except (ValueError, KeyError, TypeError, AttributeError, IndexError):
                        pass  # Erreur de parsing (ex: date invalide), ignorer et continuer
            if not found_match_in_this_pass:
                break
        return current_query_text

    def _parse_terms_and_operator(self, text_segment: str) -> tuple[list[str], str | None]:
        """
        Extrait les termes de recherche et l'opérateur logique ("AND"/"OR") d'un segment de texte.
        Normalise les termes extraits.
        """
        terms = []
        operator = None
        text_lower = text_segment.lower()

        if " ou " in text_lower:
            operator = OP_OR
            parts = re.split(r"\s+ou\s+", text_segment, flags=self.config.REGEX_FLAGS_I)
        elif " et " in text_lower: # "et" a priorité plus faible que "ou" pour la division principale
            operator = OP_AND
            parts = re.split(r"\s+et\s+", text_segment, flags=self.config.REGEX_FLAGS_I)
        else:
            parts = [text_segment]

        for part_raw in parts:
            # Cas spécifique: "A ou B et C" -> si op principal est OR, "B et C" doit être traité comme un bloc.
            # Actuellement, le split principal par "ou" gère cela: B et C seront dans une même `part_raw`.
            # Il faut ensuite traiter le "et" dans cette `part_raw`.
            if operator == OP_OR and " et " in part_raw.lower():
                sub_parts_et = re.split(r"\s+et\s+", part_raw, flags=self.config.REGEX_FLAGS_I)
                for sub_term_raw in sub_parts_et:
                    term_norm = self.normalize_str(sub_term_raw.strip())
                    if term_norm: terms.append(term_norm)
            else:
                term_norm = self.normalize_str(part_raw.strip())
                if term_norm: terms.append(term_norm)

        if not terms or len(terms) <= 1: # Pas d'opérateur si un seul terme ou aucun.
            operator = None
        return terms, operator

    def _preprocess_query_input(self, query_input: str) -> str:
        """
        Pré-traite la chaîne de requête: normalisation globale, suppression des introductions génériques.
        """
        query_work_normalized = normalize_apostrophes_globally(query_input)
        if query_work_normalized is None:
            return EMPTY_STRING
        query_work = query_work_normalized.lower()
        query_work = query_work.replace("«", '"').replace("»", '"')

        # Suppression des phrases d'introduction génériques.
        for phrase_pattern_str in self.config.GENERIC_INTRO_PHRASES_TO_STRIP:
            pat = r"^\s*" + re.escape(phrase_pattern_str) + r"(?:\s+|[?.,!:](?:\s+|$)|$)"
            match = re.match(pat, query_work) # query_work est déjà en minuscules
            if match:
                query_work = query_work[match.end():].strip(self.config.STRIP_CHARS_ALL)
                break # Une seule phrase d'intro est retirée.
        return query_work

    def _extract_return_fields(self, query_work: str, structured_query: dict) -> str:
        """Détecte les demandes de retour de champs spécifiques (ex: "rubriques des articles")."""
        phrases_return_rubric = [
            "rubriques des articles",
            "dans quelles rubriques trouve-t-on des articles"
        ]
        for phrase in phrases_return_rubric:
            if phrase in query_work:  # query_work est déjà normalisé et en minuscules
                structured_query["return_fields"] = [RETURN_FIELD_RUBRIC]
                query_work = query_work.replace(phrase, EMPTY_STRING, 1).strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)
                break
        return query_work

    def _extract_has_image(self, query_work: str, structured_query: dict) -> str:
        """Détecte les demandes d'articles contenant des images."""
        img_phrases_patterns = [
            r"\bavec\s+(?:une|des)\s+images?\b",
            r"\b(?:articles\s+)?(?:contenant|contiennent|contain(?:s)?)\s+(?:une|des)\s+images?\b",
            r"\b(?:qui\s+)?(?:a|ont)\s+(?:une|des)\s+images?\b"
        ]
        for img_pattern in img_phrases_patterns:
            match = re.search(img_pattern, query_work, flags=self.config.REGEX_FLAGS_I)
            if match:
                structured_query["has_image"] = True
                query_work = self._remove_and_cleanup_match_from_text(query_work, match)
                break
        return query_work

    def _extract_negated_terms(self, query_work: str, structured_query: dict) -> str:
        """Extrait les termes de contenu niés (ex: "mais pas X") et les négations de mois."""
        # Capture de termes à nier (entre guillemets ou 1-3 mots).
        neg_term_capture = r"(\"(?:[^\"]+)\"|[^\s,.;\?!\(\)]+(?:\s+[^\s,.;\?!\(\)]+){0,2})"
        # Lookahead pour délimiter la fin du terme à nier.
        neg_lookahead = r"(?=\s+et|\s+ou|\s+dans|\s+pour|\s+qui|,|\.|\?|!|\(|\s+rubrique|$)"
        negation_patterns_config = [
            (rf"(?:mais\s+pas\s+de|mais\s+pas|non\s+pas\s+de|non\s+pas|et\s+non\s+pas\s+(?:la\s+|le\s+)?)\s*{neg_term_capture}{neg_lookahead}",
             1), # Le 1er groupe capturant est le terme.
            (rf"(?:mais\s+qui\s+ne\s+parle(?:nt)?\s+pas\s+(?:de|d'))\s*{neg_term_capture}{neg_lookahead}", 1),
            (rf"mais\s+(?:ne\s+contient\s+pas|pas\s+d['e])\s*{neg_term_capture}{neg_lookahead}", 1),
        ]

        current_query_text = query_work
        for pattern_str, term_group_idx in negation_patterns_config:
            def collect_negated_term_and_remove(match_obj: re.Match) -> str:
                term_to_negate_raw = match_obj.group(term_group_idx)
                term_to_negate_normalized = self.normalize_str(term_to_negate_raw)
                if term_to_negate_normalized:
                    structured_query["negated_content_terms"].append(term_to_negate_normalized)
                return EMPTY_STRING # La partie matchée est supprimée

            # Utilisation de re.sub avec une fonction de remplacement
            current_query_text = re.sub(pattern_str, collect_negated_term_and_remove, current_query_text,
                                        flags=self.config.REGEX_FLAGS_I)

        query_work = current_query_text.strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)

        # Extraction de la négation de mois (ex: "mais pas au mois de janvier")
        neg_month_pattern = rf"mais\s+pas\s+au\s+mois\s+de\s+({self.config.MONTHS_FR_RE_PATTERN})"
        match_neg_month = re.search(neg_month_pattern, query_work, flags=self.config.REGEX_FLAGS_I)
        if match_neg_month:
            month_name_raw = match_neg_month.group(1).lower()
            month_name_norm = normalize_apostrophes_globally(month_name_raw)
            if month_name_norm:
                month_val = self.config.MONTHS_FR.get(month_name_norm)
                if month_val:
                    structured_query["date_conditions"].append({DATE_EXCLUDE_MONTH: month_val})
                    query_work = self._remove_and_cleanup_match_from_text(query_work, match_neg_month)
        return query_work

    @staticmethod
    def _is_valid_parsed_date_condition(date_info: dict | None) -> bool:
        """Vérifie la validité d'une condition de date extraite."""
        if not date_info: return False
        dtype = date_info.get("type")
        if dtype == DATE_TYPE_RANGE:
            return bool(date_info.get("from") and date_info.get("to"))
        if dtype == DATE_TYPE_YEAR_RANGE:
            return date_info.get("from") is not None and date_info.get("to") is not None
        if dtype in [DATE_TYPE_EXACT_DATE, DATE_TYPE_AFTER]:
            return bool(date_info.get("date"))
        if dtype == DATE_TYPE_AFTER_YEAR:
            return date_info.get("year") is not None
        if dtype == DATE_TYPE_MONTH_YEAR:
            return date_info.get("month") is not None and date_info.get("year") is not None
        if dtype == DATE_TYPE_YEAR:
            return date_info.get("year") is not None
        return True # Pour DATE_EXCLUDE_MONTH, etc.

    def _extract_date_conditions(self, query_work: str, structured_query: dict) -> str:
        """Extrait diverses conditions de date (intervalle, après une date, date exacte, etc.)."""
        months_pattern = self.config.MONTHS_FR_RE_PATTERN

        # Lambdas d'action pour le parsing de dates
        action_range_text_date = lambda m, p: {"type": DATE_TYPE_RANGE,
                                               "from": p.parse_date_text(m[0], m[1], m[2]),
                                               "to": p.parse_date_text(m[3], m[4], m[5])}
        action_range_slash_date = lambda m, p: {"type": DATE_TYPE_RANGE,
                                                "from": QueryParser._parse_slash_date_to_iso(m[0]),
                                                "to": QueryParser._parse_slash_date_to_iso(m[1])}
        action_after_text_date = lambda m, p: {"type": DATE_TYPE_AFTER,
                                               "date": p.parse_date_text(m[0], m[1], m[2])}
        action_after_slash_date = lambda m, p: {"type": DATE_TYPE_AFTER,
                                                "date": QueryParser._parse_slash_date_to_iso(m[0])}
        action_after_month_year_or_year = lambda m, p: (
            {"type": DATE_TYPE_AFTER, "date": p.parse_date_text("1", m[0], m[1])} if m[0] else # Si mois présent
                {"type": DATE_TYPE_AFTER_YEAR, "year": int(m[1])}) # Sinon, année seule
        action_exact_text_date = lambda m, p: {"type": DATE_TYPE_EXACT_DATE,
                                               "date": p.parse_date_text(m[0], m[1], m[2])}
        action_year_range = lambda m, p: {"type": DATE_TYPE_YEAR_RANGE,
                                          "from": int(m[0]), "to": int(m[1])}
        action_month_year = lambda m, p: {"type": DATE_TYPE_MONTH_YEAR,
                                          "month": p.config.MONTHS_FR.get(
                                              normalize_apostrophes_globally(m[0].lower()) or ""),
                                          "year": int(m[1])}

        date_patterns_actions = [
            # Ex: "entre le 1 janvier 2020 et le 5 juin 2021"
            (rf"\bentre\s+(?:le\s+)?(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})\s+et\s+(?:le\s+)?(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})\b",
             action_range_text_date),
            # Ex: "entre 01/01/2020 et 05/06/2021"
            (r"\bentre\s+(?:le\s+)?(\d{1,2}/\d{1,2}/\d{4})\s+et\s+(?:le\s+)?(\d{1,2}/\d{1,2}/\d{4})\b",
             action_range_slash_date),
            # Ex: "après le 15 mars 2022"
            (rf"\b(?:après|[aà]\s+partir\s+de|daté(?:s)?\s*(?:[aà]\s+partir\s+de|après)|(?:qui\s+date|datant)\s+d'après|publiés\s+après)\s+(?:le\s+)?(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})\b",
             action_after_text_date),
            # Ex: "publiés après 15/03/2022"
            (r"\b(?:après|[aà]\s+partir\s+de|publiés\s+après)\s+(?:le\s+)?(\d{1,2}/\d{1,2}/\d{4})\b",
             action_after_slash_date),
            # Ex: "à partir de mars 2023" ou "après 2023"
            (rf"\b(?:après|[aà]\s+partir\s+de|daté(?:s)?\s*(?:[aà]\s+partir\s+de|après)|publiés\s+après|(?:qui\s+date|datant)\s+d'après)\s+(?:le\s+)?(?:({months_pattern})\s+)?(\d{{4}})\b",
             action_after_month_year_or_year),
            # Ex: "du 10 avril 2021"
            (rf"\b(?:du|datent\s+du|daté(?:s)?\s+au|le)\s+(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})\b",
             action_exact_text_date),
            # Ex: "entre 2020 et 2022"
            (r"\bentre\s+(\d{4})\s+et\s+(\d{4})\b", action_year_range),
            # Ex: "en janvier 2020" ou "publiés en janvier 2020"
            (rf"\b(?:(?:publiés|écrits|parus)\s+)?(?:au\s+mois\s+de\s+|en\s+|datés\s+)?({months_pattern})\s+(\d{{4}})\b",
             action_month_year),
        ]

        def process_date_match(date_info: dict) -> bool:
            """Callback pour traiter et valider une condition de date extraite."""
            if self._is_valid_parsed_date_condition(date_info):
                structured_query["date_conditions"].append(date_info)
                return True
            return False

        return self._apply_patterns_iteratively_and_extract(query_work, date_patterns_actions, process_date_match)

    def _extract_year_only(self, query_work: str, structured_query: dict, processed_years: set[str]) -> str:
        """
        Extrait les années seules (ex: "en 2020"), en évitant celles déjà traitées
        ou celles apparaissant à côté d'un mois (gérées par `_extract_date_conditions`).
        """
        year_only_patterns_config = [
            (r"\b(?:de\s+l'année|l'année|en|de)\s+(\d{4})\b", 1), # Année avec préposition
            (r"(?<!\d)\b(\d{4})\b(?!\d)", 1) # Année isolée (pas un nombre plus grand)
        ]
        current_query_text = query_work

        for year_pattern_re_str, year_group_idx in year_only_patterns_config:
            new_query_parts = []
            last_pos = 0
            for match_year in re.finditer(year_pattern_re_str, current_query_text, flags=self.config.REGEX_FLAGS_I):
                year_str = match_year.group(year_group_idx)
                try:
                    year_int = int(year_str)
                except ValueError:
                    year_int = 0 # Invalide

                is_valid_year_range = 1900 <= year_int < 2100
                is_already_processed = year_str in processed_years # Évite double comptage
                is_near_month_context = False # Pour le pattern d'année isolée

                if is_valid_year_range and not is_already_processed:
                    # Si c'est une année isolée, vérifier qu'un mois ne la précède pas directement.
                    if year_pattern_re_str == r"(?<!\d)\b(\d{4})\b(?!\d)":
                        context_len_before = self.config.MAX_MONTH_NAME_LEN + 3 # Longueur max d'un nom de mois + espace/ponctuation
                        context_before_year = current_query_text[
                                              max(0, match_year.start() - context_len_before):match_year.start()]
                        if re.search(rf"(?:{self.config.MONTHS_FR_RE_PATTERN})\s*$", context_before_year,
                                     flags=self.config.REGEX_FLAGS_I):
                            is_near_month_context = True # Probablement géré par _extract_date_conditions

                    if not is_near_month_context:
                        structured_query["date_conditions"].append({"type": DATE_TYPE_YEAR, "year": year_int})
                        processed_years.add(year_str)
                        new_query_parts.append(current_query_text[last_pos:match_year.start()])
                        last_pos = match_year.end()
                        continue # Match traité, passe au suivant

                # Si non traité, conserver la partie du texte
                new_query_parts.append(current_query_text[last_pos:match_year.end()])
                last_pos = match_year.end()

            new_query_parts.append(current_query_text[last_pos:])
            current_query_text = EMPTY_STRING.join(new_query_parts)

        return current_query_text.strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)

    def _extract_title_terms(self, query_work: str, structured_query: dict) -> str:
        """Extrait les termes spécifiquement destinés à la recherche dans le titre."""
        # Lookahead pour délimiter la fin du terme de titre.
        title_lookahead = r"(?=\s+dans\s+la\s+rubrique|\s+provenant\s+de\s+la\s+rubrique|\s+de\s+la\s+rubrique|publiés\s+en|écrit\s+en|paru\s+en|$|,|\.|\?|!|\(|\s+et\s+rubrique|\s+ou\s+rubrique)"
        title_term_capture = r"(.+?)" # Capture non-gourmande
        title_patterns_actions = [
            # Ex: "titre contient X" ou "dont le titre parle de X"
            (rf"(?:(?:dont\s+le|du)\s+)?titre\s+(?:contient|évoque|traite\s+(?:de|du)|parle\s+de)\s+(?:(?:le|les)\s+(?:mot|terme)s?\s+)?{title_term_capture}{title_lookahead}",
             lambda m, p: m[0]), # m[0] car 1er groupe après les non-capturants
            # Ex: "contenant X dans le titre"
            (rf"(?:contenant|mentionnant|parlant\s+de)\s+(?:(?:le|les)\s+(?:mot|terme)s?\s+)?{title_term_capture}\s+dans\s+le\s+titre{title_lookahead}",
             lambda m, p: m[0]),
        ]

        def process_title_match(title_terms_raw_from_match: str | None) -> bool:
            """Callback pour traiter les termes de titre extraits."""
            if not title_terms_raw_from_match:
                return False

            title_terms_raw = title_terms_raw_from_match.strip("\"'")
            # Nettoyer "et"/"ou" en fin de capture (si lookahead trop large)
            title_terms_raw = re.sub(r"\s+(et|ou)$", EMPTY_STRING, title_terms_raw,
                                     flags=self.config.REGEX_FLAGS_I).strip()

            current_match_terms, current_match_operator = self._parse_terms_and_operator(title_terms_raw)

            if current_match_terms:
                structured_query["title_terms"].extend(current_match_terms)
                # Gestion de l'opérateur: OR si un OU est détecté n'importe où.
                if structured_query["title_operator"] == OP_OR or current_match_operator == OP_OR:
                    if len(structured_query["title_terms"]) > 1: # Opérateur pertinent si >1 terme
                        structured_query["title_operator"] = OP_OR
                elif len(structured_query["title_terms"]) > 1: # Sinon AND par défaut
                    structured_query["title_operator"] = OP_AND
                return True
            return False

        return self._apply_patterns_iteratively_and_extract(query_work, title_patterns_actions, process_title_match)

    def _extract_explicit_rubric_combination(self, query_work: str, structured_query: dict) -> tuple[str, bool]:
        """
        Tente d'extraire une combinaison explicite de rubriques (ex: "rubrique X et Y", "rubrique X ou Y").
        Retourne le texte modifié et un booléen indiquant si une combinaison a été trouvée.
        """
        rubric_combo_pattern_str = (
            rf"(?:la\s+|de\s+la\s+|dans\s+la\s+)?rubrique\s+(?:est\s+)?" # Préfixe "rubrique"
            rf"{self._RUBRIC_TERM_CAPTURE_PATTERN}\s+(ou|et)\s+(?!rubrique\b)" # Rubrique1 + op (non suivi de "rubrique")
            rf"(?:(?:la\s+|de\s+la\s+|dans\s+la\s+)?rubrique\s+(?:est\s+)?)?" # Préfixe optionnel pour Rubrique2
            rf"{self._RUBRIC_TERM_CAPTURE_PATTERN}{self._RUBRIC_LOOKAHEAD_PATTERN}" # Rubrique2 + délimiteur
        )

        match_rubric_combo = re.search(rubric_combo_pattern_str, query_work, flags=self.config.REGEX_FLAGS_I)
        if match_rubric_combo:
            r1_raw = match_rubric_combo.group(1).strip("\"'") # `_RUBRIC_TERM_CAPTURE_PATTERN` est le 1er groupe
            op_str_raw = match_rubric_combo.group(2).strip().lower() # "ou" ou "et" est le 2e groupe
            r2_raw = match_rubric_combo.group(3).strip("\"'") # 2e `_RUBRIC_TERM_CAPTURE_PATTERN` est le 3e groupe

            r1_norm = self.normalize_str(r1_raw, context=self.NORMALIZE_CONTEXT_STRICT_RUBRIC)
            r2_norm_candidate = self.normalize_str(r2_raw, context=self.NORMALIZE_CONTEXT_STRICT_RUBRIC)

            # Valider que r2_norm_candidate est une rubrique connue si ce n'est pas entre guillemets.
            # Si r2_raw était entre guillemets, r2_norm_candidate le sera aussi, et on l'accepte.
            # Sinon, on vérifie si c'est une rubrique connue pour éviter de capturer du texte générique.
            r2_is_valid = False
            if r2_norm_candidate:
                if r2_norm_candidate.startswith('"') and r2_norm_candidate.endswith('"'):
                    r2_is_valid = True
                elif self._get_normalized_rubric_lookup_key(r2_norm_candidate) in self.config.CANONICAL_RUBRICS_MAP:
                    r2_is_valid = True


            if r1_norm and r2_norm_candidate and r2_is_valid:
                term1_canonical = self.get_canonical_rubric(r1_norm)
                term2_canonical = self.get_canonical_rubric(r2_norm_candidate)

                if term1_canonical: structured_query["rubric_terms"].append(term1_canonical)
                if term2_canonical: structured_query["rubric_terms"].append(term2_canonical)

                if len(list(set(structured_query["rubric_terms"]))) > 1:
                    structured_query["rubric_operator"] = OP_OR if op_str_raw == "ou" else OP_AND

                query_work = self._remove_and_cleanup_match_from_text(query_work, match_rubric_combo)
                return query_work, True
        return query_work, False

    def _extract_explicit_single_rubrics(self, query_work: str, structured_query: dict) -> tuple[str, bool]:
        """
        Extrait les rubriques uniques déclarées explicitement (ex: "de la rubrique X").
        Itère sur toutes les occurrences.
        Retourne le texte modifié et un booléen indiquant si au moins une rubrique explicite a été trouvée.
        """
        rubric_single_pattern_str = (
            rf"(?:(?:dont|de|dans|pour|provenant\s+de)\s+(?:la\s+)?)?rubrique\s+(?:est\s+)?" # Préfixe "rubrique"
            rf"{self._RUBRIC_TERM_CAPTURE_PATTERN}{self._RUBRIC_LOOKAHEAD_PATTERN}" # Rubrique + délimiteur
        )

        new_query_parts = []
        last_pos = 0
        explicit_rubric_found_this_method = False

        for match_rubric_single in re.finditer(rubric_single_pattern_str, query_work, flags=self.config.REGEX_FLAGS_I):
            rubric_raw = match_rubric_single.group(1).strip("\"'") # `_RUBRIC_TERM_CAPTURE_PATTERN`
            rubric_raw = re.sub(r"\s+(et|ou)$", EMPTY_STRING, rubric_raw, flags=self.config.REGEX_FLAGS_I).strip()
            rubric_norm = self.normalize_str(rubric_raw, context=self.NORMALIZE_CONTEXT_STRICT_RUBRIC)

            if rubric_norm:
                canonical_rubric = self.get_canonical_rubric(rubric_norm)
                structured_query["rubric_terms"].append(canonical_rubric)
                explicit_rubric_found_this_method = True
                new_query_parts.append(query_work[last_pos:match_rubric_single.start()]) # Texte avant le match
                last_pos = match_rubric_single.end() # Met à jour la position pour la prochaine itération
            else: # Si la normalisation donne None, on ne supprime pas, mais on avance
                new_query_parts.append(query_work[last_pos:match_rubric_single.end()])
                last_pos = match_rubric_single.end()


        new_query_parts.append(query_work[last_pos:]) # Ajoute le reste du texte
        current_query_text = EMPTY_STRING.join(new_query_parts).strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)

        if explicit_rubric_found_this_method:
            # Si plusieurs rubriques uniques ont été ajoutées sans opérateur explicite (par ex. via plusieurs "rubrique X"),
            # l'opérateur par défaut est AND.
            if len(list(set(structured_query["rubric_terms"]))) > 1 and not structured_query["rubric_operator"]:
                structured_query["rubric_operator"] = OP_AND
            # Nettoyer les connecteurs en début de chaîne restante.
            current_query_text = re.sub(r"^\s*(et|ou|puis|donc|qui|[aà]|de|des|du)\s+", EMPTY_STRING,
                                        current_query_text, flags=self.config.REGEX_FLAGS_I).strip(
                self.config.STRIP_CHARS_PUNCTUATION_ONLY)
        return current_query_text, explicit_rubric_found_this_method

    def _extract_implicit_rubrics(self, query_work: str, structured_query: dict) -> str:
        """
        Extrait les rubriques implicites (noms de rubriques connus apparaissant directement dans le texte).
        Seulement si aucune rubrique explicite n'a été trouvée avant.
        """
        if not self.config.KNOWN_RUBRICS_IMPLICIT_RE_PATTERN or not query_work:
            return query_work

        # On split par "et"/"ou" pour traiter les segments et potentiellement trouver un opérateur.
        parts = re.split(r"(\s+(?:et|ou)\s+)", query_work, flags=self.config.REGEX_FLAGS_I)

        implicit_rubrics_terms_found_this_call = []
        remaining_query_parts = [] # Parties du texte qui ne sont pas des rubriques implicites.
        operator_for_implicit = OP_AND # Par défaut AND pour les rubriques implicites trouvées.

        idx = 0
        last_part_was_implicit_rubric = False # Pour déterminer si un "ou" est entre deux rubriques.

        while idx < len(parts):
            part_text = parts[idx].strip()
            is_known_rubric = False
            if part_text: # Segment de texte potentiel
                normalized_part = self.normalize_str(part_text, context=self.NORMALIZE_CONTEXT_STRICT_RUBRIC)
                # Vérifier si la partie normalisée correspond à une rubrique connue.
                if normalized_part and self._get_normalized_rubric_lookup_key(
                        normalized_part) in self.config.CANONICAL_RUBRICS_MAP:
                    implicit_rubrics_terms_found_this_call.append(self.get_canonical_rubric(normalized_part))
                    is_known_rubric = True

            if not is_known_rubric: # Si ce n'est pas une rubrique, on garde ce segment.
                remaining_query_parts.append(parts[idx])

            last_part_was_implicit_rubric = is_known_rubric
            idx += 1

            if idx < len(parts):  # Opérateur (et/ou)
                op_text = parts[idx].strip().lower()
                # Si la partie précédente était une rubrique et l'opérateur est "ou",
                # et la partie suivante est aussi une rubrique (vérifié à la prochaine itération implicitement),
                # alors l'opérateur pour les rubriques implicites devient OR.
                if last_part_was_implicit_rubric: # Si un op suit une rubrique
                    if op_text == "ou": # Si c'est "ou", on le note pour l'opérateur global implicite
                        operator_for_implicit = OP_OR
                    # Si c'est "et", on ne fait rien de spécial, on le supprime car il connectait des rubriques.
                else: # Si l'opérateur ne suit pas une rubrique, on le garde.
                    remaining_query_parts.append(parts[idx])
                idx += 1


        if implicit_rubrics_terms_found_this_call:
            structured_query["rubric_terms"].extend(implicit_rubrics_terms_found_this_call)
            # Définir l'opérateur si plusieurs rubriques.
            if len(list(set(structured_query["rubric_terms"]))) > 1:
                if not structured_query["rubric_operator"] or operator_for_implicit == OP_OR:
                    structured_query["rubric_operator"] = operator_for_implicit
            # Retourner les parties du texte qui n'étaient pas des rubriques.
            return EMPTY_STRING.join(remaining_query_parts).strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)

        return query_work # Si aucune rubrique implicite trouvée, retourner le texte original.

    def _extract_rubric_terms(self, query_work: str, structured_query: dict) -> str:
        """
        Orchestre l'extraction des termes de rubriques:
        1. Combinaisons explicites ("rubrique X et Y").
        2. Rubriques uniques explicites ("rubrique X").
        3. Rubriques implicites (si aucune explicite trouvée).
        """
        current_query_text = query_work
        explicit_rubric_found = False

        # 1. Essayer d'extraire les combinaisons de rubriques explicites.
        current_query_text, found_combo = self._extract_explicit_rubric_combination(current_query_text,
                                                                                    structured_query)
        if found_combo:
            explicit_rubric_found = True

        # 2. Si pas de combinaison, essayer les rubriques uniques explicites (peut en trouver plusieurs).
        #    On ne le fait que si aucune combinaison n'a été trouvée pour éviter
        #    qu'une partie d'une combinaison (ex: "rubrique X" dans "rubrique X et Y")
        #    soit capturée ici par erreur.
        if not explicit_rubric_found:
            current_query_text, found_single = self._extract_explicit_single_rubrics(current_query_text,
                                                                                     structured_query)
            if found_single:
                explicit_rubric_found = True

        # 3. Si aucune rubrique explicite (ni combinaison, ni unique) n'a été trouvée,
        #    chercher les rubriques implicites.
        if not explicit_rubric_found:
            current_query_text = self._extract_implicit_rubrics(current_query_text, structured_query)

        return current_query_text

    def _extract_content_terms(self, query_work_for_content: str, structured_query: dict):
        """
        Extrait les termes de contenu généraux du texte restant après les autres extractions.
        Nettoie les introductions spécifiques au contenu.
        """
        temp_content_text = query_work_for_content
        # Nettoyage initial des connecteurs en début/fin
        temp_content_text = re.sub(r"^\s*(et|ou|puis|donc|qui|de|des|du|sur|pour)\s+", EMPTY_STRING, temp_content_text,
                                   flags=self.config.REGEX_FLAGS_I).strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)
        temp_content_text = re.sub(r"\s+(et|ou|puis|donc|qui|de|des|du|sur|pour)\s*$", EMPTY_STRING, temp_content_text,
                                   flags=self.config.REGEX_FLAGS_I).strip(self.config.STRIP_CHARS_PUNCTUATION_ONLY)
        if not temp_content_text: return

        # Nettoyage des phrases d'introduction de contenu (ex: "parlant de", "contenant les mots")
        temp_content_text_cleaned = self._iterative_regex_cleanup(
            temp_content_text,
            self.config.COMPILED_CONTENT_INTRO_PHRASES_TO_STRIP,
            self.config.STRIP_CHARS_ALL,
            self.config.STRIP_CHARS_ALL
        )
        remaining_content_text = temp_content_text_cleaned
        if remaining_content_text:
            remaining_content_text = remaining_content_text.strip(self.config.STRIP_CHARS_ALL)
        if not remaining_content_text: return

        extracted_terms = []
        operator_for_these_terms = OP_AND # Par défaut

        # Gestion du pattern "soit X, soit Y" ou "soit X ou Y" ou "soit X et Y"
        # Capture générique pour les termes après "soit".
        soit_pattern_prefix = r"soit\s+(?:(?:du|des|de\s+la|de\s+l'|de)\s+)?"
        # Différents connecteurs possibles entre les "soit".
        soit_pattern_connectors = r"(?:\s*,\s*" + soit_pattern_prefix + \
                                  r"|\s+(?:ou|et)\s+" + soit_pattern_prefix + \
                                  r"|\s+ou(?:\s+(?:du|des|de\s+la|de\s+l'|de))?\s*" + \
                                  r"|\s+et(?:\s+(?:du|des|de\s+la|de\s+l'|de))?\s*)"
        # Pattern complet: ^soit Terme1 Connecteur Terme2$
        soit_pattern = r"^\s*" + soit_pattern_prefix + r"(.+?)\s*" + soit_pattern_connectors + r"\s*(.+)$"


        match_soit = re.match(soit_pattern, remaining_content_text, flags=self.config.REGEX_FLAGS_I)

        if match_soit:
            parts_raw = [match_soit.group(1).strip(), match_soit.group(2).strip()]
            operator_for_these_terms = OP_OR # "soit X soit Y" implique un OU logique.
            for part_raw in parts_raw:
                # Chaque partie peut elle-même contenir des "et" (ex: "soit A et B ou C et D")
                sub_terms, _sub_op = self._parse_terms_and_operator(part_raw)
                extracted_terms.extend(sub_terms)
        else:
            # Si pas de "soit", parse standard des termes et opérateur.
            extracted_terms, operator_candidate = self._parse_terms_and_operator(remaining_content_text)
            if operator_candidate:
                operator_for_these_terms = operator_candidate

        if extracted_terms:
            structured_query["content_terms"].extend(extracted_terms)
            # Gestion de l'opérateur global de contenu.
            if structured_query["content_operator"] == OP_OR or operator_for_these_terms == OP_OR:
                if len(structured_query["content_terms"]) > 1:
                    structured_query["content_operator"] = OP_OR
            elif len(structured_query["content_terms"]) > 1: # Si pas de OR et >1 terme, alors AND.
                structured_query["content_operator"] = OP_AND

    def _apply_fallback_content(self, original_query_normalized: str | None,
                                query_text_at_fallback: str,
                                structured_query: dict):
        """
        Mécanisme de repli: si aucun critère principal (contenu, titre, rubrique, date, etc.)
        n'a été trouvé, utilise le texte restant (ou la requête originale normalisée)
        comme termes de contenu.
        """
        is_search_criteria_empty = not any([
            structured_query["content_terms"], structured_query["title_terms"],
            structured_query["rubric_terms"], structured_query["date_conditions"],
            structured_query["negated_content_terms"], structured_query["has_image"]
        ])

        # Si aucun critère et pas de demande de champ spécifique (ex: juste "rubriques des articles").
        if is_search_criteria_empty and not structured_query["return_fields"]:
            fallback_text_to_parse = query_text_at_fallback if query_text_at_fallback else original_query_normalized

            if fallback_text_to_parse:
                # Nettoyage des phrases d'intro de contenu
                cleaned_fallback_text = self._iterative_regex_cleanup(
                    fallback_text_to_parse,
                    self.config.COMPILED_CONTENT_INTRO_PHRASES_TO_STRIP,
                    self.config.STRIP_CHARS_ALL,
                    self.config.STRIP_CHARS_ALL
                )
                if cleaned_fallback_text:
                    cleaned_fallback_text = cleaned_fallback_text.strip(self.config.STRIP_CHARS_ALL)

                if cleaned_fallback_text:
                    fallback_terms, fallback_op = self._parse_terms_and_operator(cleaned_fallback_text)
                    if fallback_terms:
                        structured_query["content_terms"] = fallback_terms
                        structured_query["content_operator"] = fallback_op

    @staticmethod
    def _finalize_structured_query(structured_query: dict):
        """Nettoie et finalise la requête structurée: termes uniques, opérateurs par défaut."""
        for key_base in ["content", "title", "rubric"]:
            terms_list_key = f"{key_base}_terms"
            operator_key = f"{key_base}_operator"

            # Assurer l'unicité et le tri des termes.
            unique_terms = sorted(list(set(filter(None, structured_query[terms_list_key]))))
            structured_query[terms_list_key] = unique_terms

            # Ajuster l'opérateur: None si 0 ou 1 terme. AND par défaut si >1 terme et pas d'opérateur.
            if not unique_terms or len(unique_terms) <= 1:
                structured_query[operator_key] = None
            elif len(unique_terms) > 1 and structured_query[operator_key] is None:
                structured_query[operator_key] = OP_AND # Opérateur par défaut

        # Termes niés: unicité et tri.
        structured_query["negated_content_terms"] = sorted(
            list(set(filter(None, structured_query["negated_content_terms"])))
        )

    @staticmethod
    def _get_years_from_date_condition(date_condition: dict) -> list[str]:
        """Utilitaire pour extraire les années (sous forme de str) d'une condition de date structurée."""
        years = []
        year_val = date_condition.get("year") # Pour DATE_TYPE_YEAR, DATE_TYPE_MONTH_YEAR, DATE_TYPE_AFTER_YEAR
        if year_val is not None:
            years.append(str(year_val))

        # Pour DATE_TYPE_YEAR_RANGE
        if date_condition.get("type") == DATE_TYPE_YEAR_RANGE:
            if date_condition.get("from") is not None: years.append(str(date_condition.get("from")))
            if date_condition.get("to") is not None: years.append(str(date_condition.get("to")))

        # Pour DATE_TYPE_EXACT_DATE, DATE_TYPE_AFTER (format YYYY-MM-DD)
        date_str_val = date_condition.get("date")
        if date_str_val and isinstance(date_str_val, str) and len(date_str_val) >= 4: # Assure YYYY...
            years.append(date_str_val[:4])

        # Pour DATE_TYPE_RANGE (from/to au format YYYY-MM-DD)
        if date_condition.get("type") == DATE_TYPE_RANGE:
            from_date_str = date_condition.get("from")
            to_date_str = date_condition.get("to")
            if from_date_str and isinstance(from_date_str, str) and len(from_date_str) >= 4:
                years.append(from_date_str[:4])
            if to_date_str and isinstance(to_date_str, str) and len(to_date_str) >= 4:
                years.append(to_date_str[:4])

        return list(set(years)) # Uniques

    def process_query(self, query_input: str | None) -> dict:
        """
        Méthode principale pour analyser une requête utilisateur.
        Retourne un dictionnaire structuré représentant la requête.
        """
        query_input = query_input or EMPTY_STRING
        original_query_normalized_for_fallback = self.normalize_str(query_input)

        structured_query = {
            "content_terms": [], "content_operator": None,
            "title_terms": [], "title_operator": None,
            "rubric_terms": [], "rubric_operator": None,
            "date_conditions": [],
            "negated_content_terms": [],
            "has_image": False,
            "return_fields": None, # Ex: [RETURN_FIELD_RUBRIC]
            "raw_query": query_input
        }

        # 1. Pré-traitement initial de la requête.
        query_work = self._preprocess_query_input(query_input)

        # 2. Extractions spécifiques (champs à retourner, images, négations, dates).
        # L'ordre peut être important car chaque extraction modifie `query_work`.
        query_work = self._extract_return_fields(query_work, structured_query)
        query_work = self._extract_has_image(query_work, structured_query)
        query_work = self._extract_negated_terms(query_work, structured_query)
        query_work = self._extract_date_conditions(query_work, structured_query)

        # Collecter les années déjà traitées par `_extract_date_conditions` pour éviter redondance.
        processed_years_from_dates = set()
        for dc in structured_query["date_conditions"]:
            processed_years_from_dates.update(self._get_years_from_date_condition(dc))

        # 3. Extraction des années seules (non associées à des mois/jours).
        query_work = self._extract_year_only(query_work, structured_query, processed_years_from_dates)

        # 4. Extraction des termes de titre et de rubrique.
        query_work = self._extract_title_terms(query_work, structured_query)
        query_work = self._extract_rubric_terms(query_work, structured_query)

        # 5. Le texte restant est considéré comme termes de contenu.
        query_work_before_content_extraction = query_work # Conserver pour le fallback
        self._extract_content_terms(query_work_before_content_extraction, structured_query)

        # 6. Mécanisme de fallback si aucun critère principal n'a été trouvé.
        self._apply_fallback_content(original_query_normalized_for_fallback,
                                     query_work_before_content_extraction, # Utilise le texte avant la tentative d'extraction de contenu
                                     structured_query)

        # 7. Finalisation (termes uniques, opérateurs par défaut).
        self._finalize_structured_query(structured_query)

        return structured_query