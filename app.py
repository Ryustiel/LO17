import streamlit as st
import time
from typing import List
from datetime import datetime
from index.transactions.document import Document, Image
from index.transactions.corpus import Corpus


# --- Fonctions de simulation du backend ---
@st.cache_resource # Cache le corpus pour éviter rechargements
def load_dummy_corpus() -> Corpus:
    """Charge un corpus factice."""
    docs = [
        Document(
            fichier="doc1.html",
            numero="101",
            date=datetime(2023, 1, 15),
            rubrique="Technologie",
            titre="L'Avenir de l'Intelligence Artificielle",
            auteur="Dr. Ada Lovelace",
            contact="ada@example.com",
            texte="L'intelligence artificielle (IA) progresse à pas de géant. Cet article explore les implications futures de l'IA dans divers secteurs, de la santé à l'éducation. Nous discutons des avancées récentes en apprentissage profond et en traitement du langage naturel.",
            images=[
                Image(url="https://via.placeholder.com/300x200.png?text=Robot+Futuriste",
                      legende="Un robot symbolisant l'IA."),
                Image(url="https://via.placeholder.com/300x200.png?text=Réseau+Neuronal",
                      legende="Visualisation d'un réseau de neurones.")
            ]
        ),
        Document(
            fichier="doc2.html",
            numero="102",
            date=datetime(2023, 2, 20),
            rubrique="Science",
            titre="Découvertes Récentes sur Mars",
            auteur="Dr. Carl Sagan Jr.",
            contact="carl.sagan.jr@example.com, Tel: 123-456-7890",
            texte="De nouvelles données envoyées par les rovers martiens suggèrent la présence passée d'eau liquide en abondance. Ces découvertes relancent le débat sur la possibilité de vie extraterrestre. L'analyse des roches sédimentaires est au coeur de ces recherches.",
            images=[
                Image(url="https://via.placeholder.com/300x200.png?text=Surface+de+Mars",
                      legende="Paysage martien capturé par un rover.")
            ]
        ),
        Document(
            fichier="doc3.txt",
            numero="103",
            date=datetime(2023, 3, 10),
            rubrique="Économie",
            titre="L'Impact des Cryptomonnaies",
            auteur="Prof. Satoshi Nakamoto III",
            texte="Les cryptomonnaies continuent de façonner le paysage financier mondial. Leur volatilité et les questions réglementaires restent des défis majeurs. Cet article analyse les tendances et les prédictions pour l'année à venir. Bitcoin et Ethereum sont au centre de l'attention.",
            images=[]
        ),
        Document(
            fichier="doc4.html",
            numero="104",
            date=datetime(2023, 4, 5),
            rubrique="Technologie",
            titre="Streamlit: Créer des applications web interactives en Python",
            auteur="Adrien Treuille",
            contact="info@streamlit.io",
            texte="Streamlit est un framework open-source qui permet de créer et de partager facilement de belles applications web personnalisées pour le machine learning et la data science, le tout en Python. Pas besoin de compétences en frontend ! L'IA peut bénéficier de ces outils pour la visualisation.",
            images=[
                Image(url="https://via.placeholder.com/300x200.png?text=Streamlit+Logo", legende="Logo de Streamlit")
            ]
        )
    ]
    return Corpus(documents=docs)


def search_documents(query: str, corpus: Corpus) -> List[Document]:
    """Simule une recherche par mot-clé (titre/texte)."""
    if not query:
        return []
    query_lower = query.lower()
    results: List[Document] = []
    for doc in corpus.documents:
        found_in_title = doc.titre and query_lower in doc.titre.lower()
        found_in_text = doc.texte and query_lower in doc.texte.lower()
        if found_in_title or found_in_text:
            results.append(doc)
    time.sleep(0.5 + len(query) * 0.05) # Simule délai
    return results


# --- Fonctions d'affichage ---
def display_document_details(doc: Document):
    """Affiche les détails d'un document."""
    with st.container(border=True):
        if doc.titre:
            st.subheader(doc.titre)

        meta_info = [
            f"**Auteur:** {doc.auteur}" if doc.auteur else None,
            f"**Date:** {doc.date.strftime('%d %B %Y')}" if doc.date else None,
            f"**Rubrique:** {doc.rubrique}" if doc.rubrique else None,
            f"**Numéro de revue:** {doc.numero}" if doc.numero else None,
            f"**Fichier source:** `{doc.fichier}`" if doc.fichier else None,
        ]
        st.caption(" | ".join(filter(None, meta_info)))

        if doc.texte:
            preview_text = (doc.texte[:300] + '...') if len(doc.texte) > 300 else doc.texte
            st.markdown(preview_text)
            if len(doc.texte) > 300:
                with st.expander("Lire la suite"):
                    st.markdown(doc.texte)

        if doc.images:
            if len(doc.images) > 1:
                cols = st.columns(len(doc.images))
                for i, img in enumerate(doc.images):
                    if img.url:
                        cols[i].image(img.url, caption=img.legende, use_container_width=True)
            elif doc.images[0].url:
                st.image(doc.images[0].url, caption=doc.images[0].legende, use_container_width=True)

        if doc.contact:
            with st.expander("Informations de contact"):
                st.markdown(doc.contact)


def display_search_results(results: List[Document], query: str):
    """Affiche l'en-tête et les documents des résultats."""
    st.header(f"Résultats pour \"{query}\" ({len(results)} trouvé{'s' if len(results) > 1 else ''})")
    for doc in results:
        display_document_details(doc)
        if len(results) > 1:
            st.divider()

# --- Configuration de la page ---
st.set_page_config(
    page_title="Moteur de Recherche",
    page_icon="📚",
    layout="wide"
)

# --- Initialisation de l'état de session ---
if "search_query" not in st.session_state:
    st.session_state.search_query = "" # Dernière requête soumise
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False
if "query_text_input_key" not in st.session_state:
    # Clé pour text_input, initialisée avec la dernière requête pour persistance
    st.session_state.query_text_input_key = st.session_state.search_query

# --- Chargement des données ---
corpus_data = load_dummy_corpus()

# --- Interface principale ---
st.title("📚 Moteur de Recherche de Documents")
st.markdown("Entrez votre requête pour rechercher dans le corpus de documents.")

# Formulaire de recherche
with st.form(key="search_form"):
    st.text_input(
        "Votre requête :",
        key="query_text_input_key", # Lie la valeur du champ à st.session_state
        placeholder="Ex: Intelligence Artificielle, Mars...",
        label_visibility="collapsed"
    )
    submitted = st.form_submit_button("Rechercher", type="primary", use_container_width=True)

# Traitement de la recherche
if submitted:
    current_query_from_input = st.session_state.query_text_input_key
    st.session_state.search_query = current_query_from_input # Stocke la requête active
    st.session_state.search_performed = True

    if st.session_state.search_query:
        with st.spinner(f"Recherche de '{st.session_state.search_query}'..."):
            st.session_state.search_results = search_documents(st.session_state.search_query, corpus_data)

        num_results = len(st.session_state.search_results)
        if num_results > 0:
            st.toast(f"{num_results} document{'s' if num_results > 1 else ''} trouvé{'s' if num_results > 1 else ''} !",
                     icon="✅")
        else:
            st.toast("Aucun document correspondant.", icon="🤷")
    else:
        # Requête soumise vide
        st.session_state.search_results = []
        st.toast("Veuillez entrer des termes de recherche.", icon="ℹ️")

# Affichage des résultats
if st.session_state.search_performed and st.session_state.search_query:
    st.divider()
    if st.session_state.search_results:
        display_search_results(st.session_state.search_results, st.session_state.search_query)
    else:
        st.warning(f"Aucun document trouvé pour \"{st.session_state.search_query}\".")

# Pied de page
st.divider()
st.caption(f"© {datetime.now().year} - Moteur de recherche Streamlit")