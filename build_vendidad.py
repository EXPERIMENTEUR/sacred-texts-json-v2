# -*- coding: ascii -*-
"""Vendidad (Darmesteter 1880, SBE vol. 4) : construit vendidad_darmesteter.json
a partir des pages HTML sbe0407..sbe0428. Separe : texte / intro_traducteur / notes."""
import html, json, os, re, sys

DOSSIER = sys.argv[1] if len(sys.argv) > 1 else "sbe04_html"
SORTIE = sys.argv[2] if len(sys.argv) > 2 else "vendidad_darmesteter.json"

def lire(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def nettoie(h):
    h = re.sub(r"<A NAME=\"page_\d+\">.*?</A>", " ", h, flags=re.I | re.S)
    h = re.sub(r"<A NAME=\"fr_\d+\"></A>\s*<A HREF=\"#fn_\d+\">.*?</A>", "", h, flags=re.I | re.S)
    h = re.sub(r"<br\s*/?>", " ", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace(chr(0xa0), " ")
    h = re.sub(r"\s+", " ", h).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", h)

RX_P = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
RX_FN = re.compile(r"<P><A NAME=\"fn_(\d+)\"></A><A HREF=\"[^\"]*\">([^<]*)</A>(.*?)</P>", re.I | re.S)
RX_VERS = re.compile(r"^\[?(\d+)((?:,\s*\d+)*)\.?\s*(?:\(([^)]*)\)\.?)?\s")

fargards = []
for n in range(7, 29):
    s = lire(os.path.join(DOSSIER, "sbe04%02d.htm" % n))
    corps, _, _ = s.partition('<A NAME="fn_')
    m = re.search(r"<h2[^>]*>(.*?)</h2>", corps, re.I | re.S)
    titre = nettoie(m.group(1)) if m else "?"
    m3 = re.search(r"<h3[^>]*>(.*?)</h3>", corps, re.I | re.S)
    sous = ""
    for m3 in re.finditer(r"<h3[^>]*>(.*?)</h3>", corps, re.I | re.S):
        sous = nettoie(m3.group(1))
        break
    brutes = []
    for pm in RX_P.finditer(corps):
        t = nettoie(pm.group(1))
        if t and not t.startswith("The Zend Avesta, Part I"):
            brutes.append(t)
    debut = next((i for i, t in enumerate(brutes) if re.match(r"^\[?1(?:\s*\(\d+\))?\.?\s", t)), None)
    if debut is None:
        print("ERREUR : verset 1 introuvable dans", n)
        sys.exit(1)
    paras = [{"kind": "intro_traducteur", "text": t} for t in brutes[:debut]]
    for t in brutes[debut:]:
        mv = RX_VERS.match(t + " ") if RX_VERS.match(t + " ") and len(t) > 12 else None
        prec = [p["n"] for p in paras if p["kind"] == "texte" and p["n"]]
        num = int(mv.group(1)) if mv else None
        if mv:
            erreur = bool(prec) and (num < prec[-1] or num > prec[-1] + 5)
            fin = re.findall(r"\d+", mv.group(2) or "")
            paras.append({"kind": "texte", "n": prec[-1] + 1 if erreur else num,
                          "n_fin": int(fin[-1]) if fin else None, "n_alt": mv.group(3),
                          "n_imprime": num if erreur else None,
                          "text": t[mv.end() - 1:].strip()})
        elif paras and paras[-1]["kind"] == "texte":
            paras[-1]["text"] += " " + t
        else:
            paras.append({"kind": "texte", "n": None, "text": t})
    notes = []
    for fm in RX_FN.finditer(s):
        notes.append({"ref": nettoie(fm.group(2)), "text": nettoie(fm.group(3))})
    fargards.append({"fargard": len(fargards) + 1, "titre": "FARGARD %d" % (len(fargards) + 1), "sous_titre": sous,
                     "source": "sbe04%02d.htm" % n, "paragraphs": paras, "notes": notes})

out = {
    "title": "The Vendidad (Zend Avesta, Part I)",
    "translator": "James Darmesteter (1880), Sacred Books of the East vol. 4",
    "note": "kind=texte : traduction ; intro_traducteur : resume/commentaire de Darmesteter (exclu de l'analyse) ; notes : notes de bas de page de Darmesteter (exclues).",
    "fargards": fargards,
}
with open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
tt = ti = nn = 0
for fg in fargards:
    mt = sum(len(p["text"].split()) for p in fg["paragraphs"] if p["kind"] == "texte")
    mi = sum(len(p["text"].split()) for p in fg["paragraphs"] if p["kind"] != "texte")
    tt += mt; ti += mi; nn += len(fg["notes"])
    print("%2d %-14s %-30s texte %5d  intro %4d  notes %3d" % (fg["fargard"], fg["titre"], fg["sous_titre"][:30].encode("ascii", "replace").decode(), mt, mi, len(fg["notes"])))
print("TOTAL : texte %d mots, intro %d mots, %d notes" % (tt, ti, nn))
