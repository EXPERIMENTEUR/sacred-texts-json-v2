# -*- coding: utf-8 -*-
# Construit popol_vuh_complete.json a partir de popol_brasseur_a.txt
# (Brasseur de Bourbourg, "Popol Vuh. Le livre sacre et les mythes de l'antiquite americaine", Paris, 1861 ;
#  texte quiche et traduction francaise en regard, scan archive.org "popolvuhlelivres01bras").
# Garde uniquement la traduction francaise ; exclut le texte quiche, les notes et commentaires de Brasseur.
import re, json, io, collections

SRC = "popol_brasseur_a.txt"
OUT = "popol_vuh_complete.json"

raw = io.open(SRC, encoding="utf-8-sig", errors="replace").read().replace("\r", "")
L = raw.split("\n")
a = next(i for i, l in enumerate(L) if re.match(r"^PREMI.RE\s+PARTIE", l.strip()))
b = next(i for i, l in enumerate(L) if i > a and l.strip() == "FIN.")
txt = "\n".join(L[a:b])

paras = []
for bl in re.split(r"\n\s*\n", txt):
    ls = [re.sub(r"\s+", " ", x).strip() for x in bl.split("\n")]
    ls = [x for x in ls if x]
    if ls:
        paras.append(ls)

FR = set("le la les de des du et un une que qui dans leur leurs il ils elle elles fut furent sont pour avec par sur ce cette ces ses son sa au aux en est ont mais ou ne pas se lui nous vous alors ainsi bien fort donc car comme si tous tout toute cet meme plus tres sans sous entre vers apres avant pendant tandis encore deja aussi voici voila etait avait ete leurs eux celui celle ceux dont lorsque quand puis ensuite suis es sommes etes y ni nos notre votre vos mon ma mes ta tes".split())
QU = set("ri chi ta eut cut puch ca cha chu vi pa ru ruq cumal ahau ahauab xa x-e e u ma-habi cu chic hun ch'u re ch'a vae are".split())

def feat(s):
    w = re.findall(r"[a-z\u00e0-\u00ff'\-]+", s.lower())
    if not w:
        return 0, 0, 0
    fr = sum(1 for x in w if x.replace("\u00e9", "e").replace("\u00e8", "e").replace("\u00e0", "a") in FR) / len(w)
    qu = sum(1 for x in w if x in QU or x.startswith("x-")) / len(w)
    return fr, qu, len(w)

def is_fr(t):
    fr, qu, n = feat(t)
    return n >= 4 and fr - qu >= 0.08

CH = re.compile(r"^CHAPITRE\s+(PREMIER|DEUXI|TROISI|QUATRI|CINQUI|SIXI|SEPTI|HUITI|NEUVI|DIXI|ONZI|DOUZI|TREIZI|QUATORZI)", re.I)
REF = re.compile(r"\s?\(\s*(?:\d{1,2}|l|fi)\s*[\)j]['\u2019]?")

def propre(t):
    t = REF.sub("", t)
    t = re.sub(r"(\w)- (\w)", r"\1\2", t)
    return re.sub(r"\s+", " ", t).strip()

parts = [{"part": 0, "title": "Preambule", "chapters": [{"chapter": 0, "title": "PREAMBULE", "paragraphs": []}]}]
cur = None
for ls in paras:
    t = " ".join(ls)
    m = CH.match(t)
    if m:
        if re.match(r"CHAPITRE\s+PREMIER", t, re.I):
            parts.append({"part": len(parts), "title": "Partie %d" % len(parts), "chapters": []})
        pt = parts[-1]
        pt["chapters"].append({"chapter": len(pt["chapters"]) + 1, "title": re.sub(r"[\s.,\-]+$", "", t), "paragraphs": []})
        cur = None
        continue
    if re.match(r"^[\(\[]\s*[\d\.lI]{1,3}\s*[\)\]]", t):
        continue
    mx = max(len(x) for x in ls)
    if not (is_fr(t) and mx >= 50):
        continue
    ch = parts[-1]["chapters"][-1]
    t = propre(t)
    prev = ch["paragraphs"][-1] if ch["paragraphs"] else None
    if prev is not None and cur is ch and (t[:1].islower() or not re.search(r"[.:;!?\u00bb)]$", prev)):
        ch["paragraphs"][-1] = prev + " " + t
    else:
        ch["paragraphs"].append(t)
    cur = ch

data = {
    "work": "Popol Vuh (Livre sacre des Quiches)",
    "edition": "Charles-Etienne Brasseur de Bourbourg, Popol Vuh. Le livre sacre et les mythes de l'antiquite americaine, Paris, 1861 (texte quiche et traduction francaise en regard ; seule la traduction francaise est conservee). Scan : Internet Archive, popolvuhlelivres01bras.",
    "license": "Public domain (1861).",
    "note": "Traduction francaise de 1861, litterale mais critiquee par les specialistes ; les traductions modernes (Recinos, Goetz-Morley, Tedlock, Christenson...) sont sous droit d'auteur et ne sont pas incluses. Texte issu d'un OCR : erreurs possibles. Le texte quiche, les notes et les longs commentaires de Brasseur (souvent speculatifs) sont exclus par heuristique ; quelques fragments de notes peuvent subsister, et un alinea coupe par un saut de page peut etre mal recolle. Les parentheses sont des ajouts du traducteur. Division en parties et chapitres de Brasseur (le manuscrit n'en comporte pas). Les appels de notes ont ete supprimes.",
    "parts": parts,
}
io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))

print("Fichier:", OUT)
for pt in parts:
    print("Partie %d : %d chapitres, %d alineas, %d mots" % (
        pt["part"], len(pt["chapters"]),
        sum(len(c["paragraphs"]) for c in pt["chapters"]),
        sum(len(p.split()) for c in pt["chapters"] for p in c["paragraphs"])))