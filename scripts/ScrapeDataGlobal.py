# ScrapeDataGlobal.py
import subprocess, os, pandas as pd, glob, shutil
from datetime import datetime as dt
import os, requests,sys

SCRIPTS = [
    "ScrapeFifaClub.py",
    "ScrapeCan2023.py",
    "ScrapeCan2025.py",
    "ScrapeBotolaPro.py"
]

ROOT = os.path.dirname(os.path.abspath(__file__))          # dossier scripts
OUT_DIR = os.path.join(ROOT, "..", "data", "raw")          # data/raw
os.makedirs(OUT_DIR, exist_ok=True)

CSV_GLOBAL = os.path.join(OUT_DIR, "ScrapeDataGlobal.csv")

def run_one(script: str):
    print(f"\n>>> {dt.now():%H:%M:%S} – lancement {script}")
    try:
        subprocess.run(
            [sys.executable, os.path.join(ROOT, script)],   # <— sys.executable
            check=True,
            cwd=ROOT
        )
        print(f"<<< {script} terminé")
        return True
    except subprocess.CalledProcessError as e:
        print(f"!!! Erreur dans {script} – code {e.returncode}")
        return False

def merge_csv():
    frames = []
    for csv in glob.glob(os.path.join(OUT_DIR, "*.csv")):
        if os.path.basename(csv) == "ScrapeDataGlobal.csv":
            continue
        try:
            # détecte automatiquement le séparateur et saute les lignes vides
            df = pd.read_csv(csv,  sep=None, engine='python')
            df.dropna(how='all', inplace=True)          # enlève les lignes totalement vides
            df["source_file"] = os.path.basename(csv)
            frames.append(df)
        except Exception as e:
            print(f"!!! Impossible de lire {csv} – {e}")
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(CSV_GLOBAL, index=False, encoding="utf-8-sig")
        print(f"\n>>> ScrapeDataGlobal.csv créé ({len(frames)} fichiers fusionnés)")
    else:
        print("!!! Aucun CSV à fusionner")

if __name__ == "__main__":
    # 1) exécution individuelle
    for scr in SCRIPTS:
        run_one(scr)

    # 2) assemblage global
    merge_csv()