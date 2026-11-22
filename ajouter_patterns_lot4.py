# -*- coding: ascii -*-
"""Lot 4 de motifs : Bible hebraique, Septante, Enoch, Baruch, Testaments des 12 Patriarches (noms propres uniquement).
Sans argument : apercu seulement. Avec l'argument 'appliquer' : ecrit dans patterns_religieux.jsonl (sauvegarde .bak_lot4).
Usage (depuis le dossier sacred-texts-json) : python ajouter_patterns_lot4.py [appliquer]"""
import json, os, shutil, sys

FICHIER = "patterns_religieux.jsonl"
LOT = {
    "PROPHET_FIGURE": [
        # Prophetes et livres historiques
        "Saul", "Joab", "Absalom", "Jonathan", "Hezekiah", "Jeroboam", "Ahab", "Zedekiah", "Abner", "Jehu", "Gideon",
        "Abimelech", "Samson", "Jehoshaphat", "Josiah", "Rehoboam", "Jehoiada", "Amaziah", "Zadok", "Benaiah", "Shimei",
        # Ketuvim
        "Mordecai", "Esther", "Haman", "Job", "Nebuchadnezzar", "Ahasuerus", "Azariah", "Asaph", "Zechariah", "Shemaiah",
        "Asa", "Ezra", "Esdras", "Cyrus", "Jeshua", "Boaz", "Obed", "Naomi", "Darius", "Meshullam",
        # Torah
        "Esau", "Laban", "Balaam", "Abram", "Eleazar", "Balak", "Lot", "Rebekah", "Korah", "Sihon", "Ishmael", "Sarai",
        "Nahor", "Cain", "Abel", "Pharaoh", "Pharao",
        # Septante (graphies grecques)
        "Abraam", "Ezekias", "Jeremias", "Elisaie", "Achaab", "Josaphat", "Eliu", "Josias", "Abenner", "Abessalom",
        "Nabuchodonosor", "Mardoch\u00e6us", "Roboam", "Aman", "Ruben", "Joas", "Azarias", "Jodae", "Antiochus",
        # Enoch, Baruch, Testaments
        "Lamech", "Jared", "Mahalalel", "Mathusalem", "Enoc", "Baruch", "Neriah", "Bilhah", "Tamar", "Bathshua",
        "Potiphar", "Hamor", "Dinah", "Shelah", "Gersham", "Kohath", "Merari", "Zilpah",
    ],
    "SACRED_PLACE": [
        "Babylon", "Zion", "Sion", "Jordan", "Assyria", "Samaria", "Hebron", "Chebron", "Jericho", "Lebanon", "Libanus",
        "Gilead", "Galaad", "Gilgal", "Shechem", "Jezreel", "Mizpah", "Gibeah", "Persia", "Shushan", "Sodom", "Seir",
        "Edom", "Moab", "Ammon", "Syria", "Judea", "Chanaan", "Madiam", "B\u00e6thel", "Kadesh", "Sinai", "Nile",
        "Heshbon", "Bashan", "Aram", "Kidron", "Cedron", "Sheol", "Paradise", "Hades",
    ],
    "PEOPLE_GROUP": [
        "Juda", "Ephraim", "Manasseh", "Manasse", "Jews", "Levites", "Philistines", "Ammonites", "Amorites", "Chaldeans",
        "Assyrians", "Arameans", "Hittites", "Benjaminites", "Reubenites", "Gadites", "Ishmaelites", "Gentiles", "Amalek",
    ],
    "DEITY": ["Baal", "Almighty", "Shaddai", "Highest"],
    "NEGATIVE_ENTITY": [
        "Beliar", "Az\u00e2z\u00eal", "Semj\u00e2z\u00e2", "Arm\u00e2r\u00f4s", "\u00caz\u00eaq\u00ea\u00eal", "Bar\u00e2q\u00eej\u00e2l", "T\u00fbr\u00eal", "Sari\u00eal", "K\u00f4kab\u00eal",
    ],
    "CELESTIAL_BEING": ["Phanuel", "Ramiel"],
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
    shutil.copy(FICHIER, FICHIER + ".bak_lot4")
    with open(FICHIER, "a", encoding="utf-8", newline="\n") as f:
        for label, nom in nouveaux:
            f.write(json.dumps({"label": label, "pattern": nom}, ensure_ascii=False) + "\n")
    print("Applique : %d motifs ajoutes. Sauvegarde : %s.bak_lot4" % (len(nouveaux), FICHIER))
else:
    print("Apercu seulement. Pour ecrire : python ajouter_patterns_lot4.py appliquer")
