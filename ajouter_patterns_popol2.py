# -*- coding: ascii -*-
"""Complete les motifs du Popol Vuh (lot 2) : seigneurs de Xibalba, personnages secondaires, lieux.
Noms releves dans le texte de Brasseur (contexte verifie). Sans doublon, sauvegarde unique .bak_popol2.
Usage : python ajouter_patterns_popol2.py"""
import json, os, re, shutil

FICHIER = "patterns_religieux.jsonl"
APP = os.path.join("..", "streamlit-app", "app.py")
categories = set()
if os.path.exists(APP):
    with open(APP, "r", encoding="utf-8-sig") as f:
        bloc = re.search(r"CATEGORIES_PERSONNALISEES\s*=\s*\{(.*?)\}", f.read(), re.S)
    if bloc:
        categories = set(re.findall(r'"([A-Z_]+)"', bloc.group(1)))
NEG = "NEGATIVE_ENTITY" if "NEGATIVE_ENTITY" in categories else "PROPHET_FIGURE"

SEIGNEURS = ["Cuchumaquiq", "Xiqiripat", "Ahalpuh", "Ahalgana", "Chamiabak", "Chamiaholom", "Ahalmez", "Ahaltocob",
             "Xic", "Patan"]
PERSONNAGES = ["Xbalanque", "Xtah", "Xpuch", "Xbakiyalo", "Chimalmat", "Qoacul", "Qoacutec", "Qoahau", "Qochahuh",
               "Qotzibaha"]
LIEUX = ["Izmachi", "Meavan"]
NOUVEAUX = ([(NEG, p) for p in SEIGNEURS] + [("PROPHET_FIGURE", p) for p in PERSONNAGES]
            + [("SACRED_PLACE", p) for p in LIEUX])

with open(FICHIER, "r", encoding="utf-8-sig") as f:
    contenu = f.read()
existants = set((o["label"], o["pattern"]) for o in (json.loads(l) for l in contenu.splitlines() if l.strip()))
a_ajouter = [(l, p) for l, p in NOUVEAUX if (l, p) not in existants]
if a_ajouter:
    if not os.path.exists(FICHIER + ".bak_popol2"):
        shutil.copyfile(FICHIER, FICHIER + ".bak_popol2")
    with open(FICHIER, "a", encoding="utf-8", newline="\n") as f:
        if contenu and not contenu.endswith("\n"):
            f.write("\n")
        for l, p in a_ajouter:
            f.write(json.dumps({"label": l, "pattern": p}, ensure_ascii=False) + "\n")
print("Motifs ajoutes : %d (deja presents : %d). Categorie des seigneurs : %s" % (len(a_ajouter), len(NOUVEAUX) - len(a_ajouter), NEG))
