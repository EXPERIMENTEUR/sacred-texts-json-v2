# build_testaments.py - lit UNIQUEMENT testaments_sources\ (aucun acces reseau)
import re, json, html, os, glob
from collections import Counter

DOSSIER = "testaments_sources"
SORTIE = "testaments_12_patriarches_complete.json"
ORDRE = ["Reuben", "Simeon", "Levi", "Judah", "Issachar", "Zebulun", "Dan", "Naphtali", "Gad", "Asher", "Joseph", "Benjamin"]
MODELES_SUPPRIMES = Counter()

def nettoyer_wikitexte(wt):
    wt = re.sub(r"<!--.*?-->", "", wt, flags=re.S)
    wt = re.sub(r"<ref[^>/]*/>", "", wt)
    wt = re.sub(r"<ref[^>]*>.*?</ref>", "", wt, flags=re.S)
    # modeles qui entourent simplement du texte : on garde le texte
    wt = re.sub(r"\{\{(?:sc|smaller|larger|uc|lc|dropinitial|di|small-caps)\|([^{}|]*)\}\}", r"\1", wt, flags=re.I)
    # les autres modeles (en-tete, navigation, notes) sont supprimes, du plus interne au plus externe
    while True:
        def rep(m):
            MODELES_SUPPRIMES[m.group(0)[2:].split("|")[0].split("}")[0].strip().lower()[:30]] += 1
            return ""
        nouveau = re.sub(r"\{\{[^{}]*\}\}", rep, wt)
        if nouveau == wt: break
        wt = nouveau
    wt = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", wt)
    wt = wt.replace("'''", "").replace("''", "")
    wt = re.sub(r"<[^>]+>", "", wt)
    wt = html.unescape(wt).replace("\xa0", " ")
    lignes = [re.sub(r"[ \t]+", " ", l).strip() for l in wt.split("\n")]
    return [l for l in lignes if not re.fullmatch(r"[\u2014\u2013\-_=\s]*", l) or l == ""]

def chapitres(lignes):
    attendu, courant, sortie = 1, None, []
    for l in lignes:
        m = re.match(r"^(\d{1,3})\.(?: +|$)", l)
        if m and int(m.group(1)) == attendu:
            if courant: sortie.append(courant)
            courant = {"chapter": attendu, "lignes": [l[m.end():]]}
            attendu += 1
        elif courant is not None:
            courant["lignes"].append(l)
    if courant: sortie.append(courant)
    res = []
    for c in sortie:
        paras, cur = [], []
        for l in c["lignes"]:
            if l == "":
                if cur: paras.append(" ".join(cur)); cur = []
            else:
                cur.append(l)
        if cur: paras.append(" ".join(cur))
        res.append({"chapter": c["chapter"], "text": "\n\n".join(paras)})
    return res

testaments = []
for fichier in sorted(glob.glob(os.path.join(DOSSIER, "*.json"))):
    with open(fichier, "r", encoding="utf-8") as f:
        page = json.load(f)
    m = re.search(r"The Testament of (\w+)", page["title"])
    if not m:
        continue  # introduction, note de l'editeur, page de titre : ecartees
    nom = m.group(1)
    chap = chapitres(nettoyer_wikitexte(page["wikitext"]))
    titre = page["title"].split("/")[-1]
    testaments.append({"patriarch": nom, "title": titre, "source": page["source"], "chapters": chap})

testaments.sort(key=lambda t: ORDRE.index(t["patriarch"]) if t["patriarch"] in ORDRE else 99)

print("Testaments construits :", len(testaments), "->", [t["patriarch"] for t in testaments])
for t in testaments:
    textes = [c["text"] for c in t["chapters"]]
    num = [c["chapter"] for c in t["chapters"]]
    reste = sum(1 for x in textes if re.search(r"\{\{|\[\[|<|&#|&[a-z]+;", x))
    print("  %-10s %2d chapitres (1..%s) | %6d caracteres | chapitres avec balises residuelles : %d" % (
        t["patriarch"], len(num), num[-1] if num else "-", sum(len(x) for x in textes), reste))
print("Modeles wiki supprimes :", dict(MODELES_SUPPRIMES.most_common(12)))

data = {
    "book": "Testaments of the Twelve Patriarchs",
    "translator": "Traduction anglaise parue dans Ante-Nicene Fathers, vol. VIII (a verifier : Robert Sinker)",
    "license": "Domaine public (traduction du 19e siecle).",
    "note": ("Source : Wikisource, Ante-Nicene Fathers/Volume VIII/The Testaments of the Twelve Patriarchs. "
             "Seuls les 12 testaments sont inclus ; la notice introductive du traducteur, la note de l'editeur americain "
             "et la page de titre sont exclues. Les notes de bas de page eventuelles ont ete supprimees. "
             "La datation et la presence d'interpolations chretiennes dans ce texte sont debattues parmi les chercheurs."),
    "testaments": testaments,
}
with open(SORTIE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("Ecrit :", SORTIE)