"""Profils budgétaires « monde » : les 30 pays Eurostat + les pays FMI et OCDE comparables.

Entrées : data/derived/profils_2024.json (Eurostat, inchangé) et data/raw/intl/*.csv (script 09).
Sorties : data/derived/profils_monde.json, profils_monde.csv, taux_de_change.csv,
          controles_monde.txt (rapport des contrôles, l'exécution échoue s'il y a une erreur).

Règles de sélection (décidées en séance 2) :
  S1  Périmètre : administrations publiques dans leur ensemble (S13) uniquement. Les pays pour lesquels
      seul l'État central est disponible sont exclus.
  S2  Les 10 fonctions COFOG doivent toutes être publiées pour l'année retenue, ainsi que le total.
  S3  Année : la plus récente disponible, au plus tôt 2022. Pays européens : Eurostat 2024 (inchangé).
  S4  Priorité des sources à année égale : Eurostat > OCDE > FMI ; sinon, l'année la plus récente.
  S5  Comptes en caisse acceptés (signalés) ; territoires non souverains exclus (Hong Kong, Macao).
  S6  Pays exclus si la somme des fonctions s'écarte du total publié de plus de 0,5 %.
Transformations :
  T1  % du PIB : valeur publiée (FMI), ou dépense / PIB de la même source et de la même année (OCDE),
      arrondie à 0,1 point comme Eurostat.
  T2  Euros : montant en monnaie nationale ÷ (monnaie nationale pour 1 euro, moyenne de l'année des
      données, FMI « Exchange Rates » PA_RT). Contrôle croisé avec la BCE quand elle publie la devise.
  T3  Parts du total et détail de la protection sociale : comme pour Eurostat (regroupement 10.7-10.9).
      Détail absent si l'un des groupes n'est pas publié (le rectangle reste alors d'un seul tenant).
"""
import datetime as dt
import json
import math
import pathlib
import re

import pandas as pd
import pycountry
from babel import Locale
from babel.numbers import get_territory_currencies

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data/raw/intl", ROOT / "data/derived"
MIN_YEAR = 2022
EXCLUDED = {"HKG": "territoire (Hong Kong)", "MAC": "territoire (Macao)"}
ISO3_EXTRA = {"KOS": "XK"}
FR = Locale("fr").territories
NAMES_FIX = {"XK": "Kosovo", "US": "États-Unis", "GB": "Royaume-Uni", "KR": "Corée du Sud", "AE": "Émirats arabes unis",
             "CN": "Chine", "RU": "Russie", "MD": "Moldavie", "KG": "Kirghizistan", "DO": "République dominicaine"}

EU = json.loads((OUT / "profils_2024.json").read_text(encoding="utf-8"))
EU_ISO3 = {pycountry.countries.get(alpha_2=p["iso2"]).alpha_3 for p in EU}
DIV = {f"GF{i:02d}": lbl for i, lbl in zip(range(1, 11), [d["label"] for d in EU[0]["divisions"]])}
SOCIAL = [(k["code"], k["label"]) for k in EU[0]["divisions"][9]["detail"]]
IMF_SP = {"SP_SICK": ["GF101"], "SP_OLD": ["GF1020"], "SP_SURV": ["GF1030"], "SP_FAM": ["GF1040"], "SP_UNEMP": ["GF1050"],
          "SP_HOUS": ["GF1060"], "SP_OTHER": ["GF1070", "GF1080", "GF1090"]}
OECD_SP = {"SP_SICK": ["GF1001"], "SP_OLD": ["GF1002"], "SP_SURV": ["GF1003"], "SP_FAM": ["GF1004"], "SP_UNEMP": ["GF1005"],
           "SP_HOUS": ["GF1006"], "SP_OTHER": ["GF1007", "GF1008", "GF1009"]}

ts = (ROOT / "data/raw/tradle_countries.ts").read_text(encoding="utf-8")
COORDS = {m[0]: (float(m[1]), float(m[2])) for m in re.findall(r'code:\s*"(\w\w)",\s*latitude:\s*(-?[\d.]+),\s*longitude:\s*(-?[\d.]+)', ts)}
report, errors = [], []


def log(s):
    report.append(s)
    print(s)


def iso2(iso3):
    return ISO3_EXTRA.get(iso3) or pycountry.countries.get(alpha_3=iso3).alpha_2


# ---------- Taux de change : FMI (référence) et BCE (contrôle)
er = pd.read_csv(RAW / "imf_er.csv", dtype=str)
er = er[er.OBS_VALUE.notna()]
ER = {(r.COUNTRY, int(r.TIME_PERIOD)): float(r.OBS_VALUE) for r in er.itertuples()}
ecb = pd.read_csv(RAW / "ecb_exr.csv", dtype=str)
ECB = {(r.CURRENCY, int(r.TIME_PERIOD)): float(r.OBS_VALUE) for r in ecb.itertuples() if isinstance(r.OBS_VALUE, str)}


CURRENCY_FIX = {"XK": "EUR", "NA": "NAD"}  # Kosovo (euro de fait) ; Namibie (dollar namibien, à parité avec le rand)


def currency(i2, year):
    if i2 in CURRENCY_FIX:
        return CURRENCY_FIX[i2]
    cur = get_territory_currencies(i2, start_date=dt.date(year, 6, 30), end_date=dt.date(year, 6, 30))
    return cur[0] if cur else None


# ---------- Candidats FMI
def imf_table(name):
    d = pd.read_csv(RAW / name, dtype=str, usecols=["COUNTRY", "INDICATOR", "TIME_PERIOD", "OBS_VALUE", "BASES_OF_RECORDING_CASH_NON_CASH"])
    d = d[d.OBS_VALUE.notna()]
    d["v"] = d.OBS_VALUE.astype(float)
    d["code"] = d.INDICATOR.str.replace("_T", "", regex=False)
    d["year"] = d.TIME_PERIOD.astype(int)
    return d


pg, xd = imf_table("imf_cofog_pogdp.csv"), imf_table("imf_cofog_xdc.csv")
L1 = list(DIV)
cand = {}
for (c, y), g in xd.groupby(["COUNTRY", "year"]):
    if c in EU_ISO3 or y < MIN_YEAR:
        continue
    x = g.set_index("code").v
    p = pg[(pg.COUNTRY == c) & (pg.year == y)].set_index("code").v
    if all(k in x for k in L1) and "TOTOUT" in x and all(k in p for k in L1) and "TOTOUT" in p:
        base = g.BASES_OF_RECORDING_CASH_NON_CASH.dropna()
        cand.setdefault(c, []).append(("FMI", y, x, p, base.iloc[0] if len(base) else None))

# ---------- Candidats OCDE (en monnaie nationale ; % du PIB = dépense / PIB OCDE)
oc = pd.read_csv(RAW / "oecd_cofog.csv", dtype=str)
oc = oc[oc.OBS_VALUE.notna() & (oc.SECTOR == "S13") & (oc.TRANSACTION == "OTE")]
gdp = pd.read_csv(RAW / "oecd_gdp.csv", dtype=str)
GDP = {(r.REF_AREA, int(r.TIME_PERIOD)): float(r.OBS_VALUE) for r in gdp.itertuples() if isinstance(r.OBS_VALUE, str)}
for (c, y), g in oc.groupby(["REF_AREA", oc.TIME_PERIOD.astype(int)]):
    if y < MIN_YEAR or (c, y) not in GDP:
        continue
    x = g.set_index("EXPENDITURE").OBS_VALUE.astype(float) * 1e6  # UNIT_MULT 6
    x = x.rename({"_T": "TOTOUT"})
    if all(k in x for k in L1) and "TOTOUT" in x:
        p = x / (GDP[(c, y)] * 1e6) * 100
        cand.setdefault(c, []).append(("OCDE", y, x, p, "AC"))

# ---------- Choix d'une source et d'une année par pays (S3, S4)
PRIO = {"OCDE": 2, "FMI": 1}
profiles, excluded, ecb_checked = [], [], []
for c, opts in sorted(cand.items()):
    if c in EXCLUDED:
        excluded.append(f"{c} : {EXCLUDED[c]}")
        continue
    src, y, x, p, base = max(opts, key=lambda o: (o[1], PRIO[o[0]]))
    i2 = iso2(c)
    cur = currency(i2, y)
    rate = 1.0 if cur == "EUR" else ER.get((c, y))
    if rate is None:
        excluded.append(f"{c} : pas de taux de change {y}")
        continue
    # Contrôle croisé BCE
    if cur in {k[0] for k in ECB} and cur != "EUR":
        e = ECB.get((cur, y))
        if e is not None:
            ecb_checked.append((i2, cur, y, 100 * (rate / e - 1)))
        if e is not None and abs(rate / e - 1) > 0.01:
            errors.append(f"{c} {y} : taux FMI {rate:.4f} ≠ BCE {e:.4f} {cur}")
    sp_map = IMF_SP if src == "FMI" else OECD_SP
    tot_mio = x["TOTOUT"] / rate / 1e6
    divs = []
    s_l1 = sum(x[k] for k in L1)
    for k in L1:
        item = {"code": k, "label": DIV[k], "label_officiel": None, "pc_gdp": round(p[k], 1),
                "mio_eur": x[k] / rate / 1e6, "part_du_total": x[k] / s_l1}
        if k == "GF10":
            if all(m in x for v in sp_map.values() for m in v):
                det = []
                for code, lbl in SOCIAL:
                    mem = sp_map[code]
                    v = sum(x[m] for m in mem)
                    det.append({"code": code, "label": lbl, "cofog": mem, "mio_eur": v / rate / 1e6,
                                "pc_gdp_somme_publiee": round(sum(p[m] for m in mem if m in p), 1),
                                "composantes_manquantes": [], "part_du_total": v / s_l1})
                gap = (sum(d["mio_eur"] for d in det) - item["mio_eur"]) / item["mio_eur"]
                if abs(gap) > 0.005:
                    errors.append(f"{c} : détail protection sociale ≠ total ({100 * gap:+.2f} %)")
                item["detail"] = det
            else:
                item["detail"] = None
        divs.append(item)
    gap = (s_l1 - x["TOTOUT"]) / x["TOTOUT"]
    if abs(gap) > 0.005:  # règle S2 : les fonctions doivent couvrir tout le total
        excluded.append(f"{c} {y} : somme des fonctions ≠ total ({100 * gap:+.2f} %)")
        continue
    if i2 not in COORDS:
        errors.append(f"{c} : pas de centroïde")
        continue
    nom = NAMES_FIX.get(i2) or FR.get(i2)
    profiles.append({
        "geo": i2, "iso2": i2, "nom": nom, "annee": y, "lat": COORDS[i2][0], "lon": COORDS[i2][1],
        "total": {"pc_gdp": round(p["TOTOUT"], 1), "mio_eur": tot_mio},
        "population_milliers": None, "provisoire": False, "drapeaux": [],
        "source": src, "base_comptable": "caisse" if base == "CA" else "droits constatés",
        "devise": cur, "taux_eur": rate, "divisions": divs,
    })
    log(f"{i2} {nom:<28} {src:<4} {y}  {'caisse' if base == 'CA' else 'droits':<6} {cur} {rate:>12.4f}  "
        f"total {tot_mio / 1000:>9.1f} Md€  {p['TOTOUT']:.1f} % PIB  écart fonctions {100 * gap:+.3f} %"
        f"{'' if divs[9]['detail'] else '  (sans détail social)'}")

# ---------- Pays européens (Eurostat, inchangés) + contrôle de la méthode de conversion
for e in EU:
    e.update({"annee": 2024, "source": "Eurostat", "base_comptable": "droits constatés",
              "devise": currency(e["iso2"], 2024), "taux_eur": None})
# Contrôle 1 : la méthode de conversion reproduit les euros d'Eurostat à partir de sa propre monnaie nationale
# Contrôle 2 (information) : écart de niveau entre FMI et Eurostat pour un même pays et une même année
es = pd.read_csv(ROOT / "data/raw/gov_10a_exp.csv", dtype=str)
es = es[(es.TIME_PERIOD == "2024") & (es.cofog99 == "TOTAL") & (es.unit == "MIO_NAC")].set_index("geo").OBS_VALUE.astype(float)
conv, level = [], []
for e in EU:
    c3 = pycountry.countries.get(alpha_2=e["iso2"]).alpha_3
    # La Bulgarie a rejoint la zone euro en 2026 : sa série Eurostat « monnaie nationale » est désormais en euros fixes
    if e["devise"] == "EUR" or e["iso2"] == "BG" or (c3, 2024) not in ER:
        continue
    conv.append((e["iso2"], 100 * (es[e["geo"]] / ER[(c3, 2024)] / e["total"]["mio_eur"] - 1)))
    g = xd[(xd.COUNTRY == c3) & (xd.year == 2024) & (xd.code == "TOTOUT")]
    if len(g):
        level.append((e["iso2"], 100 * (g.v.iloc[0] / 1e6 / es[e["geo"]] - 1)))
for k, v in conv:
    if abs(v) > 0.5:
        errors.append(f"conversion {k} : écart {v:+.2f} % avec Eurostat")
log("\nContrôle de la conversion (monnaie nationale Eurostat ÷ taux FMI, comparé aux euros Eurostat, 2024) : "
    + ", ".join(f"{k} {v:+.2f} %" for k, v in conv))
log("Information — dépense totale FMI vs Eurostat en monnaie nationale, 2024 : " + ", ".join(f"{k} {v:+.2f} %" for k, v in level))

world = EU + profiles
OUT.joinpath("profils_monde.json").write_text(json.dumps(world, ensure_ascii=False, indent=1), encoding="utf-8")
rows = []
for p in world:
    rows.append({"geo": p["geo"], "pays": p["nom"], "source": p["source"], "annee": p["annee"], "base": p["base_comptable"],
                 "devise": p["devise"], "taux_eur": p["taux_eur"], "total_mio_eur": round(p["total"]["mio_eur"], 1),
                 "total_pc_pib": p["total"]["pc_gdp"],
                 **{d["code"]: round(100 * d["part_du_total"], 2) for d in p["divisions"]},
                 "detail_social": p["divisions"][9]["detail"] is not None})
pd.DataFrame(rows).to_csv(OUT / "profils_monde.csv", index=False)
pd.DataFrame([{"pays": p["geo"], "annee": p["annee"], "devise": p["devise"], "monnaie_pour_1_euro": p["taux_eur"],
               "source": "FMI Exchange Rates (ER), moyenne annuelle PA_RT" if p["taux_eur"] not in (None, 1.0) else "sans objet"}
              for p in profiles]).to_csv(OUT / "taux_de_change.csv", index=False)
log(f"\nPays retenus : {len(world)} ({len(EU)} Eurostat, {sum(p['source'] == 'OCDE' for p in profiles)} OCDE, "
    f"{sum(p['source'] == 'FMI' for p in profiles)} FMI) ; en caisse : {sum(p['base_comptable'] == 'caisse' for p in profiles)} ; "
    f"sans détail social : {sum(p['divisions'][9]['detail'] is None for p in profiles)}")
log("Exclus : " + "; ".join(excluded))
log(f"Taux FMI comparés à la BCE : {len(ecb_checked)} pays, écart max "
    f"{max(abs(v) for *_, v in ecb_checked):.2f} % (" + ", ".join(f"{a} {c} {v:+.2f} %" for a, c, _, v in ecb_checked) + ")")
log(f"\nErreurs : {len(errors)}" + "".join("\n  " + e for e in errors))
(OUT / "controles_monde.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
raise SystemExit(1 if errors else 0)
