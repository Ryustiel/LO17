
from typing import List, Dict, Tuple, Optional, Callable
from datetime import datetime
from pydantic import Field

import re
from functools import cached_property

from .base.xml_base_model import XMLBaseModel
from .base.base_document import BaseDocument


class Image(XMLBaseModel):
    """
    Represents an image in the document.
    """
    url: Optional[str] = Field(None, description="L'URL de l'image")
    legende: Optional[str] = Field(None, description="La légende affichée sous l'image.")


class Document(XMLBaseModel, BaseDocument):
    """
    Represents the information that we are looking for in the provided documents.
    """    
    @cached_property
    def zones(self):
        zones: Dict[str, Callable[["Document"], str]] = {
            "titre": lambda doc: doc.titre or "",
            "texte": lambda doc: doc.texte or "",
            "legendes": lambda doc: "".join([img.legende or "" for img in doc.images]),
        }
        return zones
    
    @cached_property
    def document_id(self) -> str:
        if self.fichier is None: raise ValueError("Le document n'a pas d'attribut fichier.")
        return self.fichier

    fichier: Optional[str] = Field(None,
        description="""
            Le nom du fichier d'après le chemin fourni.
        """
    )
    numero: Optional[str] = Field(None,
        description="""
            Un nombre unique qui identifie la revue dans laquelle est apparu l'article.
        """
    )
    date: Optional[datetime] = Field(None,
        description="""
            La date à laquelle l'article a été écrit.
        """
    )
    rubrique: Optional[str] = Field(None,
        description="""
            Le nom de la rubrique de journal dans laquelle est paru l'article.
            Dans les documents html, elle est typiquement encapsulée dans
            <p class="style96"> qui contient
            un <span class="style42"> (rubrique) 
            suivi d'un <span class="style17"> (titre).
        """
    )
    titre: Optional[str] = Field(None,
        description="""
            Le titre de l'article.
            Dans les documents html, elle est typiquement encapsulée dans
            <p class="style96"> qui contient
            un <span class="style42"> (rubrique) 
            suivi d'un <span class="style17"> (titre).
        """
    )
    auteur: Optional[str] = Field(None,
        description="""
            Le nom de l'auteur de l'article.
            Dans les doucments html, 
            il est souvent mentionné dans les objets paragraph
            qui spécifient "email" ou "adit".
        """
    )
    contact: Optional[str] = Field(None,
        description="""
            Les informations de contact des auteurs, 
            qui peuvent être des numéros de téléphone, des emails, ...
            Dans les documents html, elles sont typiquement encapsulées 
            dans le <span class="style28"> qui contient un label "Pour en savoir plus, contacts".
        """
    )
    texte: Optional[str] = Field(None,
        description="""
            Le contenu de l'article.
            Dans les documents html, il est typiquement encapsulé dans des paragraphs
            à l'intérieur de l'élément td <td class="FWExtra2">.
        """
    )
    images: List[Image] = Field([], 
        description="""
            La liste des images présentes dans l'article, 
            dans l'ordre d'apparition.
        """
    )
    
    @cached_property
    def tokens(self) -> Dict[str, Dict[str, int]]:
        """
        List all the words occurring in this document's fields and the number of times they occurred.
        Returns:
            A dictionary of field keys mapped to a dictionary of words and their counts.
        """
        tokens = {}
        
        for zone_name, zone_content in self.read_zones.items():
        
            word_counts = {}
            # Utilise \w+, trouve directement toutes les séquences alphanumériques
            for word in re.findall(r"\w+", zone_content):
                cleaned_lower = word.lower()  # Met en minuscule
                word_counts[cleaned_lower] = word_counts.get(cleaned_lower, 0) + 1
            
            tokens[zone_name] = word_counts
        
        return tokens
