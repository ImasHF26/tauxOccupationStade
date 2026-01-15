import requests, os, time, datetime as dt
from bs4 import BeautifulSoup
import pandas as pd

URL = "https://en.wikipedia.org/wiki/2023_Africa_Cup_of_Nations"

HEADERS = {                       # ← 1) respecter la politique WP
    "User-Agent": "Stat-Etudiant/1.0 (https://example.com; contact@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en,fr;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

STADES = {
    "Alassane Ouattara Stadium": {"ville": "Abidjan", "capacite": 60000, "lat": 5.4167, "lon": -4.0167},
    "Felix Houphouet Boigny Stadium": {"ville": "Abidjan", "capacite": 33000, "lat": 5.348, "lon": -4.006},
    "Stade de la Paix": {"ville": "Bouaké", "capacite": 40000, "lat": 7.69, "lon": -5.03},
    "Amadou Gon Coulibaly Stadium": {"ville": "Korhogo", "capacite": 20000, "lat": 9.45, "lon": -5.633},
    "Charles Konan Banny Stadium": {"ville": "Yamoussoukro", "capacite": 20000, "lat": 6.817, "lon": -5.283},
    "Laurent Pokou Stadium": {"ville": "San-Pédro", "capacite": 20000, "lat": 4.75, "lon": -6.633},
}

def prix_billet(phase):
    if "Final" in phase: return 40
    if "Semi" in phase: return 30
    if "Quarter" in phase: return 25
    if "Round of 16" in phase: return 20
    return 12

def get_temperature(lat, lon, date_match):
    if not lat or not lon or not date_match:
        return None
    try:
        url = (
            "https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat}&longitude={lon}&start_date={date_match}&end_date={date_match}"
            "&daily=temperature_2m_mean&timezone=Africa%2FAbidjan"
        )
        return round(requests.get(url, timeout=15).json()["daily"]["temperature_2m_mean"][0], 1)
    except Exception:
        return None

# ------------------------------------------------------------------
html = requests.get(URL, headers=HEADERS, timeout=30).text          
soup = BeautifulSoup(html, "html.parser")                   

rows = []
for box in soup.select("div.footballbox"):
    # phase = titre du segment (h2/h3) qui précède
    phase = "Group stage"
    for prev in box.find_previous_siblings(["h2", "h3"]):
        txt = prev.get_text(strip=True)
        if "Round of 16" in txt: phase = "Round of 16"
        elif "Quarter" in txt: phase = "Quarter-finals"
        elif "Semi" in txt: phase = "Semi-finals"
        elif "Final" in txt: phase = "Final"
        break

    # date & heure
    date_raw = box.select_one(".fdate").get_text(strip=True)
    heure = box.select_one(".ftime").get_text(strip=True)
    # conversion date → AAAA-MM-DD
    date_match = dt.datetime.strptime(date_raw.split("(")[0].strip(), "%d %B %Y").strftime("%Y-%m-%d")

    # équipes
    home = box.select_one(".fhome").get_text(strip=True)
    away = box.select_one(".faway").get_text(strip=True)
    score = box.select_one(".fscore").get_text(strip=True)

    # stade & ville
    stade_ville = box.select_one('[itemprop="location"]').get_text(strip=True)
    stade = stade_ville.split(",")[0].strip()
    ville = stade_ville.split(",")[1].strip() if "," in stade_ville else None

    # affluence
    try:
        attend_text = box.text.split("Attendance:")[1].split("[")[0].strip()
        affluence = int(attend_text.replace(",", ""))
    except (IndexError, ValueError):
        affluence = None

    # infos stade
    info = STADES.get(stade, {})
    capacite = info.get("capacite")
    temp = get_temperature(info.get("lat"), info.get("lon"), date_match)

    rows.append([
        stade, ville, capacite, home, away, score,
        phase, affluence, date_match, heure,
        prix_billet(phase), temp
    ])
    time.sleep(0.25)  # anti-429 pour l'API météo

# ------------------------------------------------------------------
os.makedirs("data/raw", exist_ok=True)
df = pd.DataFrame(rows, columns=[
    "Nom_Stade", "Ville", "Capacite_Stade", "Equipe_Home", "Equipe_Away",
    "Score", "Phase", "Spectateurs", "Date_Match", "Heure",
    "Prix_Billet_Moyen", "Temperature"
])
df.to_csv("data/raw/can2023_matches_enrichis.csv", index=False, encoding="utf-8-sig")

print(df.head(), "\n\nTotal :", len(df), "matchs")