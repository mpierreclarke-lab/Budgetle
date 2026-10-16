"""Étape 2 — Construction des profils budgétaires (table propre + métadonnées + contrôles).

Entrées : data/raw/gov_10a_exp.csv, data/raw/nama_10_pe.csv, data/raw/tradle_countries.ts
Sorties : data/derived/profils_2024.json (pour le jeu), profils_2024.csv (lecture humaine),
          metadata.json (traçabilité), controles_2024.txt (rapport des contrôles).

Règles appliquées (aucune autre transformation) :
  R1  Périmètre : secteur S13 (APU consolidées), opération TE (dépense totale), année 2024.
  R2  % du PIB : valeur publiée par Eurostat (arrondie à 0,1 point), jamais recalculée.
  R3  Montants : millions d'euros publiés (MIO_EUR) ; convertis en milliards pour l'affichage.
  R4  Surfaces du treemap : parts calculées à partir des MIO_EUR (plus précis que les % arrondis).
  R5  Valeur manquante (drapeau 'm' ou absence) : null, jamais 0, jamais imputée.
  R6  Détail protection sociale : regroupement des groupes COFOG 10.7, 10.8, 10.9 en
      « Exclusion sociale et autres » (somme simple ; null si toutes les composantes manquent).
"""
import json
import math
import pathlib
import re
import datetime as dt

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "derived"
OUT.mkdir(parents=True, exist_ok=True)
YEAR = 2024

COUNTRIES = {  # code Eurostat -> (nom français, code ISO 3166-1 alpha-2 pour les centroïdes)
    "AT": ("Autriche", "AT"), "BE": ("Belgique", "BE"), "BG": ("Bulgarie", "BG"),
    "CH": ("Suisse", "CH"), "CY": ("Chypre", "CY"), "CZ": ("Tchéquie", "CZ"),
    "DE": ("Allemagne", "DE"), "DK": ("Danemark", "DK"), "EE": ("Estonie", "EE"),
    "EL": ("Grèce", "GR"), "ES": ("Espagne", "ES"), "FI": ("Finlande", "FI"),
    "FR": ("France", "FR"), "HR": ("Croatie", "HR"), "HU": ("Hongrie", "HU"),
    "IE": ("Irlande", "IE"), "IS": ("Islande", "IS"), "IT": ("Italie", "IT"),
    "LT": ("Lituanie", "LT"), "LU": ("Luxembourg", "LU"), "LV": ("Lettonie", "LV"),
    "MT": ("Malte", "MT"), "NL": ("Pays-Bas", "NL"), "NO": ("Norvège", "NO"),
    "PL": ("Pologne", "PL"), "PT": ("Portugal", "PT"), "RO": ("Roumanie", "RO"),
    "SE": ("Suède", "SE"), "SI": ("Slovénie", "SI"), "SK": ("Slovaquie", "SK"),
}

# Libellés courts pour l'affichage (le libellé officiel est conservé à côté)
DIVISIONS = {
    "GF01": "Services généraux", "GF02": "Défense", "GF03": "Ordre et sécurité publics",
    "GF04": "Affaires économiques", "GF05": "Environnement", "GF06": "Logement et équipements collectifs",
    "GF07": "Santé", "GF08": "Loisirs, culture et culte", "GF09": "Enseignement",
    "GF10": "Protection sociale",
}
SOCIAL = {  # sous-catégories affichées -> groupes COFOG agrégés
    "SP_OLD": ("Vieillesse (surtout retraites)", ["GF1002"]),
    "SP_SURV": ("Survivants (pensions de réversion…)", ["GF1003"]),
    "SP_SICK": ("Maladie et invalidité", ["GF1001"]),
    "SP_FAM": ("Famille et enfants", ["GF1004"]),
    "SP_UNEMP": ("Chômage", ["GF1005"]),
    "SP_HOUS": ("Logement (aides sociales)", ["GF1006"]),
    "SP_OTHER": ("Exclusion sociale et autres", ["GF1007", "GF1008", "GF1009"]),
}


def clean(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def main():
    d = pd.read_csv(RAW / "gov_10a_exp.csv", dtype={"OBS_FLAG": str, "CONF_STATUS": str})
    last_update = d["LAST UPDATE"].unique().tolist()
    d = d[(d.TIME_PERIOD == YEAR) & d.geo.isin(COUNTRIES)]
    obs = {(r.unit, r.geo, r.cofog99): (clean(r.OBS_VALUE), r.OBS_FLAG if isinstance(r.OBS_FLAG, str) else None)
           for r in d.itertuples()}
    labels = dict(l.split("\t", 1) for l in (RAW / "cofog99_labels_fr.tsv").read_text(encoding="utf-8").strip().splitlines())
    pop = pd.read_csv(RAW / "nama_10_pe.csv", dtype={"OBS_FLAG": str})
    pop = pop[pop.TIME_PERIOD == YEAR].set_index("geo")
    ts = (RAW / "tradle_countries.ts").read_text(encoding="utf-8")
    coords = {m[0]: (float(m[1]), float(m[2])) for m in
              re.findall(r'code:\s*"(\w\w)",\s*latitude:\s*(-?[\d.]+),\s*longitude:\s*(-?[\d.]+)', ts)}

    report, profiles, rows = [], [], []

    def get(unit, geo, code):
        return obs.get((unit, geo, code), (None, "absent"))

    for geo, (name, iso) in COUNTRIES.items():
        tot_pc, f_tot = get("PC_GDP", geo, "TOTAL")
        tot_me, _ = get("MIO_EUR", geo, "TOTAL")
        flags = set()
        divs = []
        for code, short in DIVISIONS.items():
            pc, f1 = get("PC_GDP", geo, code)
            me, f2 = get("MIO_EUR", geo, code)
            flags |= {f for f in (f1, f2) if f}
            item = {"code": code, "label": short, "label_officiel": labels.get(code), "pc_gdp": pc,
                    "mio_eur": me, "part_du_total": None}
            if code == "GF10":
                kids = []
                for kcode, (klabel, members) in SOCIAL.items():
                    vals = [get("MIO_EUR", geo, m) for m in members]
                    pcs = [get("PC_GDP", geo, m) for m in members]
                    present = [v for v, _ in vals if v is not None]
                    missing = [m for m, (v, _) in zip(members, vals) if v is None]
                    flags |= {f for _, f in vals + pcs if f}
                    kids.append({"code": kcode, "label": klabel, "cofog": members,
                                 "mio_eur": sum(present) if present else None,
                                 "pc_gdp_somme_publiee": round(sum(p for p, _ in pcs if p is not None), 1) if present else None,
                                 "composantes_manquantes": missing})
                item["detail"] = kids
            divs.append(item)
        # R4 : parts dans le total à partir des MIO_EUR
        s_me = sum(x["mio_eur"] for x in divs)
        for x in divs:
            x["part_du_total"] = x["mio_eur"] / s_me
            for k in x.get("detail", []):
                k["part_du_total"] = None if k["mio_eur"] is None else k["mio_eur"] / s_me

        # Contrôles
        s_pc = sum(x["pc_gdp"] for x in divs)
        gap_me = (s_me - tot_me) / tot_me * 100
        sp = next(x for x in divs if x["code"] == "GF10")
        s_kids = sum(k["mio_eur"] for k in sp["detail"] if k["mio_eur"] is not None)
        gap_sp = (s_kids - sp["mio_eur"]) / sp["mio_eur"] * 100
        miss = [m for k in sp["detail"] for m in k["composantes_manquantes"]]
        ok1 = abs(gap_me) < 0.1 and abs(s_pc - tot_pc) <= 0.35
        ok2 = abs(gap_sp) < 0.5
        report.append(f"{geo}  niv.I: somme {s_me:,.0f} vs total {tot_me:,.0f} M€ ({gap_me:+.3f} %) ; "
                      f"%PIB {s_pc:.1f} vs {tot_pc:.1f}  -> {'OK' if ok1 else 'ÉCHEC'} | "
                      f"GF10: détail {gap_sp:+.3f} %{' manquant: ' + ','.join(miss) if miss else ''} -> {'OK' if ok2 else 'ÉCHEC'}")

        p_val = pop.loc[geo, "OBS_VALUE"] if geo in pop.index else None
        profiles.append({
            "geo": geo, "iso2": iso, "nom": name, "annee": YEAR,
            "lat": coords[iso][0], "lon": coords[iso][1],
            "total": {"pc_gdp": tot_pc, "mio_eur": tot_me},
            "population_milliers": clean(p_val),
            "provisoire": "p" in flags,
            "drapeaux": sorted(flags),
            "divisions": divs,
        })
        for x in divs:
            rows.append([geo, name, x["code"], x["label"], x["pc_gdp"], round(x["mio_eur"], 1), round(100 * x["part_du_total"], 2)])
            for k in x.get("detail", []):
                rows.append([geo, name, k["code"], "  └ " + k["label"], k["pc_gdp_somme_publiee"],
                             None if k["mio_eur"] is None else round(k["mio_eur"], 1),
                             None if k["part_du_total"] is None else round(100 * k["part_du_total"], 2)])
        rows.append([geo, name, "TOTAL", "Total", tot_pc, tot_me, 100.0])

    (OUT / "profils_2024.json").write_text(json.dumps(profiles, ensure_ascii=False, indent=1), encoding="utf-8")
    pd.DataFrame(rows, columns=["geo", "pays", "code", "categorie", "pc_pib", "mio_eur", "part_du_total_pct"]).to_csv(
        OUT / "profils_2024.csv", index=False)
    raw_meta = {p.name[:-10]: json.loads(p.read_text()) for p in RAW.glob("*.meta.json")}
    meta = {
        "projet": "Jeu de devinette des finances publiques — profils 2024",
        "genere_le": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sources": {
            "depenses": {"jeu": "gov_10a_exp", "doi": "https://doi.org/10.2908/GOV_10A_EXP",
                         "derniere_mise_a_jour_eurostat": last_update, "producteur": "Eurostat",
                         "metadonnees": "https://ec.europa.eu/eurostat/cache/metadata/en/gov_10a_exp_esms.htm"},
            "population": {"jeu": "nama_10_pe", "doi": "https://doi.org/10.2908/NAMA_10_PE"},
            "centroides": {"source": "Google canonical countries.csv, via le dépôt Tradle (licence MIT)"},
            "licence": "Réutilisation autorisée sous réserve de citer la source (Décision 2011/833/UE) ; "
                       "modifications signalées ci-dessous.",
        },
        "perimetre": {"secteur": "S13 administrations publiques, consolidé", "operation": "TE dépense totale",
                      "nomenclature": "COFOG 1999", "annee": YEAR},
        "unites": {"pc_gdp": "% du PIB, valeur publiée (0,1 point)", "mio_eur": "millions d'euros courants",
                   "part_du_total": "fraction calculée à partir des MIO_EUR"},
        "transformations": __doc__.split("Règles appliquées (aucune autre transformation) :")[1].strip(),
        "fichiers_bruts": raw_meta,
    }
    (OUT / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    txt = "\n".join(report)
    n_fail = txt.count("ÉCHEC")
    (OUT / "controles_2024.txt").write_text(txt + f"\n\nÉchecs : {n_fail}\n", encoding="utf-8")
    print(txt, f"\nÉchecs : {n_fail}")


if __name__ == "__main__":
    main()
