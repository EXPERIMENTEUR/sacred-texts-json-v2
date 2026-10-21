# build_avesta.py - lit UNIQUEMENT les 3 fichiers locaux de avesta_sources\ (aucun acces reseau)
import re, json, html, difflib, sys, os

DOSSIER = "avesta_sources"
SORTIE = "avesta_complete.json"
CAP = 150  # lignes gardees apres la derniere en-tete de la derniere section

def lire(nom):
    with open(os.path.join(DOSSIER, nom), "r", encoding="utf-8", errors="replace") as f:
        brut = f.read()
    # les fichiers sont des pages web enregistrees : on garde le contenu du <pre>
    if "<pre" in brut:
        debut = brut.index("<pre")
        debut = brut.index(">", debut) + 1
        fin = brut.find("</pre>", debut)
        brut = brut[debut:fin if fin != -1 else len(brut)]
    brut = html.unescape(re.sub(r"<[^>]+>", "", brut))
    return [re.sub(r"\s+", " ", l).strip() for l in brut.split("\n")]

def romain(s):
    v = {"I": 1, "V": 5, "X": 10, "L": 50}
    t = 0
    for i, c in enumerate(s):
        t += -v[c] if i + 1 < len(s) and v[c] < v[s[i + 1]] else v[c]
    return t

def lisser(hits):
    # supprime une en-tete isolee prise entre deux en-tetes identiques (erreur OCR)
    out = []
    for i, (idx, lab) in enumerate(hits):
        if 0 < i < len(hits) - 1 and hits[i - 1][1] == hits[i + 1][1] != lab:
            continue
        out.append((idx, lab))
    return out

def chaine(hits, pas_max=2):
    # plus longue suite d'en-tetes ou chaque numero vaut le precedent, +1 ou +2
    n = len(hits)
    if n == 0: return []
    best, prev = [1] * n, [-1] * n
    for i in range(n):
        for j in range(i):
            d = hits[i][1] - hits[j][1]
            if 0 <= d <= pas_max and best[j] + 1 > best[i]:
                best[i], prev[i] = best[j] + 1, j
    i = max(range(n), key=lambda k: best[k])
    out = []
    while i != -1:
        out.append(hits[i]); i = prev[i]
    return out[::-1]

def decouper(lignes, hits, est_entete, monotone):
    hits = sorted(hits)
    if monotone:
        hits = chaine(hits)
    hits = lisser(hits)
    groupes = []
    for idx, lab in hits:
        if not groupes or groupes[-1][1] != lab:
            groupes.append([idx, lab, idx, 1])
        else:
            groupes[-1][2] = idx; groupes[-1][3] += 1
    if not monotone:
        # supprime une en-tete isolee tres eloignee de ses voisines (erreur OCR)
        gardes = []
        for k, g in enumerate(groupes):
            p = groupes[k - 1][1] if k > 0 else None
            q = groupes[k + 1][1] if k + 1 < len(groupes) else None
            if g[3] == 1 and p is not None and q is not None and abs(g[1] - p) > 3 and abs(g[1] - q) > 3:
                continue
            gardes.append(g)
        groupes = gardes
    sections = []
    for k, (debut, lab, dernier, _nb) in enumerate(groupes):
        fin = groupes[k + 1][0] if k + 1 < len(groupes) else min(len(lignes), dernier + CAP)
        corps = [l for l in lignes[debut:fin] if not est_entete(l)]
        paras, cur = [], []
        for l in corps:
            if l == "":
                if cur: paras.append(" ".join(cur)); cur = []
            else:
                if cur and cur[-1].endswith("-") and l[:1].islower():
                    cur[-1] = cur[-1][:-1] + l
                else:
                    cur.append(l)
        if cur: paras.append(" ".join(cur))
        sections.append({"label": lab, "ligne_debut": debut + 1, "ligne_fin": fin,
                         "text": "\n\n".join(paras)})
    return sections

# ---------- Vendidad : en-tetes courantes "FARGARD II. 13"
RE_VEND = re.compile(r"^FARGARD ([IVXL]+)\s*[.,]?(?: [\w$;^!.']{1,4}){0,3}$")
def vendidad():
    L = lire("avesta_vendidad.txt")
    hits = [(i, romain(m.group(1))) for i, l in enumerate(L) if (m := RE_VEND.match(l)) and 1 <= romain(m.group(1)) <= 22]
    secs = decouper(L, hits, lambda l: bool(RE_VEND.match(l)) or l == "THE VENDIDAD.", True)
    return [{"fargard": s["label"], **{k: s[k] for k in ("ligne_debut", "ligne_fin", "text")}} for s in secs]

# ---------- Yashts : en-tetes courantes "ABAN YAST. 65" (OCR tres bruite)
NOMS = ["ORMAZD", "HAPTAN", "ARDIBEHESHT", "KHORDAD", "ABAN", "KHORSHED", "MAH", "TIR", "GOS",
        "MIHIR", "SROSH", "RASHN", "FARVARDIN", "BAHRAM", "RAM", "DIN", "ASHI", "ASHTAD",
        "ZAMYAD", "VANANT", "VISHTASP"]
RE_YT = re.compile(r"^([^\s.]{2,14}) [YV\\]A\S{0,3}T[.,]?(?: HAD\S+)?(?: [\w$;^!.']{1,4}){0,3}$")
def est_majuscule(mot):
    lettres = [c for c in mot if c.isalpha()]
    return len(lettres) >= 2 and sum(c.isupper() for c in lettres) >= len(lettres) / 2
def nom_yasht(brut):
    n = re.sub(r"[^A-Za-z]", "", brut).upper()
    if n in NOMS: return n
    pr = difflib.get_close_matches(n, NOMS, n=1, cutoff=0.6)
    return pr[0] if pr else None
def yashts():
    L = lire("avesta_yashts.txt")
    hits, inconnus = [], []
    for i, l in enumerate(L):
        m = RE_YT.match(l)
        if m and est_majuscule(m.group(1)) and "SIROZAH" not in l.upper():
            n = nom_yasht(m.group(1))
            if n: hits.append((i, NOMS.index(n)))
            else: inconnus.append(l)
    secs = decouper(L, hits, lambda l: bool(RE_YT.match(l)) or "AND SIROZAHS" in l.upper(), True)
    if inconnus: print("  en-tetes Yasht non reconnues :", inconnus[:10])
    return [{"yasht_numero": s["label"] + 1, "yasht_nom": NOMS[s["label"]], **{k: s[k] for k in ("ligne_debut", "ligne_fin", "text")}} for s in secs]

# ---------- Yasna : en-tetes courantes "YASNA XXIX." (ordre : Gathas d'abord, donc non monotone)
RE_YS = re.compile(r"^YASNA ([IVXL]+)\s*[.,]?(?: [\w$;^!.']{1,4}){0,3}$")
def yasna():
    L = lire("avesta_yasna.txt")
    hits = [(i, romain(m.group(1))) for i, l in enumerate(L) if (m := RE_YS.match(l))]
    secs = decouper(L, hits, lambda l: bool(RE_YS.match(l)) or l.startswith("THE YASNA,"), False)
    return [{"yasna_entete_courante": s["label"], **{k: s[k] for k in ("ligne_debut", "ligne_fin", "text")}} for s in secs]

if __name__ == "__main__":
    v, y, s = vendidad(), yashts(), yasna()
    print("Vendidad : %d sections -> fargards %s" % (len(v), [x["fargard"] for x in v]))
    print("Yashts   : %d sections -> %s" % (len(y), [x["yasht_nom"] for x in y]))
    print("Yasna    : %d blocs -> en-tetes %s" % (len(s), [x["yasna_entete_courante"] for x in s]))
    for nom, liste in (("Vendidad", v), ("Yashts", y), ("Yasna", s)):
        print(nom, "- longueurs (caracteres) :", [len(x["text"]) for x in liste])
    data = {
        "book": "Avesta (extraits : Vendidad, Yashts, Yasna) - Sacred Books of the East",
        "license": "Traductions du 19e siecle (Darmesteter 1880/1883, Mills 1887), domaine public.",
        "translators": {"vendidad": "James Darmesteter (SBE vol. 4, a verifier)",
                        "yashts": "James Darmesteter (SBE vol. 23, a verifier)",
                        "yasna": "L. H. Mills (SBE vol. 31, a verifier)"},
        "note": ("Texte issu d'une reconnaissance optique (OCR) de scans Internet Archive. "
                 "Decoupage deduit des en-tetes courantes de page : limites approximatives (a une page pres). "
                 "Yashts : le Vanant Yasht, tres court, n'a pas d'en-tete propre et reste fondu dans le bloc Zamyad. "
                 "Yasna : chaque bloc regroupe les pages placees sous une en-tete courante ; un chapitre court qui commence en milieu de page est donc fondu dans le bloc precedent (chapitres manquants possibles). "
                 "Les notes de bas de page et commentaires des traducteurs sont melanges au texte. "
                 "Le Visparad, l'Afrinagan, les Gahs et le reste du volume 31 ne sont pas inclus."),
        "vendidad": v, "yashts": y, "yasna": s,
    }
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Ecrit :", SORTIE)