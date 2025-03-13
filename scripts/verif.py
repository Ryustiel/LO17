#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de vérification du fichier XML produit par le script d'indexation.

Ce script charge le fichier "corpus.xml", parcourt chacun des <bulletin> et vérifie que :
  - L’élément racine est <corpus>.
  - Pour chaque bulletin, les balises obligatoires (<fichier>, <numero>, <date>, <rubrique>, 
    <titre>, <auteur>, <texte>, <images> et <contact>) sont présentes.
  - Pour les éléments textuels (sauf <images>), le contenu n'est pas vide (un avertissement est affiché si c’est le cas).
  - La balise <date> respecte bien le format jj/mm/aaaa.
  - Pour la section <images>, pour chaque <image>, les balises <urlImage> et <legendeImage> existent 
    (et leur contenu n'est pas vide, le cas échéant).

Si tout est OK, le script affiche un message positif, sinon il affiche les erreurs rencontrées.
"""

import xml.etree.ElementTree as ET
import re

def verify_date_format(date_text):
    """
    Vérifie que la date est au format jj/mm/aaaa.
    Retourne True si le format est correct, False sinon.
    """
    pattern = r"^\d{2}/\d{2}/\d{4}$"
    return re.match(pattern, date_text.strip()) is not None

def verify_bulletin(bulletin):
    """
    Vérifie qu'un élément <bulletin> contient bien toutes les balises requises
    et que certaines d'entre elles (date, contenu textuel) ne sont pas vides.
    
    Retourne True si le bulletin est conforme, sinon False.
    """
    mandatory_tags = ["fichier", "numero", "date", "rubrique", "titre", "auteur", "texte", "images", "contact"]
    is_ok = True

    # Pour identifier le bulletin dans les messages d'erreur, on récupère le contenu de <fichier>.
    bulletin_id = bulletin.find("fichier").text if bulletin.find("fichier") is not None else "N/A"

    # Vérification de la présence de chaque balise obligatoire.
    for tag in mandatory_tags:
        elem = bulletin.find(tag)
        if elem is None:
            print(f"[Erreur] Bulletin '{bulletin_id}': l'élément <{tag}> est absent.")
            is_ok = False
        else:
            # Pour tous les tags autres que <images>, on vérifie que le contenu texte n'est pas vide.
            if tag != "images":
                if elem.text is None or elem.text.strip() == "":
                    print(f"[Avertissement] Bulletin '{bulletin_id}': l'élément <{tag}> est vide.")
            # Pour la date, vérification du format.
            if tag == "date" and elem.text is not None:
                if not verify_date_format(elem.text):
                    print(f"[Erreur] Bulletin '{bulletin_id}': la date '{elem.text.strip()}' n'est pas au format jj/mm/aaaa.")
                    is_ok = False

    # Vérification de la section <images> et de la présence de toutes les sous-balises pour chaque image.
    images_elem = bulletin.find("images")
    if images_elem is not None:
        images_list = images_elem.findall("image")
        # Il est possible qu'un bulletin ne contienne aucune image (ce n'est pas une erreur)
        for idx, img in enumerate(images_list, start=1):
            url_img = img.find("urlImage")
            legende_img = img.find("legendeImage")
            if url_img is None:
                print(f"[Erreur] Bulletin '{bulletin_id}': l'image (index {idx}) ne contient pas <urlImage>.")
                is_ok = False
            else:
                if url_img.text is None or url_img.text.strip() == "":
                    print(f"[Avertissement] Bulletin '{bulletin_id}': <urlImage> de l'image (index {idx}) est vide.")
            if legende_img is None:
                print(f"[Erreur] Bulletin '{bulletin_id}': l'image (index {idx}) ne contient pas <legendeImage>.")
                is_ok = False
            else:
                if legende_img.text is None or legende_img.text.strip() == "":
                    print(f"[Avertissement] Bulletin '{bulletin_id}': <legendeImage> de l'image (index {idx}) est vide.")
    return is_ok

def verify_xml_file(xml_filename):
    """
    Charge et vérifie le fichier XML.
    
    Retourne True si tous les bulletins sont conformes, sinon False.
    """
    try:
        tree = ET.parse(xml_filename)
    except Exception as e:
        print(f"[Erreur] Le fichier XML '{xml_filename}' n'a pas pu être chargé : {e}")
        return False

    root = tree.getroot()
    if root.tag != "corpus":
        print(f"[Erreur] L'élément racine doit être <corpus> mais il est <{root.tag}>.")
        return False

    bulletins = root.findall("bulletin")
    if not bulletins:
        print("[Erreur] Aucun <bulletin> n'a été trouvé dans le fichier XML.")
        return False
    
    all_ok = True
    for bulletin in bulletins:
        if not verify_bulletin(bulletin):
            all_ok = False

    if all_ok:
        print("Le fichier XML respecte toutes les consignes.")
    else:
        print("Le fichier XML présente des problèmes.")
    return all_ok

if __name__ == "__main__":
    xml_filename = "corpus3.xml"
    verify_xml_file(xml_filename)