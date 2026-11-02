# -*- coding: ascii -*-
"""Gathas, Yasna, Visparad, Afrinagan, Gahs, Fragments (Mills 1887, SBE vol. 31) :
construit mills_avesta.json a partir des pages sbe31005..sbe31117 + sbe31_index.htm.
kinds : texte / indication (etiquettes de locuteurs) / intro_traducteur ; plus notes."""
import html, json, os, re, sys

DOSSIER = sys.argv[1] if len(sys.argv) > 1 else "sbe31_html"
INDEX = sys.argv[2] if len(sys.argv) > 2 else "sbe31_index.htm"
SORTIE = sys.argv[3] if len(sys.argv) > 3 else "mills_avesta.json"

def lire(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def nettoie(h):
    h = re.sub(r"<A NAME=\"page_\d+\">.*?</A>", " ", h, flags=re.I | re.S)
    h = re.sub(r"<A NAME=\"fr_\d+\"></A>\s*<A HREF=\"#fn_\d+\">.*?</A>", "", h, flags=re.I | re.S)
    h = re.sub(r"<A NAME=\"img_\d+\"></A>\s*<IMG[^>]*>", "[?]", h, flags=re.I | re.S)
    h = re.sub(r"\[paragraph continues\]", " ", h)
    h = re.sub(r"<br\s*/?>", " ", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace(chr(0xa0), " ")
    h = re.sub(r"\s+", " ", h).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", h)

RX_P = re.compile(r"<p([^>]*)>(.*?)</p>", re.I | re.S)
RX_FN = re.compile(r"<P><A NAME=\"fn_(\d+)\"></A><A HREF=\"[^\"]*\">([^<]*)</A>(.*?)</P>", re.I | re.S)
RX_VERS = re.compile(r"^\[?(\d+)(?:-(\d+))?((?:,\s*\d+)*)\.?\s*(?:\(([^)]*)\)\.?)?\s")
RX_PAGE = re.compile(r"^p\. \d+( p\. \d+)*$")

# plan : (premiere page, derniere page, groupe)
GROUPES = [(6, 22, "Gathas"), (23, 77, "Yasna"), (78, 100, "Visparad"),
           (101, 103, "Afrinagan"), (104, 108, "Gahs"), (109, 117, "Fragments")]

titres_index = {}
for m in re.finditer(r"<A HREF=\"sbe31(\d{3})\.htm\">(.*?)</A>", lire(INDEX), re.I | re.S):
    titres_index[int(m.group(1))] = nettoie(m.group(2))

sections = []
for debut, fin, groupe in GROUPES:
    for n in range(debut, fin + 1):
        nom = "sbe31%03d.htm" % n
        s = lire(os.path.join(DOSSIER, nom))
        corps = s.split('<A NAME="fn_')[0]
        corps = corps[corps.find("sacred-texts.com</FONT></P>") + 20:]
        brutes = []
        for a, b in RX_P.findall(corps):
            t = nettoie(b)
            if not t or RX_PAGE.match(t) or t.startswith("Next:") or t.startswith("Previous"):
                continue
            est_font = bool(re.search(r'<FONT SIZE="?-1"?', re.sub(r"<A NAME=\"fr_\d+\"></A>\s*<A HREF=\"#fn_\d+\">.*?</A>", "", b, flags=re.I | re.S), re.I))
            centre = "center" in a.lower()
            brutes.append((t, est_font, centre))
        paras = []
        gatha = groupe == "Gathas"
        apres_trad = not gatha
        premier_vers = False
        for t, est_font, centre in brutes:
            if re.fullmatch(r"_{5,}", t):
                continue
            if gatha and not apres_trad:
                if re.fullmatch(r"Translation\.?", t):
                    apres_trad = True
                else:
                    paras.append({"kind": "intro_traducteur", "text": t})
                continue
            if gatha and re.fullmatch(r"Translation\.?", t):
                continue
            if centre:
                paras.append({"kind": "indication", "text": t})
                continue
            mv = RX_VERS.match(t + " ") if len(t) > 12 or re.match(r"^\[?\d", t) else None
            if mv:
                premier_vers = True
                prec = [p["n"] for p in paras if p["kind"] == "texte" and p["n"]]
                num = int(mv.group(1))
                attendu = (prec[-1] + 1) if prec else 1
                if prec:
                    erreur = not (prec[-1] <= num <= prec[-1] + 5)
                else:
                    erreur = num > 5
                fin_v = re.findall(r"\d+", (mv.group(2) or "") + " " + (mv.group(3) or ""))
                paras.append({"kind": "texte", "n": attendu if erreur else num,
                              "n_fin": int(fin_v[-1]) if fin_v else None, "n_alt": mv.group(4),
                              "n_imprime": num if erreur else None, "text": t[mv.end() - 1:].strip()})
            elif not premier_vers and not gatha and (est_font or (len(t.split()) > 40 and not t.startswith("(")) or t.startswith("This chapter")):
                paras.append({"kind": "intro_traducteur", "text": t})
            elif paras and paras[-1]["kind"] == "texte":
                paras[-1]["text"] += " " + t
            else:
                paras.append({"kind": "texte", "n": None, "text": t})
        hs = [nettoie(h) for h in re.findall(r"<h[1-5][^>]*>(.*?)</h[1-5]>", corps, re.I | re.S)]
        hs = [h for h in hs if h and h != "Footnotes"]
        notes = [{"ref": nettoie(m.group(2)), "text": nettoie(m.group(3))} for m in RX_FN.finditer(s)]
        sections.append({"id": len(sections) + 1, "groupe": groupe, "titre": titres_index.get(n, hs[0] if hs else "?"),
                         "en_tetes": hs[:4], "source": nom, "paragraphs": paras, "notes": notes})

out = {
    "title": "The Zend Avesta, Part III (Gathas, Yasna, Visparad, Afrinagan, Gahs, Fragments)",
    "translator": "L. H. Mills (1887), Sacred Books of the East vol. 31",
    "note": "kind=texte : traduction (les parentheses sont des ajouts interpretatifs de Mills) ; indication : etiquettes de locuteurs, sous-titres ; intro_traducteur : introductions et resumes de Mills (exclus de l'analyse) ; notes : notes de bas de page (exclues).",
    "sections": sections,
}
with open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
tt = ti = tn = 0
for sec in sections:
    mw = lambda k: sum(len(p["text"].split()) for p in sec["paragraphs"] if p["kind"] == k)
    vs = [p for p in sec["paragraphs"] if p["kind"] == "texte"]
    tt += mw("texte"); ti += mw("intro_traducteur"); tn += len(sec["notes"])
    print("%3d %-10s %-40s v%3d texte %5d intro %5d ind %2d notes %3d" % (
        sec["id"], sec["groupe"], sec["titre"][:40].encode("ascii", "replace").decode(), len(vs), mw("texte"),
        mw("intro_traducteur"), sum(1 for p in sec["paragraphs"] if p["kind"] == "indication"), len(sec["notes"])))
print("TOTAL : texte %d mots, intro %d mots, %d notes" % (tt, ti, tn))
