# -*- coding: ascii -*-
"""Lot 3 de motifs : Edda, Mesopotamie (Enuma Elish, Gilgamesh, Atrahasis), Avesta.
Sans argument : apercu seulement. Avec l'argument 'appliquer' : ecrit dans patterns_religieux.jsonl (sauvegarde .bak_lot3).
Usage (depuis le dossier sacred-texts-json) : python ajouter_patterns_lot3.py [appliquer]"""
import json, os, shutil, sys

FICHIER = "patterns_religieux.jsonl"
LOT = {
    "DEITY": [
        # Edda
        "Othin", "Loki", "Thor", "Freyja", "Freyr", "Baldr", "Frigg", "Njorth", "Bragi", "Hel", "\u00c6gir", "Hlorrithi", "Harbarth",
        # Mesopotamie
        "Tiamat", "Marduk", "Anshar", "Kingu", "Apsu", "Lakhamu", "Lakhmu", "Mummu", "Bel", "Nudimmud", "Anu", "Anunnaki",
        "Igigi", "Gaga", "Anutum", "Enlil", "Shamash", "Ishtar", "Aruru", "Nergal", "Ninurta", "Adad", "Nisaba",
        # Avesta
        "Ahura Mazda", "Mazda", "Ahura", "Mithra", "An\u00e2hita", "Anahita", "Rashnu", "Sraosha", "Sraosh\u00f4", "Verethraghna",
        "Ashi", "Haoma", "Tistrya", "\u00c2tar", "Vohu Manah", "Amesha Spenta", "Spenta Mainyu",
    ],
    "PROPHET_FIGURE": [
        # Edda
        "Sigurth", "Atli", "Guthrun", "Hogni", "Gunnar", "Helgi", "Gjuki", "Sigmund", "Brynhild", "Loddfafnir", "Buthli",
        "Fjolsvith", "Gripir", "Nithuth", "Ottar", "Regin", "V\u00f6lund", "Alvis", "Sigrun", "Hunding", "Hamther", "Grimhild",
        "Hjorvarth", "Jormunrek", "Bothvild", "Sinfjotli", "Svava", "Svanhild", "Eylimi", "Hothbrodd", "Geirr\u00f6th", "Volsung",
        # Mesopotamie
        "Gilgamish", "Enkidu", "Napishtim", "Shanabi", "Siduri", "Ishullanu",
        # Avesta
        "Zarathustra", "Zarathujtra", "Zarathurtra", "Zarathmtra", "Zarathiutra", "Spitama", "Spit\u00e2ma", "Yima",
        "Thra\u00eataona", "Keres\u00e2spa", "V\u00eest\u00e2spa", "Husravah", "Pesh\u00f4tanu", "V\u00eevanghat",
    ],
    "NEGATIVE_ENTITY": [
        "Fafnir", "Humbaba",
        "Angra Mainyu", "Angra", "A\u00eashma", "Dah\u00e2ka", "Nasu", "Pairikas", "Da\u00eavas", "Daevas", "Da\u00eava", "Daeva", "Y\u00e2tus",
    ],
    "SACRED_PLACE": ["Erech", "Sagila", "Nisir", "Mashu"],
    "PEOPLE_GROUP": ["Wanes", "Goths", "Ylfings"],
    "CELESTIAL_BEING": ["Fravashi", "Fravashis"],
}

existants = {}
if os.path.exists(FICHIER):
    for l in open(FICHIER, encoding="utf-8-sig"):
        if l.strip():
            d = json.loads(l)
            existants.setdefault(d["pattern"], set()).add(d["label"])
else:
    raise SystemExit("%s introuvable : lancez ce script depuis le dossier sacred-texts-json" % FICHIER)

nouveaux, deja, conflits, vus = [], [], [], set()
for label, noms in LOT.items():
    for nom in noms:
        if nom in vus:
            continue
        vus.add(nom)
        if nom in existants:
            (deja if label in existants[nom] else conflits).append((nom, label, sorted(existants[nom])))
        else:
            nouveaux.append((label, nom))

print("Motifs actuels : %d. Nouveaux : %d. Deja presents : %d. Deja presents sous une autre categorie : %d."
      % (sum(len(v) for v in existants.values()), len(nouveaux), len(deja), len(conflits)))
for label in LOT:
    print("%-16s %s" % (label, ", ".join(n for l, n in nouveaux if l == label)))
for nom, label, autres in conflits:
    print("CONFLIT (non modifie) : %s propose %s, existe en %s" % (nom, label, "/".join(autres)))
if len(sys.argv) > 1 and sys.argv[1] == "appliquer":
    shutil.copy(FICHIER, FICHIER + ".bak_lot3")
    with open(FICHIER, "a", encoding="utf-8", newline="\n") as f:
        for label, nom in nouveaux:
            f.write(json.dumps({"label": label, "pattern": nom}, ensure_ascii=False) + "\n")
    print("Applique : %d motifs ajoutes. Sauvegarde : %s.bak_lot3" % (len(nouveaux), FICHIER))
else:
    print("Apercu seulement. Pour ecrire : python ajouter_patterns_lot3.py appliquer")
