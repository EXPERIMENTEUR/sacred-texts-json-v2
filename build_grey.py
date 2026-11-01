#!/usr/bin/env python3
# -*- coding: ascii -*-
"""Construit grey_polynesian_complete.json a partir de grey_html.zip.

Source : Sir George Grey, "Polynesian Mythology and Ancient Traditional History
of the New Zealand Race, as furnished by their Priests and Chiefs" (Londres,
1855), transcription Internet Sacred Text Archive (une page par legende).
Domaine public.

ATTENTION : c'est la version anglaise de Grey, pas les recits maoris
d'origine. Grey a compile des manuscrits maoris (surtout de Te Rangikaheke),
avec des modifications, des fusions et des omissions (certaines signalees par
ses notes : "considerably shortened in the translation").

Gardes : les 23 legendes (paragraphes de recit "texte" et chants "chant"),
et les notes de bas de page de Grey (separees). Exclus : la page de titre, le
sommaire, la preface (conservee a part), et l'appendice (essai de musicologie
sur les gammes grecques, sans rapport avec les mythes).
"""
import html
import json
import re
import sys
import zipfile

ZIP = "grey_html.zip"
OUT = "grey_polynesian_complete.json"
PAGES = ["grey%02d.htm" % i for i in range(3, 26)]   # 23 legendes
RE_FOLIO = re.compile(r"<A NAME=\"page_(\d+)\"><FONT[^>]*>p\. \d+</FONT></A>", re.I)
RE_RENVOI = re.compile(r"(?:&nbsp;)?\s*<A NAME=\"fr_\d+\"></A><A HREF=\"#fn_\d+\"><FONT[^>]*>\d+</FONT></A>", re.I)


def net(frag):
    frag = RE_RENVOI.sub("", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = html.unescape(frag)
    frag = frag.replace(chr(0xa0), " ")
    frag = re.sub(r"\s+", " ", frag).strip()
    frag = re.sub(r"\s+([,.;:!?])", r"\1", frag)
    return frag


def lire(zf, nom):
    return zf.read(nom).decode("utf-8", errors="replace")


def legende(zf, nom, num):
    s = lire(zf, nom)
    m1 = re.search(r"<H1[^>]*>(.*?)</H1>", s, flags=re.S | re.I)
    if not m1:
        print("ERREUR: pas de titre dans", nom)
        sys.exit(1)
    titre = net(m1.group(1))
    titre = re.sub(r"\s*\d+$", "", titre)          # renvoi colle au titre
    avant = s[:m1.start()]
    apres = s[m1.end():]

    # page de depart = dernier marqueur avant le titre
    pg = re.findall(r"page_(\d+)", avant)
    page = int(pg[-1]) if pg else 1

    # fin du corps : titre "Footnotes" ou lien "Next:"
    mf = re.search(r"<H3[^>]*>\s*Footnotes\s*</H3>", apres, flags=re.I)
    mn = re.search(r"<A HREF=\"grey\d+\.htm\">Next:", apres, flags=re.I)
    if mf:
        corps, zone_notes = apres[:mf.start()], apres[mf.end():]
    elif mn:
        corps, zone_notes = apres[:mn.start()], ""
    else:
        corps, zone_notes = apres, ""

    # sous-titre : H3 ou premier <P ALIGN="CENTER">
    sous = ""
    m3 = re.match(r"\s*<H3[^>]*>(.*?)</H3>", corps, flags=re.S | re.I)
    if m3:
        sous = net(m3.group(1))
        corps = corps[m3.end():]
    else:
        mc = re.match(r"\s*<P ALIGN=\"CENTER\">(.*?)</P>", corps, flags=re.S | re.I)
        if mc:
            sous = net(mc.group(1))
            corps = corps[mc.end():]
    sous = re.sub(r"\s*\d+$", "", sous)

    paragraphes = []
    for mp in re.finditer(r"<P[^>]*>(.*?)</P>", corps, flags=re.S | re.I):
        c = mp.group(1)
        pages = [page]
        for t in RE_FOLIO.finditer(c):
            page = int(t.group(1))
            if page not in pages:
                pages.append(page)
        c = RE_FOLIO.sub(" ", c)
        continue_ = "[paragraph continues]" in c
        c = c.replace("[paragraph continues]", " ")
        est_chant = bool(re.search(r"<BR", c, flags=re.I))
        if est_chant:
            lignes = [net(x) for x in re.split(r"<BR\s*/?>", c, flags=re.I)]
            lignes = [x for x in lignes if x]
            texte = " ".join(lignes)
        else:
            lignes = None
            texte = net(c)
        if not texte:
            continue
        if continue_ and paragraphes:
            prec = paragraphes[-1]
            prec["text"] = (prec["text"] + " " + texte).strip()
            if lignes and prec["kind"] == "chant":
                prec["lines"].extend(lignes)
            if pages[-1] != prec["_p1"]:
                prec["_p2"] = pages[-1]
            continue
        p = {"kind": "chant" if est_chant else "texte", "text": texte,
             "_p1": pages[0], "_p2": pages[-1]}
        if lignes:
            p["lines"] = lignes
        paragraphes.append(p)

    # numerotation et pages
    for k, p in enumerate(paragraphes, 1):
        p["n"] = k
        a, b = p.pop("_p1"), p.pop("_p2")
        p["pages"] = str(a) if a == b else "%d-%d" % (a, b)
    # initiale en majuscules ("MEN had" -> "Men had")
    if paragraphes:
        mots = paragraphes[0]["text"].split(" ")
        for i in range(min(4, len(mots))):
            noyau = re.sub(r"[^A-Za-z-]", "", mots[i])
            if len(noyau) > 1 and noyau.isupper():
                bas = mots[i].lower()
                j = next(k for k, ch in enumerate(bas) if ch.isalpha())
                mots[i] = bas[:j] + bas[j].upper() + bas[j + 1:]
        paragraphes[0]["text"] = " ".join(mots)

    # notes de Grey
    notes = []
    for mp in re.finditer(r"<P[^>]*>(.*?)</P>", zone_notes, flags=re.S | re.I):
        c = mp.group(1)
        mm = re.match(r"\s*<A NAME=\"fn_(\d+)\"></A><A HREF=\"[^\"]*\">(\d+):(\d+)</A>(.*)", c, flags=re.S | re.I)
        if mm:
            notes.append({"id": int(mm.group(1)), "page": int(mm.group(2)),
                          "text": net(RE_FOLIO.sub(" ", mm.group(4)))})
        elif notes:
            t = net(RE_FOLIO.sub(" ", c))
            if t and "Next:" not in t:
                notes[-1]["text"] += " " + t
    return {"id": num, "file": nom, "title": titre, "subtitle": sous,
            "paragraphs": paragraphes, "notes": notes}


def main():
    zf = zipfile.ZipFile(ZIP)
    noms = set(zf.namelist())
    # accepte les zips avec ou sans dossier
    base = {n.split("/")[-1]: n for n in noms}
    for p in PAGES + ["grey01.htm"]:
        if p not in base:
            print("ERREUR: page manquante dans le zip :", p)
            sys.exit(1)

    class Z:
        def read(self, n):
            return zf.read(base[n])
    z = Z()

    legendes = [legende(z, nom, k + 1) for k, nom in enumerate(PAGES)]

    # preface (a part)
    s = lire(z, "grey01.htm")
    i = re.search(r"<H\d[^>]*>\s*PREFACE", s, flags=re.I)
    pref = []
    if i:
        corps = s[i.end():]
        fin = re.search(r"<A HREF=\"grey\d+\.htm\">Next:", corps, flags=re.I)
        if fin:
            corps = corps[:fin.start()]
        for mp in re.finditer(r"<P[^>]*>(.*?)</P>", corps, flags=re.S | re.I):
            t = net(RE_FOLIO.sub(" ", mp.group(1)))
            if t:
                pref.append(t)

    data = {
        "title": "Polynesian Mythology and Ancient Traditional History of the New Zealand Race",
        "author": "Sir George Grey (compilateur et traducteur)",
        "edition": "John Murray, Londres, 1855 ; transcription Sacred-Texts.com",
        "note": ("Version anglaise de Grey, pas les recits maoris d'origine : "
                 "compilation de manuscrits maoris (surtout de Te Rangikaheke) avec "
                 "modifications, fusions et omissions. Les paragraphes kind=chant "
                 "sont des passages en vers. L'appendice musicologique est exclu."),
        "preface": pref,
        "legends": legendes,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    tm = tp = tn = 0
    for lg in legendes:
        mots = sum(len(p["text"].split()) for p in lg["paragraphs"])
        nch = sum(1 for p in lg["paragraphs"] if p["kind"] == "chant")
        tm += mots
        tp += len(lg["paragraphs"])
        tn += len(lg["notes"])
        print("%2d. %-52s %3d par. (%d chants) %5d mots, %d notes"
              % (lg["id"], lg["title"][:52], len(lg["paragraphs"]), nch, mots, len(lg["notes"])))
    print("TOTAL : %d legendes, %d paragraphes, %d mots, %d notes de Grey" % (len(legendes), tp, tm, tn))


if __name__ == "__main__":
    main()
