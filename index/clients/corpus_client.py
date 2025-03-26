import math
import re
from typing import (
    List,
    Dict,
    Optional,
    Self,
    TYPE_CHECKING
)
from xml.dom import minidom
import xml.etree.ElementTree as ET
import pandas as pd
if TYPE_CHECKING:
    from ..transactions.document import Document # Type hint seulement
from .base.process_client import FileProcessClient
from ..transactions import CorpusDocument


class CorpusClient:
    """
    Représente et gère une collection de documents (CorpusDocument).
    Permet le chargement, la segmentation basique, la modification en mémoire
    et l'exportation XML du corpus.
    """
    documents: List[CorpusDocument]  # Utilise le type de base abstrait

    def __init__(self, documents: List['Document']):  # Utilise le type concret si connu
        self.documents = documents

    @classmethod
    def from_folder(cls, proces_client: FileProcessClient['Document'], folder_path: str,
                    limit: Optional[int] = None) -> Self:
        """
        Charge un corpus depuis un dossier en utilisant un FileProcessClient.
        """
        list_of_documents: List['Document'] = proces_client.process_folder(folder_path, limit=limit)
        # Vérification : S'assurer que les documents chargés sont bien des CorpusDocument
        if list_of_documents and not isinstance(list_of_documents[0], CorpusDocument):
            raise TypeError("Le proces_client doit retourner une liste d'objets héritant de CorpusDocument.")
        return cls(list_of_documents)

    def segmente(self) -> pd.DataFrame:
        """
        Extrait tous les tokens (mot, document_id) du corpus.
        Utilise la propriété 'corps' de chaque document.
        """
        rows = []
        for doc in self.documents:
            # Utiliser un attribut d'identification du document, ex: 'fichier'
            doc_id = getattr(doc, 'fichier', None) or f'doc_{id(doc)}'

            # La propriété 'corps' combine déjà les bons champs (titre, texte, etc.)
            # et cached_property gère la mise en cache
            doc_corpus = doc.corps
            if doc_corpus:
                for word in re.findall(r'\w+', doc_corpus):
                    cleaned_lower = word.lower()
                    rows.append({'token': cleaned_lower, 'document_id': doc_id})
        return pd.DataFrame(rows, columns=['token', 'document_id'])

    def apply_substitutions(self, anti_dict_path: str):
        """
        Applique les substitutions de l'anti-dictionnaire directement aux
        attributs des objets Document en mémoire, basé sur doc.corps_fields.

        Args:
            anti_dict_path: Chemin vers le fichier anti-dictionnaire (mot\t"").
        """
        print(f"Application des substitutions depuis {anti_dict_path} sur {len(self.documents)} documents...")
        modification_count = 0
        # Pré-charger les substitutions pour l'efficacité
        substitutions = {}
        try:
            with open(anti_dict_path, 'r', encoding='utf-8') as f:
                for ligne in f:
                    if ligne.strip():
                        parts = ligne.strip().split('\t')
                        if len(parts) >= 2:
                            mot = parts[0]
                            remplacement = parts[1].strip('"')
                            substitutions[mot] = remplacement
        except FileNotFoundError:
            print(
                f"Erreur critique: Fichier anti-dictionnaire '{anti_dict_path}' non trouvé. Aucune substitution appliquée.")
            return  # Arrêter si le fichier n'existe pas

        if not substitutions:
            print("Avertissement: Le fichier anti-dictionnaire est vide ou n'a pas pu être lu correctement.")
            # Continuer quand même pour invalider le cache si nécessaire ? Ou retourner ?
            # Pour l'instant, on continue mais on prévient.

        for i, doc in enumerate(self.documents):
            doc_modified = False
            # Itérer sur les champs définis comme faisant partie du 'corps' sémantique
            for field_name in doc.corps_fields:
                if hasattr(doc, field_name):
                    original_text = getattr(doc, field_name)
                    # Vérifier que c'est bien une chaîne et qu'elle n'est pas vide
                    if isinstance(original_text, str) and original_text:
                        # Utiliser la méthode statique pour appliquer les substitutions
                        modified_text = CorpusDocument.substituer_mots(original_text, anti_dict_path)

                        # Mettre à jour l'attribut de l'objet si le texte a changé
                        if modified_text != original_text:
                            setattr(doc, field_name, modified_text)
                            doc_modified = True

            if doc_modified:
                modification_count += 1
                # Si 'corps' est une @cached_property, il faut supprimer la valeur cachée
                # pour qu'elle soit recalculée la prochaine fois avec le texte modifié.
                if 'corps' in doc.__dict__:  # Vérifie si la valeur est dans le cache de l'instance
                    del doc.__dict__['corps']

            # Affichage de la progression
            if (i + 1) % 100 == 0 or i == len(self.documents) - 1:
                print(f"  ... {i + 1}/{len(self.documents)} documents traités.")

        print(f"Substitutions appliquées. {modification_count} documents ont été modifiés.")
        if modification_count > 0:
            print("Le cache de la propriété 'corps' a été invalidé pour les documents modifiés.")

    def save_to_xml(self, output_xml_path: str, root_tag: str = "corpus"):
        """
        Sérialise tous les documents du corpus (dans leur état actuel en mémoire)
        dans un fichier XML. Nécessite que les objets Document héritent de XMLBaseModel.

        Args:
            output_xml_path: Chemin du fichier XML à créer.
            root_tag: Nom de la balise racine pour le fichier XML.
        """
        print(f"Sauvegarde du corpus actuel ({len(self.documents)} documents) dans {output_xml_path}...")

        # Vérifier si les documents ont la méthode de sérialisation
        if not self.documents or not hasattr(self.documents[0], 'model_dump_xml'):
            print("Erreur: Les documents ne semblent pas avoir de méthode 'model_dump_xml'.")
            print("Assurez-vous qu'ils héritent d'une classe (ex: XMLBaseModel) la fournissant.")
            return

        # Créer l'élément racine
        root = ET.Element(root_tag)

        # Ajouter chaque document comme sous-élément
        for doc in self.documents:
            try:
                # Utiliser la méthode de sérialisation de l'objet Document
                # Le tag du document sera son nom de classe par défaut (ou ce que model_dump_xml retourne)
                doc_elem = doc.model_dump_xml(tag="bulletin")
                root.append(doc_elem)
            except Exception as e:
                print(f"Erreur lors de la sérialisation XML du document {getattr(doc, 'fichier', id(doc))}: {e}")
                # Optionnel : décider si on arrête ou continue avec les autres documents

        # Utiliser minidom pour un rendu "pretty"
        try:
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml_as_string = reparsed.toprettyxml(indent="  ", encoding="utf-8")

            with open(output_xml_path, "wb") as f:  # Écrire en mode binaire
                f.write(pretty_xml_as_string)

            print(f"Corpus sauvegardé avec succès dans '{output_xml_path}'.")

        except Exception as e:
            print(f"Erreur lors de la finalisation ou écriture du fichier XML '{output_xml_path}': {e}")


class CorpusTFIDFCalculator:
    """
    Calcule les métriques TF, IDF et TF-IDF pour un CorpusClient.
    Génère un fichier anti-dictionnaire basé sur un seuil IDF.
    """

    def __init__(self, corpus_client: CorpusClient, doc_id_field: str = 'fichier'):
        """
        Initialise le calculateur.
        Args:
            corpus_client: L'instance CorpusClient contenant les documents.
            doc_id_field: Le nom de l'attribut sur les objets Document à utiliser comme ID.
        """
        self.client = corpus_client
        # --- Utilise les documents DU CLIENT ---
        self.documents = self.client.documents

        if not self.documents:
            raise ValueError("Le corpus fourni via CorpusClient ne contient aucun document.")

        # Vérifie que le champ doc_id existe sur le premier document (suffisant si homogène)
        # Utilise hasattr() pour vérifier l'existence de l'attribut
        if not hasattr(self.documents[0], doc_id_field):
            raise ValueError(
                f"L'attribut '{doc_id_field}' spécifié comme doc_id_field n'existe pas sur les objets Document.")
        self.doc_id_field = doc_id_field

        # Caches internes pour les dataframes calculés
        self._tf_df: Optional[pd.DataFrame] = None
        self._idf_df: Optional[pd.DataFrame] = None
        self._tfidf_df: Optional[pd.DataFrame] = None

        # --- IMPORTANT : Si le contenu des documents peut être modifié (par apply_substitutions), ---
        # --- les DataFrames TF/IDF calculés précédemment deviennent invalides.                   ---
        # --- Il faudrait une logique pour les réinitialiser ou recalculer si nécessaire.         ---
        # --- Pour l'instant, on assume qu'on calcule TF/IDF *avant* la substitution,           ---
        # --- ou que l'utilisateur gère la réinitialisation de l'instance Calculator.          ---

    def _get_doc_id(self, doc: 'Document') -> str:  # Utilise le type concret pour l'attribut
        """Récupère l'ID du document de manière sécurisée."""
        doc_id = getattr(doc, self.doc_id_field, None)
        return doc_id if doc_id else f'doc_sans_id_{id(doc)}'

    def calculate_tf(self) -> pd.DataFrame:
        """
        Calcule la fréquence brute (TF) de chaque terme dans chaque document.
        Utilise la méthode doc.tokens() qui elle-même utilise doc.corps.
        Si le corps a été modifié et le cache invalidé, tokens() donnera les nouvelles fréquences.
        Returns:
            DataFrame avec colonnes ['document_id', 'mot', 'tf']
        """
        # Si le cache existe et qu'on ne force pas le recalcul, on le retourne
        if self._tf_df is not None:
            # TODO: Ajouter une logique pour forcer le recalcul si les documents ont été modifiés
            # print("Utilisation du cache TF.")
            return self._tf_df

        print("Recalcul de TF...")
        tf_data = []
        for doc in self.documents:
            doc_id = self._get_doc_id(doc)
            # tokens() reflète l'état actuel du document (après substitution si apply_substitutions a été appelé
            # ET que le cache de doc.corps a été invalidé)
            tokens_with_counts = doc.tokens()
            for token, count in tokens_with_counts.items():
                tf_data.append({'document_id': doc_id, 'mot': token, 'tf': count})

        self._tf_df = pd.DataFrame(tf_data)
        # Gérer le cas où il n'y a pas de données
        if self._tf_df.empty:
            print("Calcul TF terminé. Aucune donnée TF générée (corpus vide ou aucun token trouvé?).")
            # Assigner des colonnes vides pour éviter des erreurs plus tard
            self._tf_df = pd.DataFrame(columns=['document_id', 'mot', 'tf'])
        else:
            print(f"Calcul TF terminé. {len(self._tf_df)} entrées TF générées.")
        return self._tf_df

    # calculate_idf et calculate_tfidf restent globalement les mêmes,
    # mais dépendent maintenant de quand date _tf_df
    def calculate_idf(self) -> pd.DataFrame:
        """
        Calcule l'Inverse Document Frequency (IDF) pour chaque terme unique du corpus.
        Doit être appelé après calculate_tf() ou le force.
        Returns:
            DataFrame avec colonnes ['mot', 'idf']
        """
        if self._idf_df is not None:
            # TODO: Logique de re-calcul si TF a été recalculé
            # print("Utilisation du cache IDF.")
            return self._idf_df

        # Assure que TF est calculé (utilise le cache si disponible, sinon recalcule)
        tf_df = self.calculate_tf()
        # Si TF est vide, IDF l'est aussi
        if tf_df.empty:
            print("Calcul IDF : TF est vide, IDF sera vide aussi.")
            self._idf_df = pd.DataFrame(columns=['mot', 'idf'])
            return self._idf_df

        print("Recalcul de IDF...")
        N = len(self.documents)
        if N == 0:
            print("Calcul IDF: Nombre de documents N = 0.")
            self._idf_df = pd.DataFrame(columns=['mot', 'idf'])
            return self._idf_df

        # Calcul DF
        df = tf_df.groupby('mot')['document_id'].nunique().reset_index()
        df.rename(columns={'document_id': 'df'}, inplace=True)

        # Calcul IDF: idf = log10(N / df)
        df['idf'] = df['df'].apply(lambda dft: math.log10(N / dft) if 0 < dft < N else 0.0)
        # Note: log10(N/N) = log10(1) = 0. Si dft=0, ne devrait pas arriver si tf_df non vide.

        self._idf_df = df[['mot', 'idf']]
        print(f"Calcul IDF terminé. {len(self._idf_df)} mots uniques avec IDF calculé.")
        return self._idf_df

    def calculate_tfidf(self) -> pd.DataFrame:
        """
        Calcule le score TF-IDF pour chaque terme dans chaque document.
        Doit être appelé après calculate_tf() et calculate_idf().
        Returns:
            DataFrame avec colonnes ['document_id', 'mot', 'tf_idf']
        """
        if self._tfidf_df is not None:
            # TODO: Logique de re-calcul si TF ou IDF ont été recalculés
            # print("Utilisation du cache TF-IDF.")
            return self._tfidf_df

        # Assure que TF et IDF sont calculés
        tf_df = self.calculate_tf()
        idf_df = self.calculate_idf()

        if tf_df.empty or idf_df.empty:
            print("Calcul TF-IDF: TF ou IDF est vide. TF-IDF sera vide aussi.")
            self._tfidf_df = pd.DataFrame(columns=['document_id', 'mot', 'tf_idf'])
            return self._tfidf_df

        print("Recalcul de TF-IDF...")
        # Fusionner TF et IDF
        tfidf_df = pd.merge(tf_df, idf_df, on='mot', how='left')

        # Calculer TF-IDF = tf * idf
        # Remplacer les IDF manquants (si un mot était dans TF mais pas IDF, improbable) par 0
        tfidf_df['idf'].fillna(0, inplace=True)
        tfidf_df['tf_idf'] = tfidf_df['tf'] * tfidf_df['idf']

        self._tfidf_df = tfidf_df[['document_id', 'mot', 'tf_idf']]
        print(f"Calcul TF-IDF terminé. {len(self._tfidf_df)} entrées TF-IDF générées.")
        return self._tfidf_df

    # generate_anti_dict reste la même, elle utilise IDF
    def generate_anti_dict(self, idf_threshold: float = 0.1, output_file: str = "anti_dictionnaire.txt") -> str:
        """
        Génère l'anti-dictionnaire basé sur un seuil IDF.
        Les mots avec un IDF inférieur ou égal au seuil sont ajoutés.
        Args:
            idf_threshold: Le seuil IDF. Mots avec idf <= threshold sont ajoutés.
            output_file: Nom du fichier où sauvegarder l'anti-dictionnaire.
        Returns:
            Le chemin vers le fichier anti-dictionnaire créé.
        """
        # Assure que IDF est calculé
        idf_df = self.calculate_idf()
        if idf_df.empty:
            print("Génération Anti-Dict: IDF est vide. Aucun mot ne sera ajouté.")
            # Créer un fichier vide pour éviter des erreurs ?
            with open(output_file, 'w', encoding='utf-8') as f:
                pass  # Crée un fichier vide
            print(f"Fichier anti-dictionnaire vide créé à '{output_file}'")
            return output_file

        print(f"Génération de l'anti-dictionnaire avec seuil IDF <= {idf_threshold}...")
        # Sélectionner les mots
        stop_words_df = idf_df[idf_df['idf'] <= idf_threshold]

        print(f"Nombre de mots candidats pour l'anti-dictionnaire: {len(stop_words_df)}")
        if not stop_words_df.empty:
            print("Exemples de mots (les 20 avec le plus bas IDF parmi les candidats):")
            print(stop_words_df.sort_values(by='idf').head(20))
        else:
            print("Aucun mot trouvé avec un IDF inférieur ou égal au seuil.")

        # Écrire dans le fichier
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for mot in stop_words_df['mot']:
                    # Format: mot<tab>""<newline>
                    f.write(f"{mot}\t\"\"\n")
            print(f"Anti-dictionnaire sauvegardé dans '{output_file}'")
        except IOError as e:
            print(f"Erreur lors de l'écriture du fichier anti-dictionnaire '{output_file}': {e}")
            # Peut-être lever une exception ici ? Pour l'instant on retourne le nom prévu.

        return output_file