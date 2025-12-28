"""Download DVF file for Paris.
Update DVF_URL with the right source (CSV or GeoJSON).
"""
from pathlib import Path
import requests

DVF_URL = "https://files.data.gouv.fr/geo-dvf/latest/csv/2022/75.csv"  # placeholder: adjust year/source
OUTPUT = Path("data/raw/dvf.csv")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def download():
    resp = requests.get(DVF_URL, stream=True, timeout=60)
    resp.raise_for_status()
    with OUTPUT.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    download()
