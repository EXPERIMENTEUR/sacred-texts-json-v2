# -*- coding: utf-8 -*-
"""Construit baruch_complete.json a partir du fichier local OCR (Charles 1913, vol. 2).
2 Baruch (syriaque, ch. 1-87) et 3 Baruch (grec, prologue + ch. 1-17).
Le commentaire de Charles est exclu par heuristique ; ce qui est ecarte va dans baruch_sources/commentaire_exclu_*.txt"""
import json, re, sys

SRC = "baruch_sources/charles1913_vol2.txt"
OUT = "baruch_complete.json"
lines = open(SRC, encoding="utf-8", errors="replace").read().splitlines()

def trouver(motif, debut=0, fin=None):
    rx = re.compile(motif)
    for i in range(debut, fin if fin else len(lines)):
        if rx.search(lines[i]):
            return i
    return None

RE_ENTETE = re.compile(r"^\W{0,3}\w{0,3}\s?BARUCH\b(?:.*\d|.{0,30}$)")
RE_BRUIT = re.compile(r"^(?:[A-Za-z]{0,2}[\d\W_]+)+$")
RE_PAGE = re.compile(r"^\d{3}$")
def suite(ls, l):
    """Vrai si la ligne l prolonge une phrase restee ouverte (et n'est pas un lemme de note)."""
    if re.match(r"^.{1,50}?\.\s+(?:[A-Z\u2018(]|cf\b)", l):
        return False
    return bool(ls) and l[:1].islower() and not re.search(r"[.;:?!)\]\u2019\u201d\"']\s*$", ls[-1])
LASTP = [0]
def page_ok(l):
    """Vrai pour un vrai numero de page (480-700, croissant) : le texte de la page suivante commence apres lui."""
    if RE_PAGE.match(l) and 480 <= int(l) <= 700 and int(l) >= LASTP[0]:
        LASTP[0] = int(l)
        return True
    return False
RE_REF = re.compile(r"^\d{1,2}\s?(?:Ezra|Barav|Bar\b|Baruch|En\b|Enoch|Macc|Mac\b|Kings|Kgs|Sam|Chron|Thess|Cor|Pet|John|Tim|Jub|Sib|Pss|Apoc|Test|Esd)")
RE_VERSE = re.compile(r"^(\d{1,2})(?:\s?,\s?(\d{1,2}))?\s?(?=[A-Za-z\u2018\u2019\u201c\"'(])")
RE_TITRE = re.compile(r"^[IVXLC]{1,8}(?:\s?[\u2014\u2013\-]\s?[IVXLC]{1,8})?\.?\s?\d{0,2}[-\u2014\u2013.]*\d{0,2}\.?\s+[A-Z]")
RE_SOUSTITRE = re.compile(r"^[A-Z][a-z]+(?: [A-Za-z]+){0,4}\.$")

def est_titre(l):
    if len(l) > 110 or not l.rstrip().endswith("."):
        return False
    m = RE_TITRE.match(l)
    if not m:
        return False
    titre = l[m.end()-1:].strip()
    if ". " in titre[:-1] or len(titre) < 15:
        return False
    return not re.search(r"\b(?:chapter|verse|verses|Cf|See|note|MS|Syriac|text|reads)\b", titre)

def verset(l):
    if RE_REF.match(l):
        return None
    m = RE_VERSE.match(l)
    if not m:
        return None
    return int(m.group(2) or m.group(1))

def chaine(cands):
    """cands : liste (ligne, n). Plus longue suite strictement croissante en ligne ET en n."""
    best = [1] * len(cands); prev = [-1] * len(cands)
    for a in range(len(cands)):
        for b in range(a):
            if cands[b][0] < cands[a][0] and cands[b][1] < cands[a][1] and best[b] + 1 > best[a]:
                best[a] = best[b] + 1; prev[a] = b
    if not cands:
        return []
    k = max(range(len(cands)), key=lambda x: best[x]); out = []
    while k != -1:
        out.append(cands[k]); k = prev[k]
    return out[::-1]

def decouper(region, debuts, note_re, blocs, depart=None):
    """debuts : {index_ligne: (label, verset_initial)}"""
    chap, exclu = {}, []
    cur, mode, last_v, blancs = depart, "texte", 0, 0
    fresh2 = 0
    if depart is not None:
        chap[depart] = []
    for i, brut in enumerate(region):
        l = brut.strip()
        if not l:
            blancs += 1; continue
        run, blancs = blancs, 0
        if RE_ENTETE.match(l):
            blancs = run; mode = "texte"; fresh2 = 2; exclu.append(l); continue
        if RE_PAGE.match(l) or len(l) <= 2 or (len(l) <= 8 and RE_BRUIT.match(l)):
            if page_ok(l):
                mode = "texte"; fresh2 = 2
            blancs = run; exclu.append(l); continue
        if i in debuts:
            cur, last_v = debuts[i][0], debuts[i][1]; mode = "texte"
            chap.setdefault(cur, [])
            if len(debuts[i]) < 3 or debuts[i][2]:
                chap[cur].append(l)
            continue
        if cur is None:
            continue
        v = verset(l)
        if est_titre(l):
            mode = "texte"; exclu.append("[TITRE] " + l); continue
        if mode == "texte":
            if fresh2 <= 0 and note_re.match(l):
                mode = "notes"; exclu.append(l); continue
            if blocs and cur != "Prologue" and run >= 2 and fresh2 <= 0 and not (v and last_v < v <= last_v + 2) and not suite(chap[cur], l):
                if RE_SOUSTITRE.match(l) and len(l) <= 40:
                    exclu.append("[SOUS-TITRE] " + l); continue
                mode = "notes"; exclu.append(l); continue
            if v:
                last_v = v
            fresh2 -= 1
            chap[cur].append(l)
        else:
            if v and last_v < v <= last_v + 2:
                mode = "texte"; last_v = v; chap[cur].append(l)
            else:
                exclu.append(l)
    return chap, exclu

def joindre(ls):
    t = ""
    for x in ls:
        t = (t[:-1] + x) if (t.endswith("-") and x[:1].islower()) else (t + " " + x).strip()
    return re.sub(r"\s+", " ", t)

def rapport(nom, chap, attendus, exclu, fichier):
    manq = [n for n in attendus if n not in chap]
    courts = [(n, len(joindre(chap[n]))) for n in sorted(chap, key=str) if len(joindre(chap[n])) < 150]
    print(f"\n== {nom} ==")
    print(f"Chapitres trouves : {len([n for n in chap if n != 'Prologue'])} / {len(attendus)}")
    print("Manquants :", manq if manq else "aucun")
    print("Tres courts (<150 car.) :", courts if courts else "aucun")
    open(fichier, "w", encoding="utf-8").write("\n".join(exclu))
    print(f"Ecartes : {len(exclu)} lignes -> {fichier}")

# ---------------- 2 BARUCH ----------------
d = trouver(r"^THE BOOK OF THE APOCALYPSE OF BARUCH THE", 40000)
f = trouver(r"HERE ENDS THE BOOK OF BARUCH", d) if d is not None else None
if d is None or f is None:
    sys.exit("Bornes de 2 Baruch introuvables.")
print(f"2 Baruch : lignes {d+1} a {f+1}")
reg2 = lines[d:f]
RE_CH2 = re.compile(r"^(\d{1,2}) ?[:;](\d{1,2})?(?=\s|$)")
c2 = []
for i, l in enumerate(reg2):
    m = RE_CH2.match(l.strip())
    if m and 1 <= int(m.group(1)) <= 87:
        c2.append((i, int(m.group(1)), int(m.group(2) or 1)))
ch2 = chaine([(i, n) for i, n, _ in c2])
RE_I_SEUL = re.compile(r"^I\.\s")
anc = []   # (ligne, label, verset_initial, garder_la_ligne)
for i, n in ch2:
    v = next(v for j, nn, v in c2 if j == i and nn == n)
    reg2[i] = RE_CH2.sub("", reg2[i].strip(), count=1).strip() or "."
    anc.append([i, "ch. %d" % n, v, True])
for i, l in enumerate(reg2):
    s2 = l.strip()
    if est_titre(s2) and not RE_I_SEUL.match(s2) and not RE_ENTETE.match(s2):
        anc.append([i, s2, 1, False])
anc.sort(key=lambda a: (a[0], a[3]))
fus = []
for a_ in anc:
    # un titre suivi de pres d'un marqueur de chapitre : une seule ancre
    if fus and fus[-1][3] is False and a_[3] is True and "[ch." not in fus[-1][1] and 0 < a_[0] - fus[-1][0] <= 6:
        fus[-1] = [fus[-1][0], fus[-1][1] + " [" + a_[1] + "]", a_[2], False]
        continue
    if fus and fus[-1][0] == a_[0]:
        continue
    fus.append(a_)
deb2, vus = {}, set()
for i, lab, v, garder in fus:
    k = lab; t = 2
    while k in vus:
        k = "%s (%d)" % (lab, t); t += 1
    vus.add(k); deb2[i] = (k, v, garder)
note2 = re.compile(r"^(?:THE [A-Z]+ SECTION\b|[IVXLC]{1,8}\.\s?\d{1,2}\b|\d{1,2}\.\s?(?:[a-z]|[A-Z][^.]{0,70}\.(?:\s|$)))")
chap2, ex2 = decouper(reg2, deb2, note2, blocs=False)
print("\n== 2 Baruch (blocs ancres sur marqueurs de chapitre et titres de sections) ==")
print("Blocs :", len(chap2), "| marqueurs de chapitre retenus :", len(ch2))
for k_, t_ in chap2.items():
    n_ = len(joindre(t_))
    print("  %-90s %6d car.%s" % (k_[:90], n_, "  <-- COURT" if n_ < 150 else ""))
open("baruch_sources/commentaire_exclu_2baruch.txt", "w", encoding="utf-8").write("\n".join(ex2))
print("Ecartes : %d lignes -> baruch_sources/commentaire_exclu_2baruch.txt" % len(ex2))

# ---------------- 3 BARUCH ----------------
note3 = re.compile(r"^(?:PROLOGUE\.|[IVXLC]{1,8}\.\s?\d{1,2}\b|\d{1,2}\.\s?[A-Za-z])")
p0 = None
for i in range(f, len(lines)):
    if re.match(r"^Prologue\.?\s*$", lines[i].strip()) and re.search(r"revelation|narrative", " ".join(lines[i+1:i+12]), re.I):
        p0 = i; break
if p0 is None:
    sys.exit("Debut de 3 Baruch (Prologue) introuvable.")
e3 = trouver(r"^\s*1 Esdras = ", p0) or trouver(r"THE RELATION OF 4 EZRA TO 2 BARUCH", p0) or (p0 + 2500)
print(f"\n3 Baruch : lignes {p0+1} a {e3}")
reg3 = lines[p0 + 1:e3]
_h = [i for i, l in enumerate(reg3) if re.match(r"^\W{0,3}\w{0,3}\s?BARUCH\b", l.strip()) and re.search(r"\d", l)]
if _h:
    _f = next((i for i in range(_h[-1], len(reg3)) if RE_PAGE.match(reg3[i].strip())), None)
    if _f is not None:
        reg3 = reg3[:_f + 1]
# --- chapitre 17 : l'OCR a disperse le texte final de la derniere page ; on le recompose
def prendre(motif, jusqua=None, maxl=6):
    rx = re.compile(motif)
    for i, l in enumerate(reg3):
        if rx.match(l.strip()):
            out, j = [], i
            while j < len(reg3) and len(out) < maxl:
                t = reg3[j].strip()
                if t:
                    out.append(t)
                    reg3[j] = ""
                    if jusqua is None or re.search(jusqua, t):
                        if jusqua is not None or len(out) >= 2:
                            break
                j += 1
            return out
    return []
frag_a = prendre(r"^And while he yet spake, the door was closed", jusqua=r"took me and\s*$", maxl=3)
frag_b = prendre(r"^3 restored me to the place where I was", maxl=2)
frag_c = prendre(r"^such a revelation, yourselves also glorify God", jusqua=r"Amen\.", maxl=3)
for i, l in enumerate(reg3):
    if re.match(r"^[A-Za-z]?\s?71\s?,\s?2$", l.strip()):
        reg3[i] = ""
ch17 = frag_a + frag_b + frag_c
print("Chapitre 17 recompose : %d + %d + %d lignes" % (len(frag_a), len(frag_b), len(frag_c)))
V3 = [verset(l.strip()) if l.strip() else None for l in reg3]
NB, c_ = [], 0
for l in reg3:
    c_ += 1 if l.strip() else 0
    NB.append(c_)

RE_CIEL = re.compile(r"^The (?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth)\s+Heaven\.?$")
MARQUEURS = [re.compile(r"^(\d{1,2})[\]\):]?\s?1(?:\s?,\s?\d{1,2})?,?\s+(?=[A-Z\u2018\u201c'\"])"),
             re.compile(r"^(\d{1,2}):(\d{1,2})?\s+"),
             re.compile(r"^(\d{1,2}),\s+(?=[A-Z])")]
cand3 = []
for i, l in enumerate(reg3):
    s = l.strip()
    for rx in MARQUEURS:
        m = rx.match(s)
        if m and 2 <= int(m.group(1)) <= 17:
            cand3.append((i, int(m.group(1)), m.end())); break
RE_MARQ0 = re.compile(r"^(?:\S{1,4}\s+)?1\s?,\s?2\s+(?=[A-Z])")
marq0 = {}
for i, l in enumerate(reg3):
    s0 = l.strip()
    m0 = RE_MARQ0.match(s0)
    if m0 and not any(i == c[0] for c in cand3):
        marq0[i] = m0.end()
i1 = next((i for i, l in enumerate(reg3[:80]) if re.match(r"^[1lI]\s+Verily", l.strip())), None)
if i1 is not None:
    cand3.insert(0, (i1, 1, 1))
cm3 = chaine([(i, n) for i, n, _ in cand3])
marq = {i: (n, next(e for j, nn, e in cand3 if j == i and nn == n)) for i, n in cm3}
anc3 = sorted([(i, "marq") for i in marq] + [(i, "marq0") for i in marq0] + [(i, "ciel") for i, l in enumerate(reg3) if RE_CIEL.match(l.strip())])
groupes, dernier = [], None
for i, k in anc3:
    if dernier is not None and NB[i] - NB[dernier] <= 2 and not (k != "ciel" and groupes[-1][-1][1] != "ciel"):
        groupes[-1].append((i, k))
    else:
        groupes.append([(i, k)])
    dernier = i
debut3 = {}   # ligne -> (est_debut_de_chapitre, N_explicite_ou_None)
for g in groupes:
    nn = next((marq[i][0] for i, k in g if k == "marq"), None)
    for j, (i, k) in enumerate(g):
        debut3[i] = (j == 0, nn, k)

def suite_ok(i, v):
    vus = 0
    for j in range(i + 1, min(i + 160, len(reg3))):
        if V3[j] is not None:
            if v < V3[j] <= v + 8:
                return True
            vus += 1
            if vus >= 6:
                break
    return False

chap3, ex3 = {"Prologue": []}, []
cur, mode, last_v, blancs, n_cur, dern_deb = "Prologue", "texte", 0, 0, 0, -1
fresh = 0
alertes = []
def nouveau(i, n_explicite):
    global cur, n_cur, last_v, mode, dern_deb
    cible = n_explicite if n_explicite else n_cur + 1
    if cible <= n_cur:
        cible = n_cur
        if n_explicite and n_explicite < n_cur:
            alertes.append("ligne %d : marqueur %s ignore (deja au chapitre %d)" % (p0 + 2 + i, n_explicite, n_cur))
    elif n_explicite and n_explicite != n_cur + 1:
        alertes.append("ligne %d : saut de chapitre %d -> %d" % (p0 + 2 + i, n_cur, n_explicite))
    n_cur = min(cible, 17)
    cur = n_cur; chap3.setdefault(cur, [])
    last_v, mode, dern_deb = 0, "texte", i

for i, brut in enumerate(reg3):
    l = brut.strip()
    if not l:
        blancs += 1; continue
    run, blancs = blancs, 0
    if RE_ENTETE.match(l):
        blancs = run; mode = "texte"; fresh = 2; ex3.append(l); continue
    if RE_PAGE.match(l) or len(l) <= 2 or (len(l) <= 8 and RE_BRUIT.match(l)):
        if page_ok(l):
            mode = "texte"; fresh = 2
        blancs = run; ex3.append(l); continue
    if i in debut3:
        est_debut, nn, kind = debut3[i]
        if est_debut:
            nouveau(i, nn if kind != "marq0" else None)
            fresh = 3
        if i in marq:
            reste = l[marq[i][1]:].strip() if not (marq[i][0] == 1 and marq[i][1] == 1) else l[1:].strip()
            if reste:
                chap3[cur].append(reste)
            last_v = 1
        elif i in marq0:
            reste = l[marq0[i]:].strip()
            if reste:
                chap3[cur].append(reste)
            last_v = 2
        else:
            ex3.append("[CIEL] " + l)
        continue
    v = V3[i]
    if est_titre(l):
        mode = "texte"; ex3.append("[TITRE] " + l); continue
    reset = bool(v) and v <= 2 and v < last_v and last_v >= 3 and (dern_deb < 0 or NB[i] - NB[dern_deb] > 1) and suite_ok(i, v) and cur != "Prologue" and n_cur < 17
    if mode == "texte":
        if note3.match(l):
            mode = "notes"; ex3.append(l); continue
        if cur != "Prologue" and run >= 2 and fresh <= 0 and not (reset or (v and last_v < v <= last_v + 2)) and not suite(chap3[cur], l):
            if RE_SOUSTITRE.match(l) and len(l) <= 40:
                ex3.append("[SOUS-TITRE] " + l); continue
            mode = "notes"; ex3.append(l); continue
    else:
        if not (reset or (v and last_v < v <= last_v + 2)):
            ex3.append(l); continue
        mode = "texte"
    if reset:
        nouveau(i, None)
    if v:
        last_v = v
    fresh -= 1
    chap3[cur].append(l)

if ch17:
    chap3[17] = ch17
else:
    print("  ALERTE : fragments du chapitre 17 introuvables")

print("\n== 3 Baruch ==")
manq3 = [n for n in range(1, 18) if n not in chap3]
print("Chapitres trouves : %d / 17" % len([k for k in chap3 if k != "Prologue"]), "| manquants :", manq3 if manq3 else "aucun")
for a_ in alertes:
    print("  ALERTE", a_)
for k_ in chap3:
    t_ = joindre(chap3[k_])
    print("  %-9s %5d car. | %s" % (k_, len(t_), t_[:70]))
open("baruch_sources/commentaire_exclu_3baruch.txt", "w", encoding="utf-8").write("\n".join(ex3))
print("Ecartes : %d lignes -> baruch_sources/commentaire_exclu_3baruch.txt" % len(ex3))

def net(n):
    if not isinstance(n, str):
        return n
    for a, b in (("Ferusalem", "Jerusalem"), ("Fudgement", "Judgement"), ("PRAVER", "PRAYER")):
        n = n.replace(a, b)
    return n

def livre(titre, source, chap, ordre=False):
    cles = list(chap) if ordre else sorted(chap, key=lambda x: (0, 0) if x == "Prologue" else (1, x))
    return {"title": titre, "source": source,
            "chapters": [{"chapter": net(n), "text": joindre(chap[n])} for n in cles]}

data = {
    "book": "Apocalypse de Baruch (2 Baruch syriaque et 3 Baruch grec)",
    "translator": "2 Baruch : R. H. Charles ; 3 Baruch : H. M. Hughes, dans R. H. Charles (ed.), The Apocrypha and Pseudepigrapha of the Old Testament, vol. 2, Oxford, 1913",
    "license": "Domaine public (traductions de 1913)",
    "note": ("Texte issu d'un OCR : erreurs possibles. Le 2 Baruch syriaque est une traduction d'un original grec perdu. "
             "Le commentaire, les notes et les en-tetes de page des editeurs ont ete exclus par heuristique : des fragments peuvent "
             "subsister dans certains chapitres, et des fragments du texte ont pu etre ecartes a tort. Les numeros de versets "
             "sont conserves tels quels dans le texte. Dans le 2 Baruch, l'OCR a perdu la plupart des numeros de chapitre : le texte est donc decoupe en blocs ancres sur les marqueurs de chapitre et les titres de sections de Charles qui ont survecu (etiquette = ce qui est imprime), et non en 87 chapitres ; un bloc peut regrouper plusieurs chapitres. Dans le 3 Baruch, le prologue est une entree a part ; le premier verset d'un chapitre est parfois rattache a la fin du chapitre precedent (OCR) ; le chapitre 17 a ete recompose a partir de fragments disperses par l'OCR sur la derniere page. Une quinzaine de phrases de commentaire subsistent dans le texte du 2 Baruch, et la colonne grecque parallele (papyrus d'Oxyrhynque) peut avoir laisse des fragments."),
    "livres": [livre("2 Baruch (Apocalypse syriaque)", "syriaque", chap2, ordre=True),
               livre("3 Baruch (Apocalypse grecque)", "grec", chap3)],
}
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nEcrit :", OUT)