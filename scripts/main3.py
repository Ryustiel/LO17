#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de préparation du corpus.
Pour chaque fichier HTML (.htm) présent dans le dossier 'BULLETINS',
on extrait les informations suivantes et on les écrit dans un fichier XML :
    - le nom du fichier
    - le numéro du bulletin (extrait du <span class="style32">, via les chiffres)
    - la date de parution (extrait du <title> puis reformaté en jj/mm/aaaa)
    - la rubrique (pour le bulletin, par exemple, le contenu d'un <span class="style42">)
    - le titre de l’article (par exemple le contenu d'un <span class="style17">)
    - l’auteur (détecté dans un paragraphe contenant "email" et "ADIT")
    - le texte de l’article (texte figurant dans le ou les <p> situés dans le <td class="FWExtra2">, en ignorant celui contenant rubrique/titre)
    - les images (URL et légende, ici recherchées dans un <div> centré)
    - les contacts (en localisant le repère « Pour en savoir plus, contacts »)
"""

import os
import glob
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# ---------------------------
# Fonctions d'extraction
# ---------------------------

def extract_numero(soup):
    """
    Extrait le numéro du bulletin depuis le premier <span class="style32">.
    On recherche dans ce texte une séquence de chiffres.
    """
    numero = ''
    span = soup.find('span', class_='style32')
    if span:
        text = span.get_text(strip=True)
        m = re.search(r'(\d+)', text)
        if m:
            numero = m.group(1)
    return numero

def extract_date(soup):
    """
    Extrait la date de parution.
    On commence par analyser le <title> qui contient généralement une date 
    au format "aaaa/mm/jj" et on la reformate en "jj/mm/aaaa".
    Si non trouvée, on cherche un motif dans l'ensemble du document.
    """
    date_str = ''
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
            return date_str
    # Si non trouvé dans le titre, recherche dans l'ensemble du document un pattern date.
    for span in soup.find_all('span'):
        m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', span.get_text())
        if m:
            dd, mm, yyyy = m.groups()
            dd = dd.zfill(2)
            mm = mm.zfill(2)
            date_str = f"{dd}/{mm}/{yyyy}"
            return date_str
    return date_str

def extract_rubrique(soup):
    """
    Extrait la rubrique.
    Dans les bulletins comme 67068.htm, la rubrique se trouve dans un <p class="style96">
    qui contient à la fois un <span class="style42"> (rubrique) suivi d'un <span class="style17"> (titre).
    """
    rubrique = ''
    ps = soup.find_all('p', class_='style96')
    for p in ps:
        span42 = p.find('span', class_='style42')
        span17 = p.find('span', class_='style17')
        if span42 and span17:
            rubrique = span42.get_text(strip=True)
            break
    if not rubrique:
        print("[Avertissement] Bulletin : l'élément <rubrique> est vide.")
    return rubrique

def extract_titre(soup):
    """
    Extrait le titre de l’article.
    Pour cela, on recherche dans le même <p class="style96"> que la rubrique la balise <span class="style17">
    """
    titre = ''
    ps = soup.find_all('p', class_='style96')
    for p in ps:
        span42 = p.find('span', class_='style42')
        span17 = p.find('span', class_='style17')
        if span42 and span17:
            titre = span17.get_text(strip=True)
            break
    if not titre:
        print("[Avertissement] Bulletin : l'élément <titre> est vide.")
    return titre

def extract_auteur(soup):
    """
    Extrait l’auteur de l’article.
    On parcourt les paragraphes (ici en cherchant ceux contenant 'email' et 'ADIT').
    """
    auteur = ''
    for p in soup.find_all('p'):
        text = p.get_text(separator=" ", strip=True)
        if "email" in text.lower() and "adit" in text.lower():
            auteur = text
            break
    return auteur

def extract_texte(soup):
    """
    Extrait le texte de l’article.
    On cible le premier <td class="FWExtra2"> et on récupère tous les <p> qu’il contient
    en ignorant celui qui contient à la fois <span class="style42"> et <span class="style17"> (rubrique/titre).
    """
    texte = ''
    td = soup.find('td', class_='FWExtra2')
    if td:
        paragraphs = td.find_all('p')
        parts = []
        for p in paragraphs:
            # Ignorer le paragraphe qui contient rubrique et titre
            if p.find('span', class_='style42') and p.find('span', class_='style17'):
                continue
            t = p.get_text(separator=" ", strip=True)
            if t:
                parts.append(t)
        texte = "\n".join(parts)
    return texte

def extract_images(soup):
    """
    Extrait l’information relative aux images.
    Ici, on recherche un <div> avec un style indiquant "text-align: center" (souvent d’où provient l'image et sa légende).
    """
    images_list = []
    div_center = soup.find('div', style=lambda s: s and "text-align: center" in s)
    if div_center:
        img_tag = div_center.find('img')
        if img_tag:
            url = img_tag.get("src", "").strip()
            legende = ''
            # Recherche d'une légende dans un span (par exemple class="style21")
            caption_span = div_center.find('span', class_='style21')
            if caption_span:
                legende = caption_span.get_text(strip=True)
            images_list.append({"urlImage": url, "legendeImage": legende})
    return images_list

def extract_contact(soup):
    """
    Extrait les informations de contact.
    Ici, on recherche le repère du bloc de contact en ciblant le <span class="style28"> qui contient
    le texte "Pour en savoir plus, contacts" et on récupère le contenu du <td> voisin.
    """
    contact = ''
    contact_label = soup.find("span", class_="style28", text=re.compile("Pour en savoir plus, contacts", re.IGNORECASE))
    if contact_label:
        parent_tr = contact_label.find_parent("tr")
        if parent_tr:
            tds = parent_tr.find_all("td")
            if len(tds) > 1:
                # Le deuxième <td> contient l'info de contact
                contact_td = tds[1]
                p_contact = contact_td.find("p", class_="style44")
                if p_contact:
                    contact = p_contact.get_text(separator=" ", strip=True)
    return contact

# ---------------------------
# Traitement d'un fichier HTML
# ---------------------------

def process_file(filepath):
    """
    Ouvre le fichier HTML et extrait l'ensemble des informations
    nécessaires pour constituer le bulletin.
    Renvoie un dictionnaire contenant toutes ces informations.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    bulletin_info = {
        "fichier": os.path.basename(filepath),
        "numero": extract_numero(soup),
        "date": extract_date(soup),
        "rubrique": extract_rubrique(soup),
        "titre": extract_titre(soup),
        "auteur": extract_auteur(soup),
        "texte": extract_texte(soup),
        "images": extract_images(soup),
        "contact": extract_contact(soup)
    }
    return bulletin_info

# ---------------------------
# Construction de l'XML
# ---------------------------

def build_xml(bulletins):
    """
    Construit un arbre XML à partir de la liste des bulletins.
    La structure suit exactement l’arborescence demandée dans l’énoncé
    """
    root = ET.Element("corpus")
    for b in bulletins:
        bulletin_elem = ET.SubElement(root, "bulletin")
        
        ET.SubElement(bulletin_elem, "fichier").text = b["fichier"]
        ET.SubElement(bulletin_elem, "numero").text = b["numero"]
        ET.SubElement(bulletin_elem, "date").text = b["date"]
        ET.SubElement(bulletin_elem, "rubrique").text = b["rubrique"]
        ET.SubElement(bulletin_elem, "titre").text = b["titre"]
        ET.SubElement(bulletin_elem, "auteur").text = b["auteur"]
        ET.SubElement(bulletin_elem, "texte").text = b["texte"]

        images_elem = ET.SubElement(bulletin_elem, "images")
        for img in b["images"]:
            image_elem = ET.SubElement(images_elem, "image")
            ET.SubElement(image_elem, "urlImage").text = img["urlImage"]
            ET.SubElement(image_elem, "legendeImage").text = img["legendeImage"]

        ET.SubElement(bulletin_elem, "contact").text = b["contact"]

    return ET.ElementTree(root)

# ---------------------------
# Fonction principale
# ---------------------------

def main():
    bulletin_dir = "BULLETINS"  # Le dossier contenant les fichiers .htm
    bulletin_files = glob.glob(os.path.join(bulletin_dir, "*.htm"))
    
    bulletins = []
    for filepath in bulletin_files:
        print(f"Traitement de {filepath} …")
        bulletin_info = process_file(filepath)
        bulletins.append(bulletin_info)

    xml_tree = build_xml(bulletins)
    output_file = "corpus3.xml"
    xml_tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Le corpus XML a été généré dans {output_file}")

if __name__ == "__main__":
    main()