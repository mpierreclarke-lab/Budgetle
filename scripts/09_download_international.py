"""Téléchargement des sources internationales (élargissement au-delà des 30 pays Eurostat).

Fichiers bruts (volumineux) : data/raw/intl/*.csv, non versionnés ; chaque téléchargement laisse un
.meta.json versionné (URL exacte, date, taille, SHA-256) pour pouvoir vérifier une reproduction.

  imf_cofog_pogdp.csv  FMI GFS_COFOG, administrations publiques (S13), fonctions niveau I + protection
                       sociale niveau II + total, en % du PIB, annuel depuis 2019
  imf_cofog_xdc.csv    idem en monnaie nationale
  imf_er.csv           FMI Exchange Rates : monnaie nationale pour 1 euro, moyenne annuelle (PA_RT)
  ecb_exr.csv          BCE : taux de référence annuels moyens (contrôle croisé des taux du FMI)
  oecd_cofog.csv       OCDE tableau 11 (COFOG), S13, dépense totale, AUS/KOR/CHL/COL
  oecd_gdp.csv         OCDE tableau 1, PIB à prix courants, mêmes pays (pour les % du PIB)
"""
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "intl"
RAW.mkdir(parents=True, exist_ok=True)

IMF = "https://api.imf.org/external/sdmx/2.1/data/"
IND = "+".join([f"GF{i:02d}_T" for i in range(1, 11)] + ["GF101_T"] + [f"GF10{i}0_T" for i in range(2, 10)] + ["TOTOUT_T"])
OECD_C = "AUS+KOR+CHL+COL"
CSV = {"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}
OECD_CSV = {"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}

SOURCES = {
    "imf_cofog_pogdp.csv": (IMF + f"IMF.STA,GFS_COFOG,11.0.0/.S13.G2MF.{IND}.POGDP_PT.A?startPeriod=2019&dimensionAtObservation=AllDimensions", CSV),
    "imf_cofog_xdc.csv": (IMF + f"IMF.STA,GFS_COFOG,11.0.0/.S13.G2MF.{IND}.XDC.A?startPeriod=2019&dimensionAtObservation=AllDimensions", CSV),
    "imf_er.csv": (IMF + "IMF.STA,ER,4.0.1/.XDC_EUR.PA_RT.A?startPeriod=2019&dimensionAtObservation=AllDimensions", CSV),
    "ecb_exr.csv": ("https://data-api.ecb.europa.eu/service/data/EXR/A..EUR.SP00.A?startPeriod=2019&format=csvdata", {}),
    "oecd_cofog.csv": (f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NASEC10@DF_TABLE11,1.1/A.{OECD_C}.S13._Z.D.OTE._Z..XDC....?startPeriod=2019&dimensionAtObservation=AllDimensions", OECD_CSV),
    "oecd_gdp.csv": (f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE1_EXPENDITURE,2.0/A.{OECD_C}.S1..B1GQ....XDC.V..?startPeriod=2019&dimensionAtObservation=AllDimensions", OECD_CSV),
}


def fetch(name, url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": "budgetle-data/1.0 (+https://github.com/mpierreclarke-lab/Budgetle)", **headers})
    with urllib.request.urlopen(req, timeout=600) as r:
        body = r.read()
    (RAW / name).write_bytes(body)
    meta = {"file": name, "url": url, "headers": headers,
            "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    (RAW / (name + ".meta.json")).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"{name}: {len(body):,} octets")


if __name__ == "__main__":
    for n, (u, h) in SOURCES.items():
        fetch(n, u, h)
