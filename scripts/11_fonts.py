"""Hébergement local des polices (plus aucune requête vers Google depuis le site public).

Pourquoi : chaque chargement de Google Fonts transmet l'adresse IP du visiteur à Google ; un tribunal
de Munich (LG München, 20/01/2022) y a vu une violation du RGPD. Héberger les fichiers évite ce transfert
et permet une politique de sécurité de contenu (CSP) qui n'autorise que le site lui-même.

Télécharge, pour les sous-ensembles « latin » et « latin-ext » seulement, les fichiers WOFF2 des trois
familles (licence SIL Open Font License 1.1, redistribution autorisée), les enregistre dans site/fonts/
et écrit site/css/fonts.css (chemins relatifs) ; site/fonts/SOURCES.json garde URL et empreinte SHA-256.
"""
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "site" / "fonts"
FONTS.mkdir(parents=True, exist_ok=True)
CSS_URL = ("https://fonts.googleapis.com/css2?family=Young+Serif&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400"
           "&family=IBM+Plex+Mono:wght@400;500&display=swap")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
KEEP = {"latin", "latin-ext"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


css = get(CSS_URL).decode()
blocks = re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S)
out, sources = [], []
for subset, block in blocks:
    if subset not in KEEP:
        continue
    url = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", block).group(1)
    fam = re.search(r"font-family: '([^']+)'", block).group(1)
    style = re.search(r"font-style: (\w+)", block).group(1)
    weight = re.search(r"font-weight: (\d+)", block).group(1)
    name = f"{fam.replace(' ', '')}-{weight}{'i' if style == 'italic' else ''}-{subset}.woff2"
    body = get(url)
    (FONTS / name).write_bytes(body)
    sources.append({"fichier": name, "url": url, "sha256": hashlib.sha256(body).hexdigest(), "licence": "SIL OFL 1.1"})
    out.append(f"/* {fam} {weight} {style} — {subset} */\n" + block.replace(url, f"fonts/{name}"))
(ROOT / "site/css/fonts.css").write_text("\n".join(out) + "\n", encoding="utf-8")
(FONTS / "SOURCES.json").write_text(json.dumps(sources, indent=1), encoding="utf-8")
print(f"{len(sources)} fichiers de police, {sum((FONTS / s['fichier']).stat().st_size for s in sources):,} octets")
