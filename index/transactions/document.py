
from typing import (
    List,
    Optional,
)
from pydantic import Field
from ._xml_base_model import XMLBaseModel
from datetime import datetime


class Image(XMLBaseModel):
    """
    Represents an image in the document.
    """
    url: Optional[str] = Field(None, description="L'URL de l'image")
    legende: Optional[str] = Field(None, description="La légende affichée sous l'image.")


class Document(XMLBaseModel):
    """
    Represents the information that we are looking for in the provided documents.
    """
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
