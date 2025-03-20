
from typing import (
    List,
)
from .base.process_client import FileProcessClient
from ..transactions import Document, Image

from bs4 import BeautifulSoup
from datetime import datetime
import re


class BS4Parser(FileProcessClient[Document]):
    """
    Parses html files using beautiful soup to find specific data 
    and build instances of Document models.
    """

    def process(self, file: str) -> Document:

        soup = BeautifulSoup(file, "html.parser")

        document = Document()

        # Numéro
        span = soup.find('span', class_='style32')
        if span:
            text = span.get_text(strip=True)
            m = re.search(r'(\d+)', text)
            if m:
                document.numero = m.group(1)

        #Date
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Cherche une date au format aaaa/mm/jj (parfois un chiffre simple pour le jour ou le mois)
            m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', title_text)
            if m:
                yyyy, mm, dd = m.groups()
                dd = dd.zfill(2)
                mm = mm.zfill(2)
                date_str = f"{dd}/{mm}/{yyyy}"
                document.date = datetime.strptime(date_str, "%d/%m/%Y")

        #Rubrique et Titre
        ps = soup.find_all('p', class_='style96')
        for p in ps:
            span42 = p.find('span', class_='style42')
            span17 = p.find('span', class_='style17')
            if span42 and span17:
                document.rubrique = span42.get_text(strip=True)
                document.titre = span17.get_text(strip=True)
                break

        #Extraire Auteurs
        # Chercher le span contenant "Rédacteurs :"
        redacteurs_label = soup.find("span", class_="style28", string=re.compile("Rédacteur", re.IGNORECASE))
        if redacteurs_label:
            # Trouver le parent tr
            parent_tr = redacteurs_label.find_parent("tr")
            if parent_tr:
                # Dans la même ligne, trouver la cellule contenant l'information de l'auteur
                tds = parent_tr.find_all("td")
                if len(tds) > 1:
                    # Le deuxième <td> contient l'info de l'auteur
                    auteur_td = tds[1]
                    p_auteur = auteur_td.find("p", class_="style44")
                    if p_auteur:
                        document.auteur = p_auteur.get_text(separator=" ", strip=True)

        #Texte
        td = soup.find('td', class_='FWExtra2')
        if td:
            paragraphs = td.find_all('p')
            parts = []
            for p in paragraphs:
                # Ignorer le paragraphe qui contient rubrique et titre
                if p.find('span', class_='style42') and p.find('span', class_='style17'):
                    continue
                # Ignorer le paragraphe qui contient l'URL (généralement avec la classe style93)
                if p.get('class') and 'style93' in p.get('class'):
                    a = True
                    continue
                t = p.get_text(separator=" ", strip=True)
                if t:
                    parts.append(t)
            document.texte = "\n".join(parts)

        #Images
        div_center = soup.find('div', style=lambda s: s and "text-align: center" in s)
        if div_center:
            img_tag = div_center.find('img')
            if img_tag:
                url = img_tag.get("src", "").strip()
                legende = ''
                # Recherche d'une légende dans un span (class="style21")
                caption_span = div_center.find('span', class_='style21')
                if caption_span:
                    legende = caption_span.get_text(strip=True)
                document.images.append(Image(url=url, legende=legende))

        #Contact
        contact_label = soup.find("span", class_="style28",
                                  string=re.compile("Pour en savoir plus, contacts", re.IGNORECASE))
        if contact_label:
            parent_tr = contact_label.find_parent("tr")
            if parent_tr:
                tds = parent_tr.find_all("td")
                if len(tds) > 1:
                    # Le deuxième <td> contient l'info de contact
                    contact_td = tds[1]
                    p_contact = contact_td.find("p", class_="style44")
                    if p_contact:
                        document.contact = p_contact.get_text(separator=" ", strip=True)

        #Retourner le document
        return document
