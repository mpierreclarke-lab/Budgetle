"""Étape 1 — Téléchargement reproductible des données brutes.

Chaque fichier est enregistré tel que renvoyé par l'API (aucune transformation),
avec un fichier .meta.json : URL exacte, date/heure d'extraction, empreinte SHA-256.
Relancer ce script écrase les fichiers bruts : le dépôt Git garde l'historique.
"""
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
START = "2019"

SOURCES = {
    # Dépenses des APU par fonction COFOG, tous niveaux COFOG, dépense totale (TE), secteur S13
    "gov_10a_exp.csv": EUROSTAT + f"gov_10a_exp/A.PC_GDP+MIO_EUR+MIO_NAC+PC_TOT.S13..TE.?startPeriod={START}&format=SDMX-CSV",
    # Population (concept comptabilité nationale), pour d'éventuels montants par habitant
    "nama_10_pe.csv": EUROSTAT + f"nama_10_pe/A.THS_PER.POP_NC.?startPeriod={START}&format=SDMX-CSV",
    # Libellés officiels de la nomenclature COFOG (français)
    "cofog99_labels_fr.tsv": "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/codelist/ESTAT/COFOG99?format=TSV&lang=fr",
    # Centroïdes des pays utilisés par Tradle (Google canonical countries), dans son dépôt MIT
    "tradle_countries.ts": "https://raw.githubusercontent.com/alexandersimoes/tradle/main/src/domain/countries.ts",
}


def fetch(name: str, url: str) -> None:
    with urllib.request.urlopen(url, timeout=120) as r:
        body = r.read()
    (RAW / name).write_bytes(body)
    meta = {
        "file": name,
        "url": url,
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }
    (RAW / (name + ".meta.json")).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"{name}: {len(body):,} octets")


if __name__ == "__main__":
    for n, u in SOURCES.items():
        fetch(n, u)
