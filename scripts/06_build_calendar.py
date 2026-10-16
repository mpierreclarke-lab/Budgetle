"""Calendrier des pays du jour (comme Tradle : une liste fixée à l'avance, pas de tirage pendant la partie).

Règles :
  - cycles de N jours (N = nombre de pays) ; chaque pays apparaît exactement une fois par cycle ;
  - ordre de chaque cycle mélangé avec une graine fixe (reproductible) ;
  - un même pays ne revient jamais à moins de 35 jours d'intervalle, y compris d'un cycle à l'autre.
La liste explicite est enregistrée : le jeu ne dépend pas du générateur aléatoire.
Sortie : data/derived/calendrier.json
"""
import datetime as dt
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
START = dt.date(2026, 10, 16)  # partie n° 1
CYCLES = 6                     # 6 × 70 = 420 jours
MIN_GAP = 35
SEED = 20261016

geos = [p["geo"] for p in json.loads((ROOT / "data/derived/profils_monde.json").read_text(encoding="utf-8"))]
N = len(geos)
rng = random.Random(SEED)
days: list[str] = []
for _ in range(CYCLES):
    while True:
        order = geos[:]
        rng.shuffle(order)
        recent = days[-MIN_GAP:]
        # écart entre la dernière apparition (fin du cycle précédent) et la nouvelle
        if all(g not in recent or (len(recent) - recent.index(g)) + i >= MIN_GAP for i, g in enumerate(order)):
            break
    days += order

# Contrôles
for i, g in enumerate(days):
    prev = [j for j in range(max(0, i - MIN_GAP + 1), i) if days[j] == g]
    assert not prev, f"{g} revient trop tôt (jour {i + 1})"
for c in range(CYCLES):
    assert sorted(days[N * c:N * c + N]) == sorted(geos)

out = {"debut": START.isoformat(), "regle": __doc__.strip(), "graine": SEED, "pays": days}
(ROOT / "data/derived/calendrier.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
end = START + dt.timedelta(days=len(days) - 1)
print(f"{len(days)} jours, du {START} au {end} ; 10 premiers : {days[:10]}")
