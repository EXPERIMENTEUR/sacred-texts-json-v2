import requests
from bs4 import BeautifulSoup
import json
import re
import time

headers = {"User-Agent": "TelechargementPersonnel/1.0 (usage prive; contact: jerom_yapo@outlook.fr)"}

nb_chapitres_par_livre = {
    1: 40, 2: 48, 3: 36, 4: 52, 5: 56, 6: 59, 7: 70, 8: 63,
    9: 47, 10: 59, 11: 46, 12: 51, 13: 58, 14: 48, 15: 63, 16: 78
}

def nettoyer_html(soup):
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    texte = soup.get_text(separator=" ")
    texte = re.sub(r"\s{2,}", " ", texte).strip()
    texte = re.sub(r"\d+\s*Esdras\s*Chapter\s*\d+", " ", texte)

    if "Previous Next" in texte:
        texte = texte.split("Previous Next", 1)[1]
    if "Sacred Texts" in texte:
        texte = texte.split("Sacred Texts", 1)[0]
    return texte.strip()

def decouper_versets(texte, nb_max):
    versets = {}
    pattern = re.compile(r"(?<!\d)(\d{1,2})\s+(?=[A-Z])")
    positions = [(m.start(1), int(m.group(1))) for m in pattern.finditer(texte) if int(m.group(1)) <= nb_max]
    for i, (pos, num) in enumerate(positions):
        fin = positions[i + 1][0] if i + 1 < len(positions) else len(texte)
        contenu = texte[pos + len(str(num)):fin].strip()
        if contenu and num not in versets:
            versets[num] = contenu
    return versets

tous_chapitres = []

for num_chap in range(1, 17):
    print(f"Telechargement chapitre {num_chap}...")
    url = f"https://sacred-texts.com/bib/apo/es2{num_chap:03d}.htm"
    try:
        r = requests.get(url, headers=headers)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        texte_brut = nettoyer_html(soup)

        nb_max = nb_chapitres_par_livre.get(num_chap, 100)
        versets_dict = decouper_versets(texte_brut, nb_max)

        versets_liste = [{"verse": k, "text": v} for k, v in sorted(versets_dict.items())]

        chapitre_obj = {
            "chapter": num_chap,
            "source": url,
            "verses": versets_liste
        }
        tous_chapitres.append(chapitre_obj)
        print(f"  {len(versets_liste)} versets trouves")
        time.sleep(1)
    except Exception as e:
        print(f"  ERREUR chapitre {num_chap} : {e}")

with open("2esdras_complete.json", "w", encoding="utf-8") as f:
    json.dump({
        "book": "2 Esdras (Apocalypse of Ezra)",
        "note": "Traduction King James, domaine public. Source: sacred-texts.com. Extraction automatique - quelques versets peuvent contenir de tres legeres imperfections de decoupage.",
        "chapters": tous_chapitres
    }, f, ensure_ascii=False, indent=2)

print("Termine ! Fichier 2esdras_complete.json cree (16 chapitres).")