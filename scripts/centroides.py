"""Lecture des centres géographiques des pays dans le fichier de Tradle (data/raw/tradle_countries.ts).

Le fichier contient deux listes : les vrais pays (`countries`), puis des planètes fictives utilisées pour le
poisson d'avril de Tradle (`fictionalCountries`), dont certaines réutilisent des codes de pays réels (AL, AD, AE…).
Seule la première liste est lue ; un code en double ou un nom qui ne correspond pas au pays fait échouer le script.
"""
import pathlib
import re
import unicodedata

import pycountry

PATTERN = re.compile(r'code:\s*"(\w\w)",\s*latitude:\s*(-?[\d.]+),\s*longitude:\s*(-?[\d.]+),\s*name:\s*"([^"]+)"')
NAME_OK = {"XK": "Kosovo", "MD": "Moldova", "KR": "South Korea", "CZ": "Czech Republic", "MK": "Macedonia [FYROM]", "TR": "Turkey"}


def _norm(s):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower())


def load(path: pathlib.Path) -> dict:
    ts = path.read_text(encoding="utf-8")
    real = ts.split("export const fictionalCountries")[0]
    found = PATTERN.findall(real)
    codes = [c for c, *_ in found]
    dup = sorted({c for c in codes if codes.count(c) > 1})
    if dup:
        raise SystemExit(f"Centroïdes : codes en double dans la liste des pays réels : {dup}")
    out = {}
    for c, lat, lon, name in found:
        out[c] = (float(lat), float(lon), name)
    return out


def check_name(iso2: str, tradle_name: str) -> bool:
    """Le nom anglais de Tradle doit correspondre au pays ISO (nom, nom usuel ou officiel)."""
    if NAME_OK.get(iso2) == tradle_name:
        return True
    c = pycountry.countries.get(alpha_2=iso2)
    if not c:
        return False
    names = {_norm(getattr(c, a)) for a in ("name", "common_name", "official_name") if hasattr(c, a)}
    t = _norm(tradle_name)
    return any(t == n or t in n or n in t for n in names)
