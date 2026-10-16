"""Étape 5 — Assemble la page de règles autonome (un seul fichier HTML).

Injecte dans site/src/regles.html : les fonctions de site/js/geo.js et site/js/treemap.js
(mot-clé `export` retiré), les profils de data/derived/profils_2024.json et la distance maximale.
Sortie : site/dist/regles.html
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = (ROOT / "site/src/regles.html").read_text(encoding="utf-8")
strip = lambda p: re.sub(r"^export ", "", (ROOT / p).read_text(encoding="utf-8"), flags=re.M)
profiles = json.loads((ROOT / "data/derived/profils_2024.json").read_text(encoding="utf-8"))
meta = json.loads((ROOT / "data/derived/metadata.json").read_text(encoding="utf-8"))
dmax = json.loads((ROOT / "data/derived/distance_max_m.json").read_text())["distance_max_m"]

upd = meta["sources"]["depenses"]["derniere_mise_a_jour_eurostat"][0]  # "16/09/26 23:00:00"
d, m, y = upd.split()[0].split("/")
extr = meta["fichiers_bruts"]["gov_10a_exp.csv"]["retrieved_utc"][:10]
page_meta = {"update": f"{d}/{m}/20{y}", "extraction": "/".join(reversed(extr.split("-")))}

out = (src.replace("/*__GEO__*/", strip("site/js/geo.js"))
          .replace("/*__TREEMAP__*/", strip("site/js/treemap.js"))
          .replace("/*__DATA__*/", json.dumps(profiles, ensure_ascii=False, separators=(",", ":")))
          .replace("/*__DMAX__*/", str(dmax))
          .replace("/*__META__*/", json.dumps(page_meta)))
assert "/*__" not in out
(ROOT / "site/dist").mkdir(parents=True, exist_ok=True)
(ROOT / "site/dist/regles.html").write_text(out, encoding="utf-8")
print(f"site/dist/regles.html : {len(out):,} octets ; {page_meta}")
