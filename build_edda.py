# -*- coding: utf-8 -*-
# Construit edda_complete.json a partir de edda_gutenberg.txt
# (H. A. Bellows, The Poetic Edda, 1923 ; Project Gutenberg #73533).
# Garde les strophes et la prose du manuscrit ; exclut introductions, notes et index de l'editeur.
import re, json, io

SRC = "edda_gutenberg.txt"
OUT = "edda_complete.json"

raw = io.open(SRC, encoding="utf-8-sig", errors="replace").read().replace("\r", "")
L = raw.split("\n")

# (titre dans le fichier, libelle, groupe)
GODS = "Lays of the Gods"
HEROES = "Lays of the Heroes"
POEMES = [
    ("VOLUSPO", "Voluspo", GODS), ("HOVAMOL", "Hovamol", GODS), ("VAFTHRUTHNISMOL", "Vafthruthnismol", GODS),
    ("GRIMNISMOL", "Grimnismol", GODS), ("SKIRNISMOL", "Skirnismol", GODS), ("HARBARTHSLJOTH", "Harbarthsljoth", GODS),
    ("HYMISKVITHA", "Hymiskvitha", GODS), ("LOKASENNA", "Lokasenna", GODS), ("THRYMSKVITHA", "Thrymskvitha", GODS),
    ("ALVISSMOL", "Alvissmol", GODS), ("BALDRS DRAUMAR", "Baldrs Draumar", GODS), ("RIGSTHULA", "Rigsthula", GODS),
    ("HYNDLULJOTH", "Hyndluljoth", GODS), ("SVIPDAGSMOL", "Svipdagsmol", GODS),
    ("V\u00d6LUNDARKVITHA", "V\u00f6lundarkvitha", HEROES), ("HELGAKVITHA HJORVARTHSSONAR", "Helgakvitha Hjorvarthssonar", HEROES),
    ("HELGAKVITHA HUNDINGSBANA I", "Helgakvitha Hundingsbana I", HEROES), ("HELGAKVITHA HUNDINGSBANA II", "Helgakvitha Hundingsbana II", HEROES),
    ("FRA DAUTHA SINFJOTLA", "Fra Dautha Sinfjotla", HEROES), ("GRIPISSPO", "Gripisspo", HEROES),
    ("REGINSMOL", "Reginsmol", HEROES), ("FAFNISMOL", "Fafnismol", HEROES), ("SIGRDRIFUMOL", "Sigrdrifumol", HEROES),
    ("BROT AF SIGURTHARKVITHU", "Brot af Sigurtharkvithu", HEROES), ("GUTHRUNARKVITHA I", "Guthrunarkvitha I", HEROES),
    ("SIGURTHARKVITHA EN SKAMMA", "Sigurtharkvitha en Skamma", HEROES), ("HELREITH BRYNHILDAR", "Helreith Brynhildar", HEROES),
    ("DRAP NIFLUNGA", "Drap Niflunga", HEROES), ("GUTHRUNARKVITHA II, EN FORNA", "Guthrunarkvitha II, en Forna", HEROES),
    ("GUTHRUNARKVITHA III", "Guthrunarkvitha III", HEROES), ("ODDRUNARGRATR", "Oddrunargratr", HEROES),
    ("ATLAKVITHA EN GR\u00d6NLENZKA", "Atlakvitha en Gr\u00f6nlenzka", HEROES), ("ATLAMOL EN GR\u00d6NLENZKU", "Atlamol en Gr\u00f6nlenzku", HEROES),
    ("GUTHRUNARHVOT", "Guthrunarhvot", HEROES), ("HAMTHESMOL", "Hamthesmol", HEROES),
]

# debut du corps du livre (apres la table des matieres et l'introduction generale)
start = next(i for i, l in enumerate(L) if l.strip() == "LAYS OF THE GODS")
fin_livre = next(i for i, l in enumerate(L) if l.strip().startswith("PRONOUNCING INDEX OF PROPER NAMES") and i > start + 1000)

# position de chaque titre (ligne exacte, apres 'start')
pos, cur = [], start
for key, _, _ in POEMES:
    i = next(j for j in range(cur, fin_livre) if L[j].strip() == key)
    pos.append(i); cur = i + 1
pos.append(fin_livre)

def blancs(i):
    n = 0
    while i + n < len(L) and not L[i + n].strip():
        n += 1
    return n

def corps(a, b):
    """Retourne les lignes du poeme sans introduction ni notes."""
    seg = L[a:b]
    # fin : ligne 'NOTES'
    for k, l in enumerate(seg):
        if l.strip() == "NOTES":
            seg = seg[:k]; break
    # debut : apres la derniere 'INTRODUCTORY NOTE' du segment, au premier trou d'au moins 4 lignes vides
    intro = [k for k, l in enumerate(seg) if l.strip() == "INTRODUCTORY NOTE"]
    k0 = intro[0] if intro else 0
    k = k0
    while k < len(seg):
        if not seg[k].strip() and blancs_seg(seg, k) >= 4:
            break
        k += 1
    return seg[k:]

def blancs_seg(seg, i):
    n = 0
    while i + n < len(seg) and not seg[i + n].strip():
        n += 1
    return n

ROM = re.compile(r"^(?:[IVX]+\.\s+.+|\([IVX]+\)|[A-Z\u00c0-\u00de][A-Z\u00c0-\u00de \-,'\u2019\.]{3,})$")
poemes = []
for (key, label, groupe), a, b in zip(POEMES, pos, pos[1:]):
    lines = corps(a, b)
    txt = "\n".join(lines)
    blocs = [bl for bl in re.split(r"\n\s*\n", txt) if bl.strip()]
    items = []
    for bl in blocs:
        ls = bl.split("\n")
        premiere = ls[0]
        stripped = [x.strip() for x in ls]
        t = " ".join(re.sub(r"\s+", " ", x.replace("|", " ")) .strip() for x in stripped).strip()
        t = re.sub(r"\s+", " ", t)
        m = re.match(r"^(\d+)\.\s+(.*)$", premiere.strip())
        if m and premiere.startswith(m.group(1)):
            first = re.sub(r"\s+", " ", m.group(2).replace("|", " ")).strip()
            rest = " ".join(re.sub(r"\s+", " ", x.replace("|", " ")).strip() for x in stripped[1:])
            items.append({"kind": "stanza", "n": int(m.group(1)), "text": (first + " " + rest).strip(),
                          "lines": [re.sub(r"\s+", " ", x.replace("|", " ")).strip() for x in [m.group(2)] + stripped[1:]]})
        elif premiere.startswith("  "):
            items.append({"kind": "verse", "text": t,
                          "lines": [re.sub(r"\s+", " ", x.replace("|", " ")).strip() for x in stripped]})
        elif re.fullmatch(r"(?:\*\s*)+", t):
            items.append({"kind": "separateur", "text": t})
        elif len(t) < 80 and t.endswith(":") and re.search(r"\b(spake|said|answered|asked|quoth|cried|saith|sang|called|began)\b", t):
            items.append({"kind": "locuteur", "text": t})
        elif len(ls) <= 2 and ROM.match(t):
            items.append({"kind": "titre", "text": t})
        else:
            items.append({"kind": "prose", "text": t})
    poemes.append({"id": label, "group": groupe, "items": items})

data = {
    "work": "The Poetic Edda (Edda poetique)",
    "edition": "Henry Adams Bellows, The Poetic Edda translated from the Icelandic, American-Scandinavian Foundation, 1923; Project Gutenberg #73533",
    "license": "Public domain (1923 ; Bellows d. 1944). Project Gutenberg edition.",
    "note": "Traduction anglaise de 1923 d'apres l'edition de Neckel ; les traductions modernes (Larrington, Dronke, Orchard...) sont sous droit d'auteur et ne sont pas incluses. Les introductions et notes de Bellows sont exclues. 'stanza' = strophe numerotee, 'verse' = strophe non numerotee (dialogues), 'locuteur' = indication de qui parle, 'separateur' = passage omis par le manuscrit, 'prose' = prose narrative du compilateur medieval, 'titre' = intertitre. Les parentheses dans les strophes sont des interpolations signalees par l'editeur ; '. . . .' marque une lacune du manuscrit. La cesure interne ('|') a ete supprimee.",
    "poems": poemes,
}
io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))

print("Fichier:", OUT)
for p in poemes:
    st = [i["n"] for i in p["items"] if i["kind"] == "stanza"]
    gaps = [(st[i], st[i + 1]) for i in range(len(st) - 1) if st[i + 1] != st[i] + 1]
    kinds = {k: sum(1 for i in p["items"] if i["kind"] == k) for k in ("stanza", "verse", "prose", "titre", "locuteur", "separateur")}
    print("%-30s strophes=%3d 1er=%s dernier=%s verse=%d prose=%d titres=%d locuteurs=%d sep=%d sauts=%s" % (
        p["id"], kinds["stanza"], st[:1], st[-1:], kinds["verse"], kinds["prose"], kinds["titre"], kinds["locuteur"], kinds["separateur"], gaps[:5]))