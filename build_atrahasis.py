# -*- coding: utf-8 -*-
# Construit atrahasis_complete.json a partir de atrahasis_clay1922.pdf
# (A. T. Clay, "A Hebrew Deluge Story in Cuneiform", Yale Oriental Series Researches V-3, 1922, appendice A-C).
# Ne garde que la colonne "traduction" ; la translitteration et les notes de Clay sont exclues.
# Necessite : pip install pdfplumber
import re, sys, json, io, collections
import pdfplumber

SRC = "atrahasis_clay1922.pdf"
OUT = "atrahasis_complete.json"
PAGES = range(58, 70)   # appendice : sections A, B, C (la section D, sumerienne, est ignoree)

NOTE = re.compile(r"^[A-G],\s*(?:\d|[IVX]+\s*[:,.])|^\d[A-Za-z]")
COL = re.compile(r"^COLUM\S*\s*([IVX]+)\b", re.I)
HEAD = [("A", re.compile(r"^A\.\s+AN EARLY VERSION")),
        ("B", re.compile(r"^B\.\s+A LATE REDACTION")),
        ("C", re.compile(r"^C\.\s+ASSYRIAN FRAGMENT")),
        ("D", re.compile(r"^D\.\s+A DELUGE STORY"))]
TITRES = {"A": "Version ancienne (Old Babylonian, tablette II, roi Ammi-zaduga)",
          "B": "Redaction tardive (Neo-Babylonian)",
          "C": "Fragment assyrien"}
FONCTION = {"of", "the", "to", "a", "and", "in", "that", "his", "her", "their", "for", "he", "she", "they", "with", "by", "on", "at", "from", "upon", "is", "was", "be", "I", "thy"}

def lignes(pg):
    ws = pg.extract_words()
    rows = []
    for w in sorted(ws, key=lambda w: (round(w["top"] / 4), w["x0"])):
        for r in rows:
            if abs(r["top"] - w["top"]) < 4:
                r["w"].append(w); break
        else:
            rows.append({"top": w["top"], "w": [w]})
    for r in rows:
        r["w"].sort(key=lambda w: w["x0"])
    rows.sort(key=lambda r: r["top"])
    return rows

def frontiere(rows):
    xs = []
    for r in rows:
        w = r["w"]
        t = " ".join(x["text"] for x in w)
        if NOTE.match(t):
            break
        for i in range(1, len(w)):
            if w[i]["x0"] - w[i - 1]["x1"] > 10 and w[i]["x0"] > 200:
                xs.append(round(w[i]["x0"])); break
    if not xs:
        return None
    c = collections.Counter(x // 12 for x in xs).most_common(1)[0][0]
    return min(x for x in xs if x // 12 == c) - 8

def fusion(entries):
    """Recolle les vers coupes sur deux lignes typographiques."""
    res = []
    for e in entries:
        if res:
            p = res[-1]
            if e["n"] is None and e["col"] == p["col"]:
                pt = p["text"]
                dernier = re.sub(r"[^\w\-]+$", "", pt.split()[-1]) if pt.split() else ""
                fin_phrase = pt.rstrip().endswith((".", ";", "!", "?", ":"))
                suite = e["text"][:1].islower() or re.match(r"^\[[a-z]", e["text"])
                if pt.endswith("-"):
                    p["text"] = pt[:-1] + e["text"]; continue
                if (not fin_phrase and suite) or dernier.lower() in FONCTION and not fin_phrase:
                    p["text"] = pt + " " + e["text"]; continue
        res.append(e)
    for e in res:
        e["text"] = re.sub(r"([a-z])- ([a-z])", r"\1\2", e["text"]).strip()
    return res

pdf = pdfplumber.open(SRC)
sec = None; col = None; last = None; out = collections.OrderedDict()
for pn in PAGES:
    rows = lignes(pdf.pages[pn - 1])
    bnd = frontiere(rows)
    notes = False
    for r in rows:
        w = r["w"]; t = " ".join(x["text"] for x in w).strip()
        if ("APPENDIX" in t and re.search(r"\d\s*$", t)) or "YALE ORIENTAL" in t or t == "APPENDIX.":
            continue
        hit = [k for k, rx in HEAD if rx.match(t)]
        if hit:
            sec = hit[0]; col = None; last = None; notes = False
            if sec != "D":
                out.setdefault(sec, [])
            continue
        if sec is None or sec == "D" or t.startswith("TRANSLITERATION"):
            continue
        m = COL.match(t)
        if m:
            col = m.group(1); last = None; notes = False; continue
        if NOTE.match(t):
            notes = True
        if notes or bnd is None:
            continue
        left = [x for x in w if x["x0"] < bnd]
        right = [x for x in w if x["x0"] >= bnd]
        rt = " ".join(x["text"] for x in right).strip()
        if not rt:
            continue
        n = int(left[0]["text"]) if left and re.fullmatch(r"\d{1,3}", left[0]["text"]) else None
        if left or last is None:
            last = {"col": col, "n": n, "text": rt, "page": pn}
            out[sec].append(last)
        else:
            last["text"] += " " + rt

sections = []
for k, L in out.items():
    L = fusion(L)
    if k == "A":
        c = False
        for e in L:
            if e["col"] == "VIII" and e["n"] == 440:
                c = True
            if c:
                e["kind"] = "colophon"
    sections.append({"id": k, "title": TITRES[k], "entries": [
        {key: v for key, v in e.items() if v is not None} for e in L]})

data = {
    "work": "Atrahasis (Atra-hasis epic)",
    "edition": "A. T. Clay, A Hebrew Deluge Story in Cuneiform and other epic fragments in the Pierpont Morgan Library, Yale Oriental Series Researches V-3, 1922 (appendix, sections A-C: translation column only)",
    "license": "Public domain (1922). Scan: Stony Brook University Libraries, Iraqi Archaeology Digital Texts Collection.",
    "note": "Traduction anglaise de 1922, tres fragmentaire et depassee : ces fragments ne sont qu'une petite partie de l'epopee. Les traductions modernes completes (Lambert & Millard 1969, Foster, Dalley, etc.) sont sous droit d'auteur et ne sont pas incluses. Les numeros 'n' sont ceux imprimes par Clay (un vers sur cinq), 'col' la colonne de la tablette. Les 'colophon' sont des mentions de scribe. Texte issu d'un OCR : quelques erreurs possibles. Les notes et theories de Clay (etymologies 'amorites'/hebraiques) sont exclues du texte.",
    "sections": sections,
}
io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))
print("Fichier:", OUT)
for s in sections:
    E = s["entries"]
    cols = collections.Counter(e.get("col") for e in E)
    print("Section %s : %3d lignes  colonnes=%s  colophon=%d" % (s["id"], len(E), dict(cols), sum(1 for e in E if e.get("kind"))))