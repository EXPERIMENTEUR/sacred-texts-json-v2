import requests
from bs4 import BeautifulSoup
import json
import re
import time

headers = {"User-Agent": "TelechargementPersonnel/1.0 (usage prive; contact: jerom_yapo@outlook.fr)"}

def nettoyer_texte(soup):
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    texte = soup.get_text(separator="\n")
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    texte = re.sub(r"[ \t]+", " ", texte)
    return texte.strip()

# --- Setna I : Setne Khamwas et Naneferkaptah ---
print("Telechargement de Setna I...")
r1 = requests.get("https://www.attalus.org/egypt/setne.html", headers=headers)
r1.encoding = "utf-8"
soup1 = BeautifulSoup(r1.text, "html.parser")
texte1 = nettoyer_texte(soup1)

setna1 = {
    "titre": "Setne Khamwas et Naneferkaptah (Setna I)",
    "type": "Recit de fiction egyptien, periode ptolemaique (~300-30 av. J.-C.), mentionnant le Livre de Thot legendaire",
    "traducteur": "M. Lichtheim",
    "source": "https://www.attalus.org/egypt/setne.html",
    "texte": texte1
}

with open("setna_1.json", "w", encoding="utf-8") as f:
    json.dump(setna1, f, ensure_ascii=False, indent=2)
print("Setna I sauvegarde.")

time.sleep(2)

# --- Setna II : Setne Khamwas et Si-Osire (2 pages) ---
print("Telechargement de Setna II, partie 1...")
r2a = requests.get("https://ib205.tripod.com/setne_2.html", headers=headers)
r2a.encoding = "utf-8"
soup2a = BeautifulSoup(r2a.text, "html.parser")
texte2a = nettoyer_texte(soup2a)

time.sl