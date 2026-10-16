"""Assemble les pages autonomes du site (un fichier HTML par page, sans dépendance).

Pour chaque page de site/src/, remplace les marqueurs par :
  CSS      site/css/base.css               GEO / TREEMAP / GAME  site/js/*.js (import/export retirés)
  UI       site/js/ui.js                   DATA  data/derived/profils_monde.json
  DMAX     20 000 km (échelle de Tradle)           CAL   data/derived/calendrier.json
  META     dates de mise à jour Eurostat et d'extraction
Sorties :
  site/dist/<page>.html          document HTML complet (doctype, langue, encodage) pour GitHub Pages
  site/dist-artifact/<page>.html même contenu sans squelette, pour un Artifact claude.ai (qui ajoute le sien)
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
read = lambda p: (ROOT / p).read_text(encoding="utf-8")


def js_module(p):
    s = re.sub(r"^import .*?;\n", "", read(p), flags=re.M)
    return re.sub(r"^export ", "", s, flags=re.M)


meta = json.loads(read("data/derived/metadata.json"))
upd = meta["sources"]["depenses"]["derniere_mise_a_jour_eurostat"][0]  # "16/09/26 23:00:00"
d, m, y = upd.split()[0].split("/")
extr = meta["fichiers_bruts"]["gov_10a_exp.csv"]["retrieved_utc"][:10]
cal = json.loads(read("data/derived/calendrier.json"))

MARKERS = {
    "/*__CSS__*/": read("site/css/base.css"),
    "/*__GEO__*/": js_module("site/js/geo.js"),
    "/*__TREEMAP__*/": js_module("site/js/treemap.js"),
    "/*__GAME__*/": js_module("site/js/game.js"),
    "/*__UI__*/": read("site/js/ui.js"),
    "/*__DATA__*/": json.dumps(json.loads(read("data/derived/profils_monde.json")), ensure_ascii=False, separators=(",", ":")),
    "/*__DMAX__*/": "20000000",  # échelle mondiale de Tradle : 20 000 km
    "/*__CAL__*/": json.dumps({"debut": cal["debut"], "pays": cal["pays"]}, separators=(",", ":")),
    "/*__META__*/": json.dumps({"update": f"{d}/{m}/20{y}", "extraction": "/".join(reversed(extr.split("-")))}),
}

HEAD = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')

for d_ in ("site/dist", "site/dist-artifact"):
    (ROOT / d_).mkdir(parents=True, exist_ok=True)
for src in sorted((ROOT / "site/src").glob("*.html")):
    out = src.read_text(encoding="utf-8")
    for k, v in MARKERS.items():
        out = out.replace(k, v)
    assert "/*__" not in out, f"marqueur non remplacé dans {src.name}"
    (ROOT / "site/dist-artifact" / src.name).write_text(out, encoding="utf-8")
    # Pour le site : le contenu « tête » (title, meta, link, style) va dans <head>, le reste dans <body>
    i = out.index("</style>") + len("</style>")
    full = HEAD + out[:i] + "\n</head>\n<body>\n" + out[i:] + "\n</body>\n</html>\n"
    (ROOT / "site/dist" / src.name).write_text(full, encoding="utf-8")
    print(f"{src.name} : {len(full):,} octets (site) / {len(out):,} (artifact)")
