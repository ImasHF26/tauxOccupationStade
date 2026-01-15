# Prédiction de l'Affluence dans les Stades de Football

Un projet d'analyse de données et de machine learning pour prédire l'occupation des stades de football basé sur des variables contextuelles et temporelles.

---

## 📋 Table des matières

- [Aperçu du projet](#aperçu-du-projet)
- [Architecture et pipeline](#architecture-et-pipeline)
- [Installation](#installation)
- [Guide d'utilisation](#guide-dutilisation)
- [Résultats et performances](#résultats-et-performances)
- [Structure du projet](#structure-du-projet)
- [Remarques importantes](#remarques-importantes)

---

## 🎯 Aperçu du projet

### Objectif
Développer un modèle de régression multivariée capable de prédire l'affluence dans les stades de football avec une précision suffisante pour la planification opérationnelle et commerciale.

### Données sources
- **Botola Pro** (Ligue marocaine)
- **CAN 2023 & 2025** (Coupe d'Afrique des Nations)
- **FIFA Club World Cup** (Coupe du Monde des Clubs)

### Périmètre de l'analyse
- **363 matchs** analysés
- **19 variables initiales** → **30 variables après ingénierie**
- **Horizon temporel** : Données historiques agrégées par compétition

---

## 🔄 Architecture et pipeline

### Phase 1️⃣ : Acquisition des données - `ScrapeDataGlobal.py`

**Objectif** : Scraper et consolider les données de plusieurs sources web

```bash
python scripts/ScrapeDataGlobal.py
```

**Fonctionnalité** :
- Exécute séquentiellement 4 scripts de scraping :
  - `ScrapeFifaClub.py` - Coupe du Monde des Clubs FIFA
  - `ScrapeCan2023.py` - CAN 2023
  - `ScrapeCan2025.py` - CAN 2025
  - `ScrapeBotolaPro.py` - Ligue professionnelle marocaine
- Fusionne tous les fichiers CSV dans `data/raw/ScrapeDataGlobal.csv`
- Détecte automatiquement les séparateurs CSV et nettoie les lignes vides

**Sortie** : 
- `data/raw/ScrapeDataGlobal.csv` (données brutes consolidées)

---

### Phase 2️⃣ : Nettoyage des données - `Nettoyage.ipynb`

**Objectif** : Préparer les données pour l'analyse

**Étapes principales** :
1. **Désagrégation de l'affluence** pour la Botola Pro (240 matchs)
   - Utilise des coefficients multiplicateurs avec variance ±5%
2. **Création de variables** :
   - `taux_occupation` (%) = (affluence / capacité) × 100
   - Variables temporelles : année, mois, jour_semaine, est_weekend
   - `categorie_stade` : classification (Petit/Moyen/Grand)
   - `derby_top_team` : interaction derby × top équipe
3. **Imputation des valeurs manquantes** :
   - Température : par médiane
   - Prix du billet : par médiane par compétition
   - Recette : calculée si manquante
4. **Détection des outliers** (marqués mais conservés) :
   - 8 outliers détectés sur l'affluence

**Résultats** :
- ✅ **Lignes** : 363 (aucune suppression)
- ✅ **Colonnes** : 30 (11 de plus)
- ✅ **Absence de valeurs manquantes**

**Sortie** : 
- `data/processed/data_cleaned.csv`

---

### Phase 3️⃣ : Analyse Exploratoire - `EDA.ipynb`

**Objectif** : Comprendre les distributions et identifier les facteurs influents

**Insights clés** :

| Variable | Valeur |
|----------|--------|
| Affluence moyenne | 15 025 ± 11 974 |
| Taux d'occupation moyen | 47.3% |
| Capacité moyenne | 35 406 places |

**Corrélations principales** (avec l'affluence) :
- **Recette_Moyenne** : 0.691 ⭐⭐⭐
- **Capacité du stade** : 0.603 ⭐⭐⭐
- **Taux d'occupation** : 0.469 ⭐⭐

**Facteurs booléens impactants** :
- ✅ Derby → Impact positif
- ✅ Match important → Impact positif
- ✅ Top équipe à domicile → Impact positif

**Variabilité par compétition** :
- Affluence la plus forte : FIFA Club World Cup
- Affluence la plus faible : Botola Pro

**Résultats visuels** :
- 8 visualisations générées dans `visualisation/eda/`

---

### Phase 4️⃣ : Réduction dimensionnelle - `ACP.ipynb`

**Objectif** : Identifier les composantes principales et réduire la dimensionnalité

**Configuration** :
- 11 variables continues analysées
- Standardisation : centrage-réduction (StandardScaler)

**Variance expliquée** :

| Composante | Variance | Cumulative |
|-----------|----------|-----------|
| PC1 | 33.30% | 33.30% |
| PC2 | 20.58% | 53.88% |
| PC3 | 10.98% | 64.87% |
| PC4 | 8.86% | 73.73% |
| PC5 | 7.97% | 81.70% |

**Critères de sélection** :
- Critère de Kaiser (λ > 1) : **4 composantes** ✅
- Critère des 80% de variance : **5 composantes**
- **Recommandation** : Utiliser 4 composantes

**Interprétation des composantes** :
- **PC1** (33.30%) : Récurrence, prix, type de match
- **PC2** (20.58%) : Facteur temporel (jour/semaine, weekend)
- **PC3** (10.98%) : Spécificité des derbys et capacité
- **PC4** (8.86%) : Variabilité résiduelle

**Sortie** :
- `data/pca/data_with_pca.csv` (données + scores PCA)
- `data/pca/pca_loadings.csv` (corrélations variables-composantes)
- `data/pca/pca_contributions.csv` (contributions en %)
- 5 visualisations dans `visualisation/acp/`

---

### Phase 5️⃣ : Modélisation - `Modele.ipynb`

**Objectif** : Développer et comparer 3 approches de régression

#### Modèle 1 : Variables Originales (10 features)

```
Features : Capacite, prix_billet_moyen, temperature, isDerby, 
           is_important_match, is_top_team_home, est_weekend, 
           mois, jour_semaine, derby_top_team
```

| Métrique | Train | Test |
|----------|-------|------|
| **R²** | 0.533 | 0.674 |
| **RMSE** | 7 966 | 7 458 |
| **MAE** | 4 963 | 5 270 |

---

#### Modèle 2 : Composantes Principales (5 features)

```
Features : PC1, PC2, PC3, PC4, PC5
```

| Métrique | Train | Test |
|----------|-------|------|
| **R²** | 0.438 | 0.628 |
| **RMSE** | 8 744 | 7 963 |
| **MAE** | 6 538 | 5 727 |

---

#### ⭐ Modèle 3 : Approche Hybride (12 features) - **MEILLEUR**

```
Features : Variables originales (10) + PC1 + PC2
```

| Métrique | Train | Test |
|----------|-------|------|
| **R²** | 0.740 | 0.852 ⭐ |
| **RMSE** | 5 947 | 5 027 |
| **MAE** | 4 119 | 3 696 |

**Interprétation** : Le modèle explique **85.2% de la variance** de l'affluence

---

#### Analyse des résidus

- Moyenne : -442 (proche de zéro ✓)
- Normalité (Shapiro-Wilk) : p-value = 0.0279 → Non-normaux
- Homoscédasticité : **Détectée**, hétéroscédasticité modérée

#### Features les plus influentes

| Rang | Variable | Coefficient |
|------|----------|------------|
| 1 | PC1 | +16 164 |
| 2 | PC2 | +3 866 |
| 3 | derby_top_team | -36 300 |
| 4 | isDerby | -36 300 |
| 5 | is_top_team_home | -8 274 |

---

### Phase 6️⃣ : Prédiction et déploiement - `Prediction.ipynb`

**Objectif** : Utiliser le modèle hybride entraîné pour prédire l'affluence

**Modèle déployé** :
- Type : Approche hybride
- Fichier : `models/model_affluence.pkl`
- R² : 0.780 (sur données complètes)

#### Utilisation du modèle

**Option 1 : Exécuter le script de prédiction**

```bash
python scripts/Prediction.py
```

**Option 2 : Utiliser la fonction dans votre code**

```python
from scripts.Prediction import predire_affluence

resultat = predire_affluence(
    capacite=68700,
    prix_billet=300,
    temperature=17,
    is_derby=1,
    is_important=1,
    is_top_team=1,
    is_weekend=0,
    mois=1,
    jour_semaine=3
)

print(f"Affluence prédite : {resultat['affluence_predite']} spectateurs")
print(f"Taux d'occupation : {resultat['taux_occupation']}%")
```

**Option 3 : Charger directement le modèle**

```python
import pickle
import numpy as np

with open('models/model_affluence.pkl', 'rb') as f:
    model = pickle.load(f)

# Préparer vos données au bon format
predictions = model.predict(X_new)
```

#### Scénarios de test prédéfinis

8 scénarios inclus dans `data/models/scenarios_test.csv` :

1. **Match classique Botola Pro - Semaine** → 34 279 spectateurs (76.2%)
2. **Derby Botola Pro - Weekend** → Nécessite validation
3. **Ligue des Champions - Match important** → 7 932 spectateurs (13.2%)
4. **Petit stade - Match normal** → Capacité à vérifier
5. **Finale CAN 2025** → Cas exceptionnel
6. **Match hiver - Froid** → 24 880 spectateurs (55.3%)
7. **Choc au sommet - Grand stade** → 26 708 spectateurs (39.9%)
8. **Dernier match de saison** → 33 754 spectateurs (75.0%)

**Sortie** : 
- `data/prediction/predictions.csv`
- Visualisations : `visualisation/models/`

---

## 📦 Installation

### Prérequis
- Python 3.8+
- pip ou conda

### 1. Cloner le dépôt

```bash
git clone <repository-url>
cd ProjetTP1
```

### 2. Créer un environnement virtuel

```bash
# Avec venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Ou avec conda
conda create -n stadium-prediction python=3.8
conda activate stadium-prediction
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### Dépendances principales

| Package | Version | Utilisation |
|---------|---------|------------|
| pandas | 2.0.3 | Manipulation de données |
| numpy | 1.24.3 | Calculs numériques |
| scikit-learn | 1.3.0 | Machine learning, ACP, régression |
| matplotlib | 3.7.2 | Visualisations |
| seaborn | 0.12.2 | Visualisations statistiques |
| plotly | 5.17.0 | Graphiques interactifs |
| jupyter | 1.0.0 | Notebooks interactifs |
| requests | 2.31.0 | Web scraping |
| beautifulsoup4 | 4.12.2 | Parsing HTML |

---

## 🚀 Guide d'utilisation

### Exécution complète du pipeline

```bash
# 1. Scraper et consolider les données
python scripts/ScrapeDataGlobal.py

# 2. Ouvrir les notebooks Jupyter dans l'ordre
jupyter notebook notebook/Nettoyage.ipynb
jupyter notebook notebook/EDA.ipynb
jupyter notebook notebook/ACP.ipynb
jupyter notebook notebook/Modele.ipynb
jupyter notebook notebook/Prediction.ipynb
```

### Exécution étape par étape

#### Étape 1 : Scraping
```bash
python scripts/ScrapeDataGlobal.py
```
Vérifie : `data/raw/ScrapeDataGlobal.csv` créé

#### Étape 2 : Nettoyage
Ouvrir `notebook/Nettoyage.ipynb` et exécuter toutes les cellules
Vérifie : `data/processed/data_cleaned.csv` créé

#### Étape 3 : EDA
Ouvrir `notebook/EDA.ipynb` et exécuter toutes les cellules
Vérifie : `visualisation/eda/` contient des graphiques

#### Étape 4 : ACP
Ouvrir `notebook/ACP.ipynb` et exécuter toutes les cellules
Vérifie : `data/pca/data_with_pca.csv` créé

#### Étape 5 : Modélisation
Ouvrir `notebook/Modele.ipynb` et exécuter toutes les cellules
Vérifie : `models/model_affluence.pkl` créé

#### Étape 6 : Prédiction
Ouvrir `notebook/Prediction.ipynb` et exécuter toutes les cellules
Vérifie : `data/prediction/predictions.csv` créé

---

## 📊 Résultats et performances

### Modèle final (Approche Hybride)

```
R² Test Set : 0.852 (85.2% de variance expliquée)
RMSE Test : 5 027 spectateurs
MAE Test : 3 696 spectateurs (erreur moyenne)
```

### Prédiction du taux d'occupation
```
R² : 0.625
MAE : 12.11%
```

### Forces du modèle
✅ Bon pouvoir prédictif global (R² = 0.852)  
✅ Erreur absolue moyenne acceptable (~3 700 spectateurs)  
✅ Combine variables originales et composantes principales  
✅ Variables interprétables

### Limitations
⚠️ Résidus non-gaussiens  
⚠️ Hétéroscédasticité détectée  
⚠️ Performance réduite pour cas extrêmes (très petits/grands stades)  
⚠️ Ne prend pas en compte les événements imprévus  
⚠️ Sur-apprentissage potentiel à monitorer  

### Recommandations pour amélioration

1. **Données** 
   - Collecter plus d'observations (surtout compétitions sous-représentées)
   - Enrichir avec données historiques équipes/joueurs

2. **Modélisation**
   - Tester modèles non-linéaires (Random Forest, XGBoost, Neural Networks)
   - Ajouter interactions polynomiales
   - Ajuster hyperparamètres

3. **Features**
   - Historique affluence des équipes
   - Données météorologiques détaillées
   - Effectif disponible des équipes
   - Classement/momentum en compétition

4. **Suivi en production**
   - Réentraîner périodiquement avec nouvelles données
   - Valider prédictions sur matchs réels
   - Monitorer dérive du modèle

---

## 📁 Structure du projet

```
ProjetTP1/
├── README.md                                 # Ce fichier
├── requirements.txt                          # Dépendances Python
│
├── scripts/
│   ├── ScrapeDataGlobal.py                  # Orchestrateur scraping
│   ├── ScrapeFifaClub.py                    # Scraper FIFA
│   ├── ScrapeCan2023.py                     # Scraper CAN 2023
│   ├── ScrapeCan2025.py                     # Scraper CAN 2025
│   ├── ScrapeBotolaPro.py                   # Scraper Botola Pro
│   └── Prediction.py                        # Script prédiction
│
├── notebook/
│   ├── Nettoyage.ipynb                      # Données brutes → nettoyées
│   ├── EDA.ipynb                            # Exploration statistique
│   ├── ACP.ipynb                            # Analyse en composantes principales
│   ├── Modele.ipynb                         # Entraînement modèles
│   └── Prediction.ipynb                     # Prédictions et déploiement
│
├── data/
│   ├── raw/
│   │   ├── ScrapeDataGlobal.csv             # Données brutes consolidées
│   │   ├── botola_2019_2020_matches.csv     
│   │   ├── can2023_matches_enrichis.csv
│   │   ├── can2025_matches_enrichis.csv
│   │   └── club_world_cup_multiseason.csv
│   │
│   ├── processed/
│   │   ├── data_cleaned.csv                 # Données nettoyées
│   │   └── rapport_eda.txt                  # Rapport EDA
│   │
│   ├── pca/
│   │   ├── data_with_pca.csv                # Données + composantes PCA
│   │   ├── pca_loadings.csv                 # Matrice de corrélations
│   │   ├── pca_contributions.csv            # Contributions en %
│   │   └── rapport_acp.txt                  # Rapport ACP
│   │
│   ├── prediction/
│   │   ├── predictions.csv                  # Prédictions finales
│   │   ├── models_comparison.csv            # Comparaison modèles
│   │   └── rapport_regression.txt           # Rapport de régression
│   │
│   └── models/
│       └── scenarios_test.csv               # 8 scénarios prédéfinis
│
├── models/
│   ├── model_affluence.pkl                  # Modèle entraîné
│   ├── features_list.pkl                    # Liste des features
│   ├── model_stats.pkl                      # Statistiques de normalisation
│   └── model_metadata.pkl                   # Métadonnées
│
├── rapport/
│   ├── 01_rapport_nettoyage.txt             # Détails nettoyage
│   ├── 02_rapport_eda.txt                   # Détails EDA
│   ├── 03_rapport_acp.txt                   # Détails ACP
│   ├── 04_rapport_regression.txt            # Détails modélisation
│   └── rapport_deploiement.txt              # Détails déploiement
│
└── visualisation/
    ├── nettoyage/                           # Graphiques nettoyage
    ├── eda/                                 # Graphiques exploratoires
    ├── acp/                                 # Graphiques ACP
    ├── modele/                              # Graphiques modèle
    └── models/                              # Prédictions visualisées
```

---

## ⚠️ Remarques importantes

### Variables critiques
- **Capacité du stade** : Variable prédictive la plus importante
- **Recette moyenne** : Forte corrélation (0.69) avec l'affluence
- **Derby et match important** : Facteurs booléens significatifs

### Traitement spécifique Botola Pro
Les données de Botola Pro ont été **désagrégées** avec coefficients multiplicateurs pour obtenir les affluences réelles (données publiquement disponibles agrégées).

### Interprétation des coefficients du modèle
Les coefficients négatifs sur `derby_top_team` et `isDerby` ne signifient pas un impact négatif réel, mais reflètent les **interactions complexes** dans le modèle hybride. Les anályses bivariées confirment un impact positif.

### Cas limites
Le modèle peut prédire des affluences négatives ou supérieures à la capacité dans les **cas extrêmes** (petits stades, matchs exceptionnels). Ces prédictions doivent être **clippées** à [0, capacité].

### Mise à jour du modèle
Réentraîner le modèle tous les **6 mois** ou après **50+ nouvelles observations** pour maintenir la performance en production.

---

## 📞 Contact et support

Pour toute question sur le pipeline ou les résultats, consulter les rapports détaillés dans le dossier `rapport/`.

---

**Dernier mise à jour** : 13 janvier 2026  
**État du projet** : Production ✅  
**Python version** : 3.8+  
**Statut de validation** : ✓ Prêt pour Git
