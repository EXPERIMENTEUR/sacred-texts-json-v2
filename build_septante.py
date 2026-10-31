# -*- coding: ascii -*-
# Construit septuagint_complete.json a partir de septante_usfm.zip
# (L. C. L. Brenton, The Septuagint Version of the Old Testament with an English Translation, 1851 ;
#  edition USFM d'eBible.org, domaine public).
# Garde les versets ; exclut introductions, prefaces, errata, appendices, notes de bas de page et renvois.
import re, json, io, zipfile, collections

SRC = "septante_usfm.zip"
OUT = "septuagint_complete.json"

OT = "Old Testament"
AP = "Apocrypha"
# (code, libelle, groupe) dans l'ordre de l'edition Brenton (eBible)
LIVRES = [
    ("GEN", "Genesis", OT), ("EXO", "Exodus", OT), ("LEV", "Leviticus", OT), ("NUM", "Numbers", OT),
    ("DEU", "Deuteronomy", OT), ("JOS", "Joshua", OT), ("JDG", "Judges", OT), ("RUT", "Ruth", OT),
    ("1SA", "Kings I (1 Samuel)", OT), ("2SA", "Kings II (2 Samuel)", OT), ("1KI", "Kings III (1 Kings)", OT),
    ("2KI", "Kings IV (2 Kings)", OT), ("1CH", "Chronicles I", OT), ("2CH", "Chronicles II", OT),
    ("EZR", "Esdras II (Ezra and Nehemiah)", OT),
    ("JOB", "Job", OT), ("PSA", "Psalms (Septuagint numbering)", OT), ("PRO", "Proverbs", OT),
    ("ECC", "Ecclesiastes", OT), ("SNG", "Song of Solomon", OT),
    ("ISA", "Esaias (Isaiah)", OT), ("JER", "Jeremias (Jeremiah)", OT), ("LAM", "Lamentations", OT),
    ("EZK", "Jezekiel (Ezekiel)", OT), ("HOS", "Osee (Hosea)", OT), ("JOL", "Joel", OT), ("AMO", "Amos", OT),
    ("OBA", "Obdias (Obadiah)", OT), ("JON", "Jonas (Jonah)", OT), ("MIC", "Michaeas (Micah)", OT),
    ("NAM", "Naum (Nahum)", OT), ("HAB", "Ambacum (Habakkuk)", OT), ("ZEP", "Sophonias (Zephaniah)", OT),
    ("HAG", "Aggaeus (Haggai)", OT), ("ZEC", "Zacharias (Zechariah)", OT), ("MAL", "Malachias (Malachi)", OT),
    ("TOB", "Tobit", AP), ("JDT", "Judith", AP), ("ESG", "Esther (Greek)", AP), ("DAG", "Daniel (Greek)", AP),
    ("WIS", "Wisdom of Solomon", AP), ("SIR", "Sirach", AP), ("BAR", "Baruch", AP), ("LJE", "Epistle of Jeremy", AP),
    ("SUS", "Susanna", AP), ("BEL", "Bel and the Dragon", AP), ("1MA", "Maccabees I", AP), ("2MA", "Maccabees II", AP),
    ("1ES", "Esdras I", AP), ("MAN", "Prayer of Manasses", AP), ("3MA", "Maccabees III", AP), ("4MA", "Maccabees IV", AP),
]
# NEH est un doublon de la fin d'EZR (Esdras II = Ezra 1-10 + Nehemiah 11-23) : ignore volontairement.

def propre(t):
    t = re.sub(r"\\f\s.*?\\f\*", "", t)          # notes de bas de page
    t = re.sub(r"\\x\s.*?\\x\*", "", t)          # renvois
    t = re.sub(r"\\[a-z0-9]+\*?", "", t)         # marqueurs restants (\add, \sc, \it, \vp...)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    return t

z = zipfile.ZipFile(SRC)
fichiers = {}
for nom in z.namelist():
    m = re.match(r"^\d+-([A-Z0-9]{3})eng-Brenton\.usfm$", nom)
    if m:
        fichiers[m.group(1)] = z.read(nom).decode("utf-8-sig")

livres = []
for code, titre, groupe in LIVRES:
    s = fichiers[code].replace("\r", "")
    chapitres, cur, supp, alt, titre_suivant = [], None, [], None, False
    for ligne in s.split("\n"):
        ligne = ligne.rstrip()
        m = re.match(r"^\\c\s+(\d+)", ligne)
        if m:
            cur = {"chapter": int(m.group(1)), "verses": []}
            chapitres.append(cur)
            continue
        if ligne.startswith("\\mt2"):
            alt = propre(ligne[4:])
            continue
        if cur is None:
            continue
        if ligne.startswith("\\d ") or ligne == "\\d":
            titre_suivant = True
            continue
        m = re.match(r"^\\v\s+(\d+[a-z]?)\s*(.*)$", ligne)
        if m:
            texte = propre(m.group(2))
            if texte:
                vv = {"v": m.group(1), "text": texte}
                if titre_suivant:
                    vv["superscription"] = True
                cur["verses"].append(vv)
            titre_suivant = False
            continue
        if ligne.startswith(("\\ip", "\\im", "\\is")):
            t = propre(re.sub(r"^\\[a-z0-9]+\s*", "", ligne))
            if t:
                supp.append(t)
    livre = {"code": code, "title": titre, "group": groupe, "chapters": chapitres}
    if alt:
        livre["alt_title"] = alt
    if supp:
        livre["supplements"] = supp
    livres.append(livre)

data = {
    "work": "Septuagint (Greek Old Testament)",
    "edition": "Lancelot C. L. Brenton, The Septuagint Version of the Old Testament, with an English Translation, 1851 (1844 for the Old Testament text, Authorised Version adapted for the Apocrypha); USFM edition by eBible.org",
    "license": "Public domain (1851).",
    "note": "Traduction anglaise de 1851 de la Septante (texte grec du Vaticanus, complete par l'Alexandrinus) ; les traductions modernes (NETS, LXX2012...) ne sont pas incluses. Les mots en italique de Brenton (ajouts au grec), les notes de bas de page et les renvois ont ete retires ; seul le texte des versets est conserve. Les psaumes suivent la numerotation de la Septante (151 psaumes), differente de l'hebreu ; le verset 1 est souvent un titre, marque 'superscription'. Proverbes 30:1 est vide dans l'edition (Brenton renvoie au chapitre 24) et a ete omis. Le livre Nehemiah du fichier source, doublon de la fin d'Esdras II, est ignore. Brenton nomme certains livres autrement (Kings I-IV, Esaias...) : l'equivalent moderne est entre parentheses.",
    "books": livres,
}
io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))

print("Fichier:", OUT)
tot = 0
for l in livres:
    nv = sum(len(c["verses"]) for c in l["chapters"])
    tot += nv
    print("%-34s chapitres=%3d versets=%4d" % (l["title"], len(l["chapters"]), nv))
print("TOTAL versets:", tot, "livres:", len(livres))