import streamlit as st
import time
from typing import List
from datetime import datetime
from index.transactions.document import Document, Image
from index.transactions.corpus import Corpus

# --- Fonctions de simulation du backend ---
@st.cache_resource  # Cache la ressource pour ne la charger qu'une fois
def load_dummy_corpus() -> Corpus:
    """Charge un corpus de documents factices."""
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
    """
    Simule une recherche dans le corpus.
    Retourne les documents dont le titre ou le texte contient la requête.
    """
    if not query:
        return []

    query_lower = query.lower()
    results: List[Document] = []
    for doc in corpus.documents:  # corpus est un objet Corpus, corpus.documents est la liste
        match = False
        if doc.titre and query_lower in doc.titre.lower():
            match = True
        if not match and doc.texte and query_lower in doc.texte.lower():
            match = True
        # On pourrait aussi chercher dans les légendes des images ou d'autres champs
        # Par exemple, si on voulait chercher dans les légendes :
        # for img in doc.images:
        #     if img.legende and query_lower in img.legende.lower():
        #         match = True
        #         break
        if match:
            results.append(doc)

    # Simuler un délai pour la recherche
    time.sleep(0.5 + len(query) * 0.05)  # Délai plus long pour requêtes plus longues
    return results


# --- Configuration de la page Streamlit ---
st.set_page_config(
    page_title="Moteur de Recherche de Documents",
    page_icon="📚",
    layout="wide"  # Utilise toute la largeur de la page
)

# --- Initialisation de l'état de session ---
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_performed" not in st.session_state:
    st.session_state.search_performed = False  # Pour savoir si une recherche a été lancée

# --- Chargement des données (mis en cache) ---
corpus_data = load_dummy_corpus()

# --- Interface utilisateur ---
st.title("📚 Moteur de Recherche de Documents")
st.markdown("Entrez votre requête ci-dessous pour rechercher des documents.")

# Barre de recherche et bouton
search_container = st.container()
with search_container:
    query = st.text_input(
        "Votre requête :",
        value=st.session_state.search_query,
        placeholder="Ex: Intelligence Artificielle, Mars, Streamlit...",
        key="query_input_key"  # Ajout d'une clé pour robustesse
    )

    search_button_clicked = st.button("Rechercher", type="primary")

# Logique de recherche lorsque le bouton est cliqué
if search_button_clicked:
    st.session_state.search_query = query  # Mettre à jour la requête sauvegardée
    st.session_state.search_performed = True
    if query:
        with st.spinner(f"Recherche de '{query}'..."):
            st.session_state.search_results = search_documents(query, corpus_data)
    else:
        st.session_state.search_results = []  # Pas de requête, pas de résultats

# Affichage des résultats
if st.session_state.search_performed:
    st.divider()  # Séparateur visuel
    if st.session_state.search_results:
        st.header(
            f"Résultats pour \"{st.session_state.search_query}\" ({len(st.session_state.search_results)} trouvés)")

        for doc in st.session_state.search_results:
            with st.container(border=True):  # Encadre chaque résultat
                if doc.titre:
                    st.subheader(doc.titre)

                meta_info = []
                if doc.auteur:
                    meta_info.append(f"**Auteur:** {doc.auteur}")
                if doc.date:
                    meta_info.append(f"**Date:** {doc.date.strftime('%d %B %Y')}")
                if doc.rubrique:
                    meta_info.append(f"**Rubrique:** {doc.rubrique}")
                if doc.numero:
                    meta_info.append(f"**Numéro de revue:** {doc.numero}")
                if doc.fichier:
                    meta_info.append(f"**Fichier source:** `{doc.fichier}`")

                if meta_info:
                    st.caption(" | ".join(meta_info))

                if doc.texte:
                    # Utiliser st.markdown
                    preview_text = (doc.texte[:300] + '...') if len(doc.texte) > 300 else doc.texte
                    st.markdown(preview_text)
                    if len(doc.texte) > 300:
                        with st.expander("Lire la suite"):
                            st.markdown(doc.texte)

                if doc.images:
                    # Si plusieurs images, on les met l'une sous l'autre
                    for img in doc.images:
                        if img.url:
                            st.image(img.url, caption=img.legende if img.legende else None, use_container_width=True)

                if doc.contact:
                    with st.expander("Informations de contact"):
                        st.markdown(doc.contact)

    elif st.session_state.search_query:  # Recherche effectuée, mais pas de résultats
        st.warning(f"Aucun document trouvé pour \"{st.session_state.search_query}\".")
    else:  # Pas de requête entrée
        st.info("Veuillez entrer une requête pour lancer la recherche.")

# Pied de page
st.divider()
st.caption(f"Moteur de recherche propulsé par Streamlit - {datetime.now().year}")