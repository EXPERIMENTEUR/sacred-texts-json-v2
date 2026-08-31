import requests
from bs4 import BeautifulSoup
import json
import re
import time
import ftfy

headers = {"User-Agent": "TelechargementPersonnel/1.0 (usage prive; contact: jerom_yapo@outlook.fr)"}

titres_tablettes = {
    1: "Of the Tyranny of Gilgamish, and the Creation of Enkidu",
    2: "Of the Meeting of Gilgamish and Enkidu",
    3: "The Expedition to the Forest of Cedars against Humbaba",
    4: "The Arrival at the Gate of the Forest",
    5: "Of the Fight with Humbaba",
    6: "Of the Goddess Ishtar, Who Fell In Love With the Hero",
    7: "The Death of Enkidu",
    8: "Of the Mourning of Gilgamish, and What Came of It",
    9: "Gilgamish In Terror of Death Seeks Eternal Life",
    10: "How Gilgamish Reached Uta-Napishtim",
    11: "The Flood",
    12: "Gilgamish, In Despair, Enquires of the Dead"
}

def extraire_texte(soup):
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    texte = soup.get_text(separator="\n")
    texte = ftfy.fix_text(texte)
    texte = texte.replace("Â", "")
    texte = texte.replace("â€\"", "—")
    texte = texte.replace("â€™", "'")
    if "at sacred-texts.com" in texte:
        parties = texte.split("at sacred-texts.com", 1)
        texte = parties[1] if len(parties) > 1 else texte

    if "Footnotes" in texte:
        texte = texte.split("Footnotes", 1)[0]
    if "Next:" in texte:
        texte = texte.split("Next:", 1)[0]

    texte = re.sub(r"\[\d+\]\(#fn_\d+\)", "", texte)
    texte = re.sub(r"p\.\s*\d+", "", texte)
    texte = re.sub(r"_{5,}", "", texte)
    texte = re.sub(r"\n{2,}", "\n\n", texte)
    return texte.strip()

tablettes = []

for num in range(1, 13):
    num_fichier = num + 2
    url = f"https://sacred-texts.com/ane/eog/eog{num_fichier:02d}.htm"
    print(f"Telechargement Tablette {num}...")
    try:
        r = requests.get(url, headers=headers)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        texte_propre = extraire_texte(soup)

        tablette_obj = {
            "tablet": num,
            "title": titres_tablettes.get(num, ""),
            "source": url,
            "text": texte_propre
        }
        tablettes.append(tablette_obj)
        print(f"  {len(texte_propre)} caracteres extraits")
        time.sleep(1)
    except Exception as e:
        print(f"  ERREUR Tablette {num} : {e}")

with open("gilgamesh_complete.json", "w", encoding="utf-8") as f:
    json.dump({
        "book": "The Epic of Gilgamish",
        "translator": "R. Campbell Thompson (1928)",
        "note": "Domaine public aux Etats-Unis depuis janvier 2024 (regle des 95 ans). Source: sacred-texts.com. La Tablette XI contient le recit du Deluge.",
        "tablets": tablettes
    }, f, ensure_ascii=False, indent=2)

print("Termine ! Fichier gilgamesh_complete.json cree (12 tablettes).")