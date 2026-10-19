import requests
from bs4 import BeautifulSoup
import json
import re
import ftfy

headers = {"User-Agent": "TelechargementPersonnel/1.0 (usage prive; contact: jerom_yapo@outlook.fr)"}
url = "https://www.gospels.net/thomas"

r = requests.get(url, headers=headers)
r.encoding = "utf-8"
soup = BeautifulSoup(r.text, "html.parser")

for tag in soup(["script", "style", "nav", "header", "footer"]):
    tag.decompose()

texte = ftfy.fix_text(soup.get_text(separator="\n"))
lignes = [l.strip() for l in texte.split("\n")]

def trouver(prefixe):
    for i, l in enumerate(lignes):
        if l.startswith(prefixe):
            return i
    return None

debut = trouver("Prologue")
fin = trouver("Notes on Translation")

if debut is None or fin is None:
    print("ERREUR : structure de la page inattendue (Prologue ou Notes introuvables).")
    raise SystemExit

lignes = lignes[debut:fin]

pattern = re.compile(r"^Saying (\d+): (.*)$")
prologue = []
sayings = []
courant = None

i = 0
while i < len(lignes):
    l = lignes[i]
    m = pattern.match(l)
    if m:
        titre = m.group(2).strip()
        while titre.endswith(",") and i + 1 < len(lignes):
            i += 1
            if lignes[i]:
                titre = (titre + " " + lignes[i]).strip()
        courant = {"saying": int(m.group(1)), "title": titre, "lines": []}
        sayings.append(courant)
    elif l and l != "Prologue" and l not in ("The Gospel", "According to Thomas"):
        if courant is None:
            prologue.append(l)
        else:
            courant["lines"].append(l)
    i += 1

resultat = []
for s in sayings:
    resultat.append({
        "saying": s["saying"],
        "title": s["title"],
        "text": "\n".join(s["lines"])
    })

numeros = [s["saying"] for s in resultat]
manquants = [n for n in range(1, 115) if n not in numeros]
print(f"{len(resultat)} logia trouves (attendu : 114)")
print(f"Numeros manquants : {manquants if manquants else 'aucun'}")

with open("thomas_complete.json", "w", encoding="utf-8") as f:
    json.dump({
        "book": "The Gospel of Thomas",
        "translator": "Mark M. Mattison",
        "license": "Traduction versee au domaine public par son auteur. Source : https://www.gospels.net/thomas. Base sur le texte copte de Nag Hammadi Codex II, 2.",
        "note": "Les crochets [ ] indiquent une lacune du manuscrit, les parentheses ( ) une insertion editoriale, / \\ une correction de scribe.",
        "prologue": " ".join(prologue),
        "sayings": resultat
    }, f, ensure_ascii=False, indent=2)

print("Termine ! Fichier thomas_complete.json cree.")