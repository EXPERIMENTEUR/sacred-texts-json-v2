# -*- coding: ascii -*-
"""Ajoute a patterns_religieux.jsonl des motifs pour le Popol Vuh (traduction de Brasseur, 1861).
Classement d'apres ce que dit le texte lui-meme ; noms ambigus listes a part (non ajoutes).
Sans doublon, sauvegarde unique dans patterns_religieux.jsonl.bak_popol. Relancable sans risque.
Usage : python ajouter_patterns_popol.py"""
import json, os, re, shutil

FICHIER = "patterns_religieux.jsonl"
APP = os.path.join("..", "streamlit-app", "app.py")
POPOL = "popol_vuh_complete.json"

# Categories utilisees par l'application (lues dans app.py si possible)
categories = set()
if os.path.exists(APP):
    with open(APP, "r", encoding="utf-8-sig") as f:
        bloc = re.search(r"CATEGORIES_PERSONNALISEES\s*=\s*\{(.*?)\}", f.read(), re.S)
    if bloc:
        categories = set(re.findall(r'"([A-Z_]+)"', bloc.group(1)))
NEG = "NEGATIVE_ENTITY" if "NEGATIVE_ENTITY" in categories else "PROPHET_FIGURE"

DIEUX = ["Tohil", "Avilix", "Hacavitz", "Hurakan", "Gucumatz", "Tepeu", "Xpiyacoc", "Xmucan\u00e9",
         "C\u0153ur du Ciel", "C\u0153ur du ciel"]
FIGURES = ["Hunahpu", "Xbalanqu\u00e9", "Xhunahpu", "Hunhun-Ahpu", "Vukub-Hunahpu", "Hunbatz", "Hunchouen",
           "Balam-Quitz\u00e9", "Balam-Agab", "Mahucutah", "Iqi-Balam", "BalamAgab", "BalamQuitz\u00e9",
           "Quicab", "Cavizimah", "Cotuha"]
ADVERSES = ["Vukub-Cakix", "VukubCakix", "Zipacna", "Cabrakan", "Hun-Cam\u00e9", "Vukub-Cam\u00e9",
            "HunCam\u00e9", "VukubCam\u00e9"]
LIEUX = ["Xibalba", "Tulan", "Tulan-Zuiva"]
PEUPLES = ["Quich\u00e9", "Quich\u00e9s", "Quiche", "Quiches", "Cakchiquels", "Rabinaliens", "Tamub", "Ilocab",
           "Cavek", "Nihaib", "Niha\u00efb", "Tziquinaha"]

NOUVEAUX = ([("DEITY", p) for p in DIEUX] + [("PROPHET_FIGURE", p) for p in FIGURES]
            + [(NEG, p) for p in ADVERSES] + [("SACRED_PLACE", p) for p in LIEUX]
            + [("PEOPLE_GROUP", p) for p in PEUPLES])

existants = set()
with open(FICHIER, "r", encoding="utf-8-sig") as f:
    contenu = f.read()
for ligne in contenu.splitlines():
    if ligne.strip():
        o = json.loads(ligne)
        existants.add((o["label"], o["pattern"]))

a_ajouter = [(l, p) for l, p in NOUVEAUX if (l, p) not in existants]
if a_ajouter:
    if not os.path.exists(FICHIER + ".bak_popol"):
        shutil.copyfile(FICHIER, FICHIER + ".bak_popol")
    with open(FICHIER, "a", encoding="utf-8", newline="\n") as f:
        if contenu and not contenu.endswith("\n"):
            f.write("\n")
        for l, p in a_ajouter:
            f.write(json.dumps({"label": l, "pattern": p}, ensure_ascii=False) + "\n")

print("Motifs ajoutes : %d (deja presents : %d). Categorie des adversaires : %s" % (
    len(a_ajouter), len(NOUVEAUX) - len(a_ajouter), NEG))

# Verification : occurrences dans le texte du Popol Vuh (hors texte quiche et notes)
def chaines(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in ("texte_quiche", "notes", "quiche"):
                continue
            for s in chaines(v):
                yield s
    elif isinstance(o, list):
        for v in o:
            for s in chaines(v):
                yield s

if os.path.exists(POPOL):
    with open(POPOL, "r", encoding="utf-8-sig") as f:
        texte = re.sub(r"\s+", " ", " ".join(chaines(json.load(f))))
    total = {}
    for l, p in NOUVEAUX:
        n = len(re.findall(r"(?<!\w)" + re.escape(p) + r"(?!\w)", texte))
        total[l] = total.get(l, 0) + n
    print("Occurrences attendues dans le Popol Vuh par categorie :", ", ".join("%s %d" % (k, v) for k, v in sorted(total.items())))
