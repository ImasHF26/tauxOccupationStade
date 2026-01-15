import os, time, datetime as dt, requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# ---------- CONFIG ----------
BASE_URL   = "https://www.transfermarkt.fr"
STATS_URL  = f"{BASE_URL}/botola-pro-inwi/besucherzahlen/wettbewerb/MAR1/plus/1?saison_id=2019"
MATCHES_URL= f"{BASE_URL}/botola-pro-inwi/spieltag/wettbewerb/MAR1/spieltag"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

STADES = {
    "Stade Mohamed V":                  {"ville":"Casablanca","cap":67000,"clubs":["Wydad Casablanca","Raja Club Athletic"],   "lat":33.533,"lon":-7.667},
    "Stade Ibn-Batouta":                {"ville":"Tangier",   "cap":75600,"clubs":["Ittihad Tanger"],                          "lat":35.767,"lon":-5.800},
    "Stade de honneur de Oujda":        {"ville":"Oujda",     "cap":35000,"clubs":["Mouloudia d'Oujda"],                       "lat":34.683,"lon":-1.917},
    "Complexe Sportif Moulay Abdallah": {"ville":"Rabat",     "cap":65200,"clubs":["AS FAR Rabat"],                            "lat":33.967,"lon":-6.817},
    "Stade Saniat-Rmel":                {"ville":"Tetouan",   "cap":15000,"clubs":["Moghreb Atlético Tétouan"],                "lat":35.567,"lon":-5.367},
    "Stade Adrar":                      {"ville":"Agadir",    "cap":45480,"clubs":["Hassania d'Agadir"],                       "lat":30.433,"lon":-9.600},
    "Stade El Massira":                 {"ville":"Safi",      "cap":15000,"clubs":["Olympique Safi"],                          "lat":32.283,"lon":-9.233},
    "Stade Municipal de Berkane":       {"ville":"Berkane",   "cap":15000,"clubs":["Renaissance de Berkane"],                  "lat":34.917,"lon":-2.333},
    "Stade El Abdi":                    {"ville":"El-Jadida", "cap":15000,"clubs":["Difaâ El Jadida"],                         "lat":33.233,"lon":-8.500},
    "Stade honneur de Beni Mellal":     {"ville":"Beni Mellal","cap":15000,"clubs":["Raja Beni Mellal"],                       "lat":32.333,"lon":-6.367},
    "Stade Prince Moulay Hassan":       {"ville":"Rabat",     "cap":22000,"clubs":["FUS Rabat"],                               "lat":33.967,"lon":-6.817},
    "Stade Ahmed Choukri":              {"ville":"Zemamra",   "cap": 2500,"clubs":["Renaissance Zemamra"],                     "lat":32.200,"lon":-8.067},
    "Stade Municipale de Oued Zem":     {"ville":"Oued Zem",  "cap":8000,"clubs":["Rapide Oued Zem"],                          "lat":32.900,"lon":-6.933},
    "Stade Municipal Berrechid":        {"ville":"Berrechid", "cap":6000,"clubs":["Youssoufia Berrechid"],                     "lat":33.200,"lon":-7.583},
    "Complexe Sportif du Phosphate":    {"ville":"Khouribga", "cap":15000,"clubs":["Olympique Khouribga"],                     "lat":33.167,"lon":-6.283},
}

PRIX_CAT2 = 60
TOP_TEAMS = {"Wydad Casablanca","Raja Club Athletic","AS FAR Rabat","RS Berkane","Ittihad Tanger","FUS Rabat"}
DERBIES  = {("Wydad Casablanca","Raja Club Athletic"),("AS FAR Rabat","FUS Rabat"),("Ittihad Tanger","Moghreb Atlético Tétouan")}

# ---------- FONCTIONS ----------
def get_temp(lat, lon, date_match):
    if not (lat and lon and date_match):
        return None
    try:
        url = (f"https://archive-api.open-meteo.com/v1/archive?"
               f"latitude={lat}&longitude={lon}&start_date={date_match}&end_date={date_match}"
               f"&daily=temperature_2m_mean&timezone=Africa%2FCasablanca")
        return round(requests.get(url, timeout=15).json()["daily"]["temperature_2m_mean"][0], 1)
    except:
        return None

def find_stade_by_club(club: str):
    for stade, info in STADES.items():
        if club in info["clubs"]:
            return stade, info["ville"], info["cap"]
    return "Inconnu", "Inconnu", 0

def phase_importance(journee: int) -> int:
    return 1 if journee <= 10 else 2 if journee <= 20 else 3

def is_important(journee: int, moyenne: int, cap: int) -> bool:
    return phase_importance(journee) >= 3 or moyenne > 0.8 * cap

# ---------- ETAPE 1 : MOYENNES ----------
html  = requests.get(STATS_URL, headers=HEADERS, timeout=20).text
soup  = BeautifulSoup(html, "html.parser")

moyennes = []
for tr in soup.select("table.items tbody tr"):
    cols = tr.find_all("td")
    if len(cols) < 8:
        continue
    club = cols[1].select_one("a[title]")["title"]

    txt_moy    = cols[7].get_text(strip=True).replace(".","").replace(",","")
    txt_matchs = cols[8].get_text(strip=True).replace(".","").replace(",","")
    if not (txt_moy.isdigit() and txt_matchs.isdigit()):
        continue
    moyenne, matchs = int(txt_moy), int(txt_matchs)

    stade_corr, ville, cap = find_stade_by_club(club)
    moyennes.append({"Club":club,"Stade":stade_corr,"Ville":ville,"Capacite":cap,
                     "Moyenne_Spectateurs":moyenne,"Matchs_Joues":matchs})

df_moy = pd.DataFrame(moyennes)


# --------------------------------  ÉTAPE 2 : MATCHS  --------------------------------
all_matches = []

# ---------- mapping mois fr → en ----------
MOIS_FR_EN = {
    'jan.': 'Jan', 'fév.': 'Feb', 'mars': 'Mar', 'avr.': 'Apr',
    'mai': 'May', 'juin': 'Jun', 'juil.': 'Jul', 'août': 'Aug',
    'sept.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'déc.': 'Dec'
}


for jour in range(1, 31):                       # 1 → 30
    url_jour = f"{MATCHES_URL}/?spieltag={jour}&saison_id=2019"
    try:
        resp = requests.get(url_jour, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"Journée {jour} ignorée : {e}")
        continue

    for tr in soup.select("div.box table tr.table-grosse-schrift"):
        tds = tr.find_all("td")
        if len(tds) < 9:                # structure : 9 colonnes
            continue

        # --- clubs (noms complets) ---
        home = tds[0].select_one("a[title]")["title"]
        away = tds[7].select_one("a[title]")["title"]

        # --- score ---
        score_txt = tds[4].select_one("span.matchresult").get_text(strip=True)
        if ":" not in score_txt:        # match non joué / reporté
            continue

        # --- date & heure ---
        date_tr = tr.find_next_sibling("tr")
        date_heure = date_tr.get_text(strip=True)

        # extraction date brute
        date_raw = re.search(r'(\d{1,2}\s+[a-zéû]+\.?\s+\d{4})', date_heure, flags=re.I).group(1)
        date_raw = date_raw.replace('\xa0', ' ').strip()          # enlève espace insécable

        # traduction mois
        for fr, en in MOIS_FR_EN.items():
            date_raw = date_raw.lower().replace(fr, en)

        # heure
        heure = re.search(r'(\d{1,2}:\d{2})', date_heure)
        heure = heure.group(1) if heure else ""

        # conversion
        date_match = dt.datetime.strptime(date_raw, "%d %b %Y").strftime("%Y-%m-%d")

        # --- infos stade via club domicile ---
        club_info = df_moy[df_moy["Club"].str.contains(home.split()[0], na=False)]
        if club_info.empty:
            continue
        club_info = club_info.iloc[0]
        stade = club_info["Stade"]
        ville = club_info["Ville"]
        cap   = club_info["Capacite"]
        moy   = club_info["Moyenne_Spectateurs"]

        # --- variables annexes ---
        coords = STADES.get(stade, {})
        temp  = get_temp(coords.get("lat"), coords.get("lon"), date_match)
        derby = (home, away) in DERBIES or (away, home) in DERBIES
        phase = phase_importance(jour)
        imp   = is_important(jour, moy, cap)
        top   = home in TOP_TEAMS
        rec   = PRIX_CAT2 * moy

        all_matches.append([
            "Botola Pro", "2019/2020", stade, ville, cap,
            home, away, score_txt, derby, phase,
            imp, top, moy, date_match, heure, PRIX_CAT2, temp, rec
        ])

    time.sleep(0.25)     # respect du serveur

# ----------------  EXPORT  ----------------
os.makedirs("data/raw", exist_ok=True)
df_final = pd.DataFrame(all_matches, columns=[
    "Competition","saison","Stade","Ville","Capacite",
    "Equipe_Home","Equipe_Away","Score","isDerby","PhaseImportance",
    "is_important_match","is_top_team_home","affluence_moyenne",
    "date_Match","heure_match","prix_billet_moyen","temperature","Recette_Moyenne"
])
df_final.to_csv("data/raw/botola_2019_2020_matches.csv", index=False, encoding="utf-8-sig")

print(df_final.head(), "\n\nTotal :", len(df_final), "matchs")