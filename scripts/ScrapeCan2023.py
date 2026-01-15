import os
import time
import datetime as dt
import requests
from bs4 import BeautifulSoup
import pandas as pd

URL = "https://en.wikipedia.org/wiki/2023_Africa_Cup_of_Nations"

HEADERS = {
    "User-Agent": "Stat-Etudiant/1.0 (https://example.com; contact@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en,fr;q=0.5",
}

STADES = {
    "Alassane Ouattara Stadium": {"ville": "Abidjan", "capacite": 60_000, "lat": 5.4167, "lon": -4.0167},
    "Felix Houphouet Boigny Stadium": {"ville": "Abidjan", "capacite": 33_000, "lat": 5.348, "lon": -4.006},
    "Stade de la Paix": {"ville": "Bouake", "capacite": 40_000, "lat": 7.69, "lon": -5.03},
    "Amadou Gon Coulibaly Stadium": {"ville": "Korhogo", "capacite": 20_000, "lat": 9.45, "lon": -5.633},
    "Charles Konan Banny Stadium": {"ville": "Yamoussoukro", "capacite": 20_000, "lat": 6.817, "lon": -5.283},
    "Laurent Pokou Stadium": {"ville": "San-Pedro", "capacite": 20_000, "lat": 4.75, "lon": -6.633},
}

PRIX_CAT2 = 164  # prix constant toutes phases

TOP_TEAMS = {
    "Nigeria", "Morocco", "Senegal", "Algeria", "Egypt", "Tunisia",
    "Cameroon", "Ghana", "Ivory Coast"
}

DERBIES = {
    ("Ghana", "Nigeria"), ("Senegal", "Ivory Coast"), ("Cameroon", "Ghana"),
    ("Morocco", "Algeria"), ("Tunisia", "Algeria"), ("Egypt", "Morocco")
}


def get_temperature(lat: float, lon: float, date_match: str):
    if not (lat and lon and date_match):
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


def phase_from(box) -> str:
    for tag in box.find_all_previous(["h2", "h3"], limit=1):
        txt = tag.get_text(strip=True)
        if "Final" in txt: return "Final"
        if "Third place" in txt: return "Third place play-off"
        if "Semi" in txt: return "Semi-finals"
        if "Quarter" in txt: return "Quarter-finals"
        if "Round of 16" in txt: return "Round of 16"
    return "Group stage"


def phase_importance(phase: str) -> int:
    return {"Group stage": 1, "Round of 16": 2, "Quarter-finals": 3,
            "Semi-finals": 4, "Final": 5, "Third place play-off": 3}.get(phase, 1)


def is_important_match(phase: str, spectators: int, capacity: int) -> bool:
    importance = phase_importance(phase) >= 4 or (spectators or 0) > 0.8 * capacity
    return bool(importance)


html = requests.get(URL, headers=HEADERS, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

rows = []
for box in soup.select("div.footballbox"):
    phase = phase_from(box)

    date_raw = box.select_one(".fdate").get_text(strip=True)
    heure = box.select_one(".ftime").get_text(strip=True)
    date_match = dt.datetime.strptime(date_raw.split("(")[0].strip(), "%d %B %Y").strftime("%Y-%m-%d")

    home = box.select_one(".fhome").get_text(strip=True)
    away = box.select_one(".faway").get_text(strip=True)
    score = box.select_one(".fscore").get_text(strip=True)

    stade_ville = box.select_one('[itemprop="location"]').get_text(strip=True)
    stade, ville = (stade_ville.split(",", 1) + [None])[:2]
    stade, ville = stade.strip(), ville.strip() if ville else None

    try:
        affluence = int(box.text.split("Attendance:")[1].split("[")[0].strip().replace(",", ""))
    except (IndexError, ValueError):
        affluence = 0

    info = STADES.get(stade, {})
    capacity = info.get("capacite", 0)
    temp = get_temperature(info.get("lat"), info.get("lon"), date_match)

    is_derby = (home, away) in DERBIES or (away, home) in DERBIES
    phase_imp = phase_importance(phase)
    is_imp = is_important_match(phase, affluence, capacity)
    is_top_home = home in TOP_TEAMS
    recette_moyenne = PRIX_CAT2 * affluence

    rows.append([
        "CAN", "2023", stade, ville, capacity,
        home, away, score, is_derby, phase_imp,
        is_imp, is_top_home, affluence,
        date_match, heure, PRIX_CAT2, temp, recette_moyenne
    ])
    time.sleep(0.25)

os.makedirs("data/raw", exist_ok=True)
df = pd.DataFrame(rows, columns=[
    "Competition", "saison", "Stade", "Ville", "Capacite",
    "Equipe_Home", "Equipe_Away", "Score", "isDerby", "PhaseImportance",
    "is_important_match", "is_top_team_home", "affluence_moyenne",
    "date_Match", "heure_match", "prix_billet_moyen", "temperature", "Recette_Moyenne"
])
df.to_csv("data/raw/can2023_matches_enrichis.csv", index=False, encoding="utf-8-sig")

print(df.head(), "\n\nTotal :", len(df), "matchs")