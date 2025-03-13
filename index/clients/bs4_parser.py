
from typing import (
    List,
)
from .process_client import FileProcessClient
from ..transactions.document import Document

from bs4 import BeautifulSoup
import re


class BS4Parser(FileProcessClient[Document]):
    """
    Parses html files using beautiful soup to find specific data 
    and build instances of Document models.
    """

    def process(self, file: str) -> Document:

        soup = BeautifulSoup(file, "html.parser")

        document = Document()

        span = soup.find('span', class_='style32')
        if span:  # Recherche du numero
            text = span.get_text(strip=True)
            m = re.search(r'(\d+)', text)
            if m:
                document.numero = m.group(1)

        ps = soup.find_all('p', class_='style96')
        for p in ps:  # Recherche de la rubrique
            span42 = p.find('span', class_='style42')
            span17 = p.find('span', class_='style17')
            if span42 and span17:
                document.rubrique = span42.get_text(strip=True)
                document.titre = span17.get_text(strip=True)
                break

        redacteurs_label = soup.find("span", class_="style28", string=re.compile("Rédacteur", re.IGNORECASE))
        if redacteurs_label:  # Recherche des auteurs
            parent_tr = redacteurs_label.find_parent("tr")
            if parent_tr:
                tds = parent_tr.find_all("td")  # Dans la même ligne, trouver la cellule contenant l'information de l'auteur
                if len(tds) > 1:
                    auteur_td = tds[1]  # Le deuxième <td> contient l'info de l'auteur
                    p_auteur = auteur_td.find("p", class_="style44")
                    if p_auteur:
                        document.auteur = p_auteur.get_text(separator=" ", strip=True)

        return document
