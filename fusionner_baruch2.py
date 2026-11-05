# -*- coding: ascii -*-
"""2 Baruch (R. H. Charles, 1913, texte du Wesley Center, NNU) : remplace le 2 Baruch OCR de
baruch_complete.json par les chapitres propres (sans notes). Le 3 Baruch (Hughes) est conserve.
Sauvegarde l'ancien fichier une seule fois dans baruch_complete_ocr.json. Relancable sans risque.
Usage : python fusionner_baruch2.py [2baruch_nnu.html]"""
import html, json, os, re, shutil, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "2baruch_nnu.html"
CIBLE = "baruch_complete.json"
SAUVE = "baruch_complete_ocr.json"

if not os.path.exists(SAUVE):
    shutil.copyfile(CIBLE, SAUVE)
with open(SAUVE, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    s = f.read()
debut = s.find('<h2 align="center" class="Section1"')
fin = s.find("<!-- Text: [end]")
corps = s[debut:fin]

def nt(h):
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace(chr(0xa0), " ")
    return re.sub(r"\s+", " ", h).strip()

RX_TITRE = re.compile(r"^\d+(?::\d+)?(?:\s*[-\u2014\u2013]\s*\d+(?::\d+)?)?\.\s+\D")
paras = [nt(b) for a, b in re.findall(r"<p([^>]*)>(.*?)</p>", corps, re.S | re.I)]
paras = [p for p in paras if p]

chapitres, titres_sections, cur = [], {}, 0
STRICTS = set(int(m.group(1)) for m in (re.match(r"^(\d+) 1 ", q) for q in paras) if m)
for p in paras:
    if p == "finish" or p.startswith("Translation from the Syriac"):
        break
    if p in ("2 Baruch", "The Book of The Apocalypse of Baruch The Son of Neriah"):
        continue
    if RX_TITRE.match(p) and len(p.split()) < 40:
        titres_sections.setdefault(cur + 1, []).append(p)
        continue
    m = re.match(r"^(\d+) 1 ", p)
    m2 = re.match(r"^(\d+) ", p)
    if (m and int(m.group(1)) == cur + 1) or (m2 and not m and int(m2.group(1)) == cur + 1 and (cur + 1) not in STRICTS):
        cur += 1
        chapitres.append({"chapter": cur, "paragraphs": []})
    if not chapitres:
        continue
    chapitres[-1]["paragraphs"].append(p)

def propre(p):
    p = re.sub(r"^\d+ \d+ ", "", p)
    p = re.sub(r"^\d+ ", "", p)
    p = re.sub(r"\s\d+\s(?=[A-Z'\u2018\"\u201c(\[])", " ", p)
    return re.sub(r"\s+", " ", p).strip()

nouveaux = []
for c in chapitres:
    lignes = [propre(p) for p in c["paragraphs"]]
    entree = {"chapter": c["chapter"], "text": "\n\n".join(l for l in lignes if l)}
    if c["chapter"] in titres_sections:
        entree["section"] = " / ".join(titres_sections[c["chapter"]])
    nouveaux.append(entree)

for livre in data["livres"]:
    if livre["title"].startswith("2"):
        livre["chapters"] = nouveaux
        livre["source"] = "R. H. Charles (1913), APOT vol. 2, texte du Wesley Center (NNU), sans notes ; la page source s'arrete a 85:2"
data["note"] = (data.get("note", "") + " | 2 Baruch remplace par le texte du Wesley Center (sans notes) ; ancien OCR dans " + SAUVE)
with open(CIBLE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

mots = sum(len(c["text"].split()) for c in nouveaux)
print("2 Baruch : %d chapitres, %d mots, %d titres de sections" % (len(nouveaux), mots, len(titres_sections)))
print("premier :", nouveaux[0]["text"][:90])
print("dernier :", nouveaux[-1]["chapter"], nouveaux[-1]["text"][-90:])
