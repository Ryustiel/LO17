import streamlit as st
import time
from typing import List, Optional, Union
from datetime import datetime
from index.transactions.document import Document
from dataclasses import dataclass, field
import re
import copy


# --- Modèles de données ---

@dataclass
class SearchResult:
    """Représente un résultat de recherche, incluant le document, son score et des extraits pertinents."""
    document: Document
    score: float = 0.0
    snippets: List[str] = field(default_factory=list)

    def __lt__(self, other: 'SearchResult') -> bool:
        """Permet le tri des résultats. Priorise le score, puis la date, puis le numéro de document."""
        if self.score != other.score:
            return self.score < other.score
        # Gestion des dates potentiellement None pour un tri cohérent
        date_self = self.document.date if self.document.date else datetime.min
        date_other = other.document.date if other.document.date else datetime.min
        if date_self != date_other:
            return date_self < date_other
        return self.document.numero < other.document.numero


# --- Fonctions de simulation du backend ---

from index import Corpus, InvertedIndex
from typing import Dict

@st.cache_resource
def load_corpus() -> Corpus:
    import os
    with open(os.path.join(os.getcwd(), "output", "corpus_initial.xml"), "r", encoding="utf-8") as f:
        corpus = Corpus.model_validate_xml(
            f.read(), 
            tags={"Corpus": "corpus", "documents": "bulletins", "Document": "bulletin", "Image": "image"}
        )
    return corpus
    
@st.cache_resource
def load_index() -> Dict[str, InvertedIndex]:
    import os, pandas
    index: Dict[str, InvertedIndex] = {}
    for zone in ["texte", "legendes", "titre"]:
        index[zone] = InvertedIndex.from_dataframe(pandas.read_csv(os.path.join(os.getcwd(), "output", "index_files", f"index_{zone}_lemmatized.xml"), sep="\t", encoding="utf-8"))
    return index

@st.cache_resource
def load_substitutions() -> Dict[str, str]:
    import pandas, os
    return pandas.read_csv(os.path.join(os.getcwd(), "output", "lemmatized_replacement.tsv"), sep="\t", encoding="utf-8", index_col=0, header=None).to_dict()[1]

def generate_snippets(text: Union[Optional[str],List[str]], queries: Union[str, List[str]], window_chars: int = 70, max_snippets: int = 3) -> List[str]:
    """
    Génère des extraits de texte (snippets) autour des occurrences d'un terme de recherche.
    Le terme recherché est mis en évidence en gras (Markdown).
    """

    if not text or not queries:
        return []

    if isinstance(queries, str):
        term_list = [queries]
    else:
        term_list = [q for q in queries if q]

    snippets = []
    text_lower = text.lower()
    # Créé une regex qui matche n'importe quel des termes de la liste
    escaped_terms = [re.escape(term.lower()) for term in term_list if term]
    pattern = re.compile(r'(' + '|'.join(escaped_terms) + r')', re.IGNORECASE)

    for match in pattern.finditer(text_lower):
        if len(snippets) >= max_snippets:
            break

        start_index, end_index = match.span()

        # Définit la fenêtre de l'extrait autour du terme trouvé.
        snippet_start = max(0, start_index - window_chars)
        snippet_end = min(len(text), end_index + window_chars)

        # Extrait le snippet du texte original pour conserver la casse.
        original_snippet_text = text[snippet_start:snippet_end]

        # Surligne le terme recherché dans l'extrait.
        highlighted_snippet = pattern.sub(lambda m: f"**{m.group(0)}**", original_snippet_text)

        # Ajoute des ellipses si l'extrait ne commence/finit pas avec le texte original.
        prefix = "... " if snippet_start > 0 else ""
        suffix = " ..." if snippet_end < len(text) else ""

        snippets.append(f"{prefix}{highlighted_snippet}{suffix}")

    return list(dict.fromkeys(snippets)) # Élimine les doublons tout en préservant l'ordre.


def search_documents_enhanced(query: str, corpus: Corpus) -> List[SearchResult]:
    """
    Effectue une recherche par mot-clé dans le corpus.
    Calcule un score de pertinence simple et génère des snippets pour chaque document correspondant.
    """
    if not query:
        return []

    query_lower = query.lower()
    results_list: List[SearchResult] = []

    for doc in corpus.documents:
        current_score = 0
        current_snippets: List[str] = []
        doc_matches = False # Indique si le document correspond à la requête.

        # Recherche et score dans le titre.
        if doc.titre:
            title_lower = doc.titre.lower()
            # Recherche d'occurrences exactes du mot/de l'expression.
            occurrences_in_title = len(re.findall(r'\b' + re.escape(query_lower) + r'\b', title_lower))
            if occurrences_in_title > 0:
                current_score += occurrences_in_title * 10 # Poids plus important pour le titre.
                doc_matches = True

        # Recherche et score dans le texte.
        if doc.texte:
            text_lower = doc.texte.lower()
            occurrences_in_text = len(re.findall(r'\b' + re.escape(query_lower) + r'\b', text_lower))
            if occurrences_in_text > 0:
                current_score += occurrences_in_text * 1 # Poids standard pour le texte.
                current_snippets.extend(generate_snippets(doc.texte, query_lower))
                doc_matches = True

        if doc_matches:
            results_list.append(SearchResult(document=doc, score=current_score, snippets=current_snippets))

    time.sleep(0.2 + len(query) * 0.02) # Simule un léger délai de traitement.

    # Trie les résultats par score de pertinence (décroissant).
    results_list.sort(key=lambda sr: sr.score, reverse=True)
    return results_list


# --- Fonctions d'affichage Streamlit ---

def display_search_result_item(result_item: SearchResult, query: str):
    """Affiche un élément de résultat de recherche de manière structurée."""
    doc = result_item.document

    with st.container(border=True): # Encadre chaque résultat pour une meilleure lisibilité.
        display_titre = doc.titre
        if doc.titre and query:
            try:
                # Surligne la requête dans le titre.
                pattern = re.compile(re.escape(query), re.IGNORECASE)
                display_titre = pattern.sub(lambda m: f"**{m.group(0)}**", doc.titre)
            except re.error:
                pass # En cas d'erreur regex, affiche le titre original.

        if display_titre:
            st.subheader(display_titre)

        # Affichage des métadonnées du document.
        meta_info_parts = [
            f"**Identifiant:** {doc.numero}" if doc.numero else None,
            f"**Auteur:** {doc.auteur}" if doc.auteur else None,
            f"**Date:** {doc.date.strftime('%d %B %Y')}" if doc.date else None,
            f"**Rubrique:** {doc.rubrique}" if doc.rubrique else None,
            f"**Fichier source:** `{doc.fichier}`" if doc.fichier else None,
            # f"**Pertinence (score):** {result_item.score:.0f}" # Score, affichage optionnel.
        ]
        st.caption(" | ".join(filter(None, meta_info_parts))) # Filtre les éléments vides.

        # Affichage des snippets contextuels.
        if result_item.snippets:
            st.markdown("###### Extraits contextuels :")
            for snippet in result_item.snippets:
                st.markdown(f"📝 {snippet}") # Markdown pour le gras des termes surlignés.

        # Option pour afficher le texte intégral.
        if doc.texte:
            with st.expander("Lire le texte intégral"):
                st.markdown(doc.texte)

        # Affichage des images associées.
        if doc.images:
            if len(doc.images) > 1: # Utilise des colonnes si plusieurs images.
                cols = st.columns(len(doc.images))
                for i, img in enumerate(doc.images):
                    if img.url:
                        cols[i].image(img.url, caption=img.legende, use_container_width=True)
            elif doc.images[0].url: # Affiche une seule image.
                st.image(doc.images[0].url, caption=doc.images[0].legende, use_container_width=True)

        # Option pour afficher les informations de contact.
        if doc.contact:
            with st.expander("Informations de contact"):
                st.markdown(doc.contact)


def display_search_results_list(results: List[SearchResult], query: str):
    """Affiche le titre des résultats et la liste des documents trouvés."""
    count = len(results)
    plural_s = 's' if count > 1 else ''
    st.header(f"Résultats pour \"{query}\" ({count} trouvé{plural_s})")

    for i, res_item in enumerate(results):
        display_search_result_item(res_item, query)
        if i < count - 1: # Ajoute un séparateur entre les résultats.
            st.divider()


# --- Configuration de la page Streamlit ---
st.set_page_config(
    page_title="Moteur de Recherche LO17",
    page_icon="📚",
    layout="wide"
)

# --- Initialisation de l'état de session ---
# Permet de conserver les informations entre les interactions de l'utilisateur.
if "search_query" not in st.session_state:
    st.session_state.search_query = ""  # Stocke la dernière requête effectivement soumise.
if "search_results" not in st.session_state:
    st.session_state.search_results = []  # Conserve les résultats de la dernière recherche.
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False # True si une recherche a été effectuée.
if "sort_by" not in st.session_state:
    st.session_state.sort_by = "Pertinence"  # Critère de tri par défaut.
if "current_query_input" not in st.session_state:
    # Contenu actuel du champ de texte de recherche
    st.session_state.current_query_input = st.session_state.search_query
if "build_query" not in st.session_state:
    # Contenu actuel du champ de texte de recherche
    st.session_state.build_query = None

# --- Chargement des données ---
CORPUS = load_corpus() # Charge le corpus au démarrage de l'application.
INDEX = load_index() # Charge l'index au démarrage de l'application.
SUBSTITUTIONS = load_substitutions() # Charge les substitutions de lemmatisation.

# --- Préparation des pipelines de lemmatisation ---
from typing import Callable
from index import Query, Corpus, InvertedIndex, spacy_lemmatize, correct_tokens

STANDARDIZE: Callable[[str], str] = lambda x: re.sub(r"[^\w\s]", "", re.sub(r"'", " ", x.strip().lower()))
# CORRECT_TOKENIZE_LEMMATIZE: Callable[[List[str]], List[str]] = lambda x: SUBSTITUTIONS.get(STANDARDIZE(x), None) or spacy_lemmatize(STANDARDIZE(x))[0]

lexicon = set(SUBSTITUTIONS.keys())
def CORRECT_TOKENIZE_LEMMATIZE(x: str) -> str:
    token = SUBSTITUTIONS.get(STANDARDIZE(x), None)
    if token:
        return token
    tokens = correct_tokens(tokens=[x], lexicon=lexicon)
    if tokens[0][0]:
        token = SUBSTITUTIONS.get(tokens[0][0], None)
        if token:
            return token
    return spacy_lemmatize(STANDARDIZE(x))[0]

def APPLY(q: Query, func: callable, fields: List[str]) -> Query:
    """Apply a function to the tokens in specified fields of a Query object."""
    for field in fields:
        setattr(q, field, [func(token) for token in getattr(q, field)] if isinstance(getattr(q, field), list) else func(getattr(q, field)))
    return q

def recherche_lemma_ia(query: str) -> List[Document]:
    q = Query.build(query)
    st.session_state.build_query = copy.deepcopy(q)  # Stocke la requête pour l'affichage des snippets.
    APPLY(q, CORRECT_TOKENIZE_LEMMATIZE, ["content_terms", "negated_content_terms", "title_terms"])
    APPLY(q, STANDARDIZE, ["rubric_terms", "negated_rubric_terms"])
    return q.search(documents={d.document_id: d for d in CORPUS.documents}, index=INDEX)

# --- Interface principale de l'application ---
st.title("📚 Moteur de Recherche de Documents LO17")
st.markdown("Entrez votre requête pour rechercher dans le corpus de documents. Les résultats peuvent être triés.")

# Formulaire de recherche.
with st.form(key="search_form"):
    query_input = st.text_input(
        "Votre requête :",
        key="current_query_input", # Lie ce champ à la variable d'état pour pré-remplissage/accès.
        placeholder="Ex: Intelligence Artificielle, Mars...",
        label_visibility="collapsed" # Masque le label "Votre requête :"
    )
    submitted = st.form_submit_button("Rechercher", type="primary", use_container_width=True)

# Traitement de la soumission du formulaire.
if submitted:
    st.session_state.search_query = st.session_state.current_query_input # Met à jour la requête active.
    st.session_state.search_performed = True

    if not st.session_state.search_query: # Si la requête est vide.
        st.session_state.search_results = []
        st.toast("Veuillez entrer des termes de recherche.", icon="ℹ️")
    else:
        with st.spinner(f"Recherche de '{st.session_state.search_query}'..."):
            # 1) Lancement de la recherche brute
            raw_results = recherche_lemma_ia(st.session_state.search_query)

            # 2) Si la recherche renvoie une liste de chaînes, on les stocke séparément
            if raw_results and isinstance(raw_results[0], str):
                st.session_state.search_string_results = raw_results
                st.session_state.search_results = []
            else:
                st.session_state.search_string_results = []
                # 3) Sinon on convertit en SearchResult pour l'affichage classique
                st.session_state.search_results = [
                    SearchResult(
                        document=d,
                        snippets=generate_snippets(
                            d.texte,
                            st.session_state.build_query.content_terms
                            if st.session_state.build_query.content_terms
                            else st.session_state.search_query.lower(),
                        ),
                    )
                    for d in raw_results
                ]
            # XXX Formerly : search_documents_enhanced(st.session_state.search_query, corpus_data)

        # Toast selon le type de résultat
        if st.session_state.search_string_results:
            st.toast(f"{len(st.session_state.search_string_results)} chaîne(s) brute(s) obtenue(s).", icon="ℹ️")
        else:
            num_results = len(st.session_state.search_results)
            if num_results > 0:
                st.toast(
                    f"{num_results} document{'s' if num_results > 1 else ''} trouvé{'s' if num_results > 1 else ''} !",
                    icon="✅")
            else:
                st.toast("Aucun document correspondant.", icon="🤷")

# Affichage des résultats et options de tri (si une recherche a été effectuée et qu'une requête existe).
if st.session_state.search_performed and st.session_state.search_query:
    # 1) Affichage de la liste brute de chaînes si présente
    if st.session_state.search_string_results:
        count_str = len(st.session_state.search_string_results)
        st.header(f"Résultats bruts pour “{st.session_state.search_query}” ({count_str})")
        for s in st.session_state.search_string_results:
            st.markdown(f"- `{s}`")
    # 2) Sinon affichage normal des documents
    elif st.session_state.search_results:
        # Options de tri.
        sort_options = ["Pertinence", "Date (plus récent d'abord)", "Date (plus ancien d'abord)"]
        st.radio(
            "Trier les résultats par :",
            options=sort_options,
            key="sort_by", # La sélection est stockée dans st.session_state.sort_by.
            horizontal=True,
        )

        # Applique le tri sélectionné.
        results_to_display = list(st.session_state.search_results) # Copie pour trier sans altérer l'ordre par pertinence.

        if st.session_state.sort_by == "Date (plus récent d'abord)":
            results_to_display.sort(key=lambda sr: sr.document.date if sr.document.date else datetime.min, reverse=True)
        elif st.session_state.sort_by == "Date (plus ancien d'abord)":
            results_to_display.sort(key=lambda sr: sr.document.date if sr.document.date else datetime.max, reverse=False)
        elif st.session_state.sort_by == "Pertinence":
            # Le tri par pertinence est déjà effectué par search_documents_enhanced.
            # Si l'utilisateur re-sélectionne "Pertinence", on retri explicitement.
            results_to_display.sort(key=lambda sr: sr.score, reverse=True)

        st.divider() # Séparateur visuel avant la liste des résultats.
        display_search_results_list(results_to_display, st.session_state.search_query)

    else: # Si la recherche a été effectuée mais n'a retourné aucun résultat.
        st.divider()
        st.warning(f"Aucun document trouvé pour \"{st.session_state.search_query}\".")

# Pied de page.
st.divider()
st.caption(f"© {datetime.now().year} - Moteur de recherche LO17")