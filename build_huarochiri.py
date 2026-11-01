#!/usr/bin/env python3
# -*- coding: ascii -*-
"""Construit huarochiri_avila_complete.json a partir de huarochiri_avila.htm.

Source : "A Narrative of the Errors, False Gods, and other Superstitions and
Diabolical Rites in which the Indians of the Provinces of Huarochiri, Mama and
Chaclla lived in ancient times", recueilli par le Dr Francisco de Avila (1608),
traduit par Clements R. Markham (Hakluyt Society, 1873), dans "Narratives of the
Rites and Laws of the Yncas". Transcription : Internet Sacred Text Archive.
Domaine public.

ATTENTION : ce n'est PAS le manuscrit quechua de Huarochiri (dont les
traductions modernes sont sous droit), mais le recit de Avila, un pretre
espagnol, qui melange recits indigenes et refutations theologiques.
Chaque paragraphe est donc classe : "texte" (recit rapporte) ou
"commentaire_avila" (reflexions, refutations de Avila) ou "note_editeur".
"""
import html
import json
import re
import sys

SRC = "huarochiri_avila.htm"
OUT = "huarochiri_avila_complete.json"

# Paragraphes de Avila (commentaire), reperes par leur debut.
# Chaque regle : debut du paragraphe -> liste (marqueur, genre). Le marqueur
# None designe le debut du paragraphe. Un paragraphe sans regle est un recit.
REGLES = {
    "In all the stories and fables": [
        (None, "commentaire_avila"),
        ("They relate that, a long time ago", "texte"),
        ("This may have been the eclipse", "commentaire_avila")],
    "It is necessary to go back a step": [
        (None, "commentaire_avila"),
        ("They relate that there was nearly", "texte"),
        ("This is a notable absurdity", "commentaire_avila")],
    "According to the most certain and true opinion": [
        (None, "commentaire_avila")],
    "It is certain that there were no inhabitants": [
        (None, "commentaire_avila")],
    "The above traditions are so rooted": [(None, "commentaire_avila")],
    "Also as regards the fox": [(None, "commentaire_avila")],
    "As to the falcon": [(None, "commentaire_avila")],
    "Who will not grieve": [(None, "commentaire_avila")],
    "(Here was to be added": [(None, "note_editeur")],
    "HERE THE MANUSCRIPT ENDS": [(None, "note_editeur")],
}

ROMAINS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def nettoyer(frag):
    frag = re.sub(r"<A NAME=\"[^\"]*\"></A><A HREF=\"#[^\"]*\"><FONT SIZE=1>\d+</FONT></A>", "", frag, flags=re.I)
    frag = re.sub(r"(\w)<SMALL>(\w+)</SMALL>", lambda m: m.group(1) + m.group(2).lower(), frag)
    frag = re.sub(r"<BR\s*/?>", " ", frag, flags=re.I)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = html.unescape(frag)
    frag = frag.replace(chr(0x2003), " ").replace(chr(0xa0), " ")
    frag = re.sub(r"\s+", " ", frag).strip()
    return frag


def decouper(texte, regle):
    """Decoupe un paragraphe selon une regle -> liste de (genre, texte)."""
    reperes = []
    for marq, genre in regle:
        pos = 0 if marq is None else texte.find(marq)
        if pos < 0:
            print("ERREUR: marqueur introuvable :", marq)
            sys.exit(1)
        reperes.append((pos, genre))
    reperes.sort()
    morceaux = []
    for k, (pos, genre) in enumerate(reperes):
        fin = reperes[k + 1][0] if k + 1 < len(reperes) else len(texte)
        t = texte[pos:fin].strip()
        if t:
            morceaux.append((genre, t))
    return morceaux


def main():
    with open(SRC, encoding="utf-8") as f:
        brut = f.read()

    # notes de bas de page (Markham)
    i_notes = brut.index("footnotes======================")
    corps, zone_notes = brut[:i_notes], brut[i_notes:]
    notes = []
    for m in re.finditer(r"<A NAME=\"page_(\d+)_note_(\d+)\"></A>.*?</A>\s*(.*?)</P>", zone_notes, flags=re.S | re.I):
        notes.append({"page": int(m.group(1)), "n": int(m.group(2)),
                      "text": nettoyer(m.group(3))})

    # jetons de page
    corps = re.sub(r"<!-+page \d+-+>\s*<A NAME=\"page_(\d+)\"><FONT[^>]*>p\. \d+</FONT></A>",
                   lambda m: " @@P%s@@ " % m.group(1), corps, flags=re.I)

    # avant-propos : tout ce qui precede le chapitre I
    i1 = re.search(r"<H3[^>]*>CHAPTER I\.</H3>", corps, flags=re.I)
    avant, chap = corps[:i1.start()], corps[i1.start():]
    glossaire = []
    for m in re.finditer(r"<P>&#8195;(.*?)</P>", avant, flags=re.S | re.I):
        glossaire.append(nettoyer(m.group(1)))
    front = {
        "title": "A Narrative of the Errors, False Gods, and other Superstitions and Diabolical Rites in which the Indians of the Provinces of Huarochiri, Mama and Chaclla lived in ancient times",
        "collected_by": "Dr Francisco de Avila, cure de San Damian (Huarochiri)",
        "year": 1608,
        "glossary": glossaire,
    }

    # chapitres
    morceaux = re.split(r"<H3[^>]*>CHAPTER ([IVX]+)\.</H3>", chap)
    # morceaux = ['', 'I', corps1, 'II', corps2, ...]
    chapitres = []
    page = 123
    for k in range(1, len(morceaux), 2):
        romain, cc = morceaux[k], morceaux[k + 1]
        resume = ""
        mq = re.search(r"<BLOCKQUOTE>(.*?)</BLOCKQUOTE>", cc, flags=re.S | re.I)
        if mq:
            resume = nettoyer(mq.group(1))
            cc = cc.replace(mq.group(0), "")
        paragraphes = []
        n = 0
        for mp in re.finditer(r"<P[^>]*>(.*?)</P>", cc, flags=re.S | re.I):
            c = mp.group(1)
            pages = [page]
            for t in re.findall(r"@@P(\d+)@@", c):
                page = int(t)
                if page not in pages:
                    pages.append(page)
            c = re.sub(r"@@P\d+@@", " ", c)
            t = nettoyer(c)
            if not t or t == "Next":
                continue
            regle = None
            for debut, r in REGLES.items():
                if t.startswith(debut):
                    regle = r
            morc = decouper(t, regle) if regle else [("texte", t)]
            for genre, tt in morc:
                n += 1
                paragraphes.append({
                    "n": n, "kind": genre, "text": tt,
                    "pages": "%d" % pages[0] if len(pages) == 1 else "%d-%d" % (pages[0], pages[-1]),
                })
        chapitres.append({"chapter": ROMAINS.index(romain) + 1, "roman": romain,
                          "summary": resume, "paragraphs": paragraphes})

    if [c["chapter"] for c in chapitres] != list(range(1, 9)):
        print("ERREUR: chapitres inattendus", [c["roman"] for c in chapitres])
        sys.exit(1)

    data = {
        "title": "Narrative of the Errors, False Gods... of Huarochiri",
        "author": "Francisco de Avila (1608)",
        "translator": "Clements R. Markham",
        "edition": "Hakluyt Society, Londres, 1873 ; transcription Sacred-Texts.com",
        "note": ("Recit d'un pretre espagnol, pas le manuscrit quechua de "
                 "Huarochiri. Les paragraphes kind=commentaire_avila sont les "
                 "reflexions et refutations de Avila ; kind=note_editeur sont "
                 "des notes de l'edition ; kind=texte sont les recits rapportes."),
        "front_matter": front,
        "chapters": chapitres,
        "footnotes": notes,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    tot = {"texte": 0, "commentaire_avila": 0, "note_editeur": 0}
    for c in chapitres:
        mots = {"texte": 0, "commentaire_avila": 0, "note_editeur": 0}
        for p in c["paragraphs"]:
            mots[p["kind"]] += len(p["text"].split())
        for kk in tot:
            tot[kk] += mots[kk]
        print("Chapitre %-4s : %2d paragraphes, recit %5d mots, commentaire %4d mots"
              % (c["roman"], len(c["paragraphs"]), mots["texte"], mots["commentaire_avila"]))
    print("TOTAL : recit %d mots, commentaire d'Avila %d mots, notes d'edition %d mots ; %d notes de bas de page"
          % (tot["texte"], tot["commentaire_avila"], tot["note_editeur"], len(notes)))


if __name__ == "__main__":
    main()
