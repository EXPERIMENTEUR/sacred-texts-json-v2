# -*- coding: ascii -*-
"""3 Baruch (H. M. Hughes, 1913, OCR) : retire les numeros de versets restes dans le texte,
les debris d'OCR evidents, et fusionne les chapitres dont la coupure est decalee
(un chapitre qui commence par un numero de verset >= 2 reprend la fin du precedent).
Lit le 3 Baruch dans baruch_complete_ocr.json (copie d'origine), ecrit dans baruch_complete.json.
Relancable sans risque. Usage : python nettoyer_baruch3.py"""
import json, re

ORIGINE = "baruch_complete_ocr.json"
CIBLE = "baruch_complete.json"

with open(ORIGINE, "r", encoding="utf-8-sig") as f:
    src = json.load(f)
with open(CIBLE, "r", encoding="utf-8-sig") as f:
    cible = json.load(f)

livre3 = [l for l in src["livres"] if l["title"].startswith("3")][0]

RX_DEBUT_DECALE = re.compile(r"^(?:[2-9]|\d\d)\s")
RX_NUM = re.compile(r"(?<![\w.])\d{1,3}x?(?:,\s*\d{1,3})*\s?")
RX_JE = re.compile(r"(?<!\w)(?:7|101)(?= (?:said|do|will|shall|pray|saw|asked|answered)\b)")

def nettoyer(t):
    t = re.sub(r"^(?:xr\s*)?<\s*", "", t)
    t = re.sub(r"\s(?:rt|rf)\s(?=[A-Z])", " ", t)
    t = RX_JE.sub("I", t)
    t = t.replace("w2th", "with")
    t = re.sub(r"(?<=\w) ?\b47s\b", "'s", t)
    t = RX_NUM.sub("", t)
    return re.sub(r"[ \t]+", " ", t).strip()

blocs = []
for c in livre3["chapters"]:
    brut = c["text"]
    if blocs and RX_DEBUT_DECALE.match(brut):
        blocs[-1]["ids"].append(str(c["chapter"]))
        blocs[-1]["textes"].append(brut)
    else:
        blocs.append({"ids": [str(c["chapter"])], "textes": [brut]})

nouveaux, fusions = [], []
for b in blocs:
    ident = b["ids"][0] if len(b["ids"]) == 1 else b["ids"][0] + "-" + b["ids"][-1]
    if len(b["ids"]) > 1:
        fusions.append(ident)
    texte = nettoyer(" ".join(b["textes"]))
    nouveaux.append({"chapter": ident, "text": texte})

for livre in cible["livres"]:
    if livre["title"].startswith("3"):
        livre["chapters"] = nouveaux
        livre["source"] = "H. M. Hughes (1913), APOT vol. 2, OCR ; numeros de versets et debris retires, coupures de chapitres decalees fusionnees"
with open(CIBLE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(cible, f, ensure_ascii=False, indent=2)

reste = sum(len(re.findall(r"\d", c["text"])) for c in nouveaux)
mots = sum(len(c["text"].split()) for c in nouveaux)
print("3 Baruch : %d blocs, %d mots, chiffres restants : %d" % (len(nouveaux), mots, reste))
print("fusions :", ", ".join(fusions) if fusions else "aucune")
print("identifiants :", " ".join(c["chapter"] for c in nouveaux))
