import os, time, datetime as dt, requests
from bs4 import BeautifulSoup
import pandas as pd

# ---------- CONFIG ----------
SESSIONS = {
    "2022": {
        "url": "https://en.wikipedia.org/wiki/2022_FIFA_Club_World_Cup",
        "prix": 80,
        "stades": {
            "Tangier Grand Stadium": {"ville": "Tangier", "cap": 65_000, "lat": 35.7667, "lon": -5.8000},
            "Prince Moulay Abdellah Stadium": {"ville": "Rabat", "cap": 53_000, "lat": 34.0209, "lon": -6.8416},
        },
    },
    "2014": {
        "url": "https://en.wikipedia.org/wiki/2014_FIFA_Club_World_Cup",
        "prix": 60,
        "stades": {
            "Stade de Marrakech": {"ville": "Marrakech", "cap": 41_245, "lat": 31.6342, "lon": -7.9969},
            "Prince Moulay Abdellah Stadium": {"ville": "Rabat", "cap": 52_000, "lat": 34.0209, "lon": -6.8416},
        },
    },
    "2013": {
        "url": "https://en.wikipedia.org/wiki/2013_FIFA_Club_World_Cup",
        "prix": 60,
        "stades": {
            "Stade de Marrakech": {"ville": "Marrakech", "cap": 41_356, "lat": 31.6342, "lon": -7.9969},
            "Stade Adrar": {"ville": "Agadir", "cap": 45_480, "lat": 30.4277, "lon": -9.5833},
        },
    },
}

HEADERS = {
    "User-Agent": "Stat-Etudiant/1.0 (https://example.com; contact@example.com)",
    "Accept-Language": "en,fr;q=0.5",
}

TOP_TEAMS = {"Real Madrid", "Barcelona","Monterrey", "Chelsea", "Bayern Munich", 
             "Paris Saint-Germain", "AC Milan", "Inter Milan","Atlético Mineiro", 
             "Al Ahly", "Palmeiras", "Flamengo", "San Lorenzo", "Auckland City"}
DERBIES = {("Real Madrid", "Barcelona"), ("AC Milan", "Inter Milan"), 
           ("Al Ahly", "Zamalek"), ("Palmeiras", "Santos"), ("Flamengo", "Fluminense")}


# ---------- FONCTIONS ----------
def get_temp(lat, lon, date_match):
    if not (lat and lon and date_match): return None
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date_match}&end_date={date_match}&daily=temperature_2m_mean&timezone=Africa%2FCasablanca"
        return round(requests.get(url, timeout=15).json()["daily"]["temperature_2m_mean"][0], 1)
    except: return None


def phase_from(box):
    for tag in box.find_all_previous(["h2", "h3"], limit=1):
        txt = tag.get_text(strip=True)
        if "Final" in txt: return "Final"
        if "Third place" in txt: return "Third place play-off"
        if "Semi-finals" in txt: return "Semi-finals"
        if "Quarter-finals" in txt: return "Quarter-finals"
        if "Second round" in txt: return "Second round"
    return "First round"


def phase_importance(phase: str) -> int:
    return {"First round": 1, "Second round": 2, "Quarter-finals": 3, "Semi-finals": 4, "Final": 5, "Third place play-off": 2}.get(phase, 1)


def is_important(phase, spect, cap): return phase_importance(phase) >= 3 or (spect or 0) > 0.8 * cap


# ---------- SCRAPING ----------
all_rows = []
for saison, cfg in SESSIONS.items():
    html = requests.get(cfg["url"], headers=HEADERS, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    prix = cfg["prix"]
    stades = cfg["stades"]

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

        if stade not in stades: continue

        # Attendance corrigée
        affluence_div = box.select_one('.fright div:nth-child(2)')
        affluence = 0
        if affluence_div and affluence_div.text.startswith("Attendance:"):
            try: affluence = int(affluence_div.text.split(":")[1].strip().replace(",", ""))
            except: affluence = 0

        info = stades[stade]
        cap = info["cap"]
        temp = get_temp(info["lat"], info["lon"], date_match)

        is_derby = (home, away) in DERBIES or (away, home) in DERBIES
        phase_imp = phase_importance(phase)
        is_imp = is_important(phase, affluence, cap)
        is_top_home = home in TOP_TEAMS
        recette = prix * affluence

        all_rows.append([
            "FIFA Club World Cup", saison, stade, ville, cap,
            home, away, score, is_derby, phase_imp,
            is_imp, is_top_home, affluence,
            date_match, heure, prix, temp, recette
        ])
        time.sleep(0.25)

# ---------- EXPORT ----------
os.makedirs("data/raw", exist_ok=True)
df = pd.DataFrame(all_rows, columns=[
    "Competition", "saison", "Stade", "Ville", "Capacite",
    "Equipe_Home", "Equipe_Away", "Score", "isDerby", "PhaseImportance",
    "is_important_match", "is_top_team_home", "affluence_moyenne",
    "date_Match", "heure_match", "prix_billet_moyen", "temperature", "Recette_Moyenne"
])
df.to_csv("data/raw/club_world_cup_multiseason.csv", index=False, encoding="utf-8-sig")

print(df.head(), "\n\nTotal :", len(df), "matchs")