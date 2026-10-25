# liste_upanishads.py - liste les sous-pages Upanishads sur Wikisource (SBE vol. 1 et 15). Lecture seule, API officielle.
import requests, time, json

API = "https://en.wikisource.org/w/api.php"
HEADERS = {"User-Agent": "SacredTextsPersonalProject/1.0 (etude privee; python-requests)"}
sortie = {}
for prefixe in ("Sacred Books of the East/Volume 1/", "Sacred Books of the East/Volume 15/"):
    titres, suite = [], {}
    while True:
        for essai in range(6):
            r = requests.get(API, params={"action": "query", "list": "allpages", "apprefix": prefixe,
                                          "aplimit": 500, "format": "json", **suite},
                             headers=HEADERS, timeout=30)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", "60")) + 5); continue
            r.raise_for_status(); break
        d = r.json()
        titres += [p["title"] for p in d["query"]["allpages"]]
        if "continue" in d:
            suite = d["continue"]; time.sleep(8)
        else:
            break
    sortie[prefixe] = titres
    print(prefixe, ":", len(titres), "pages")
    time.sleep(8)
json.dump(sortie, open("liste_upanishads.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Ecrit : liste_upanishads.json")