
# Script de prédiction - Occupation des stades
# Généré automatiquement

import pickle
import pandas as pd
import numpy as np

def charger_modele():
    """Charge le modèle et les métadonnées"""
    with open('../models/model_affluence.pkl', 'rb') as f:
        model = pickle.load(f)

    with open('../models/features_list.pkl', 'rb') as f:
        features = pickle.load(f)

    with open('../models/model_metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)

    return model, features, metadata

def predire_affluence(capacite, prix_billet, temperature, is_derby, 
                      is_important, is_top_team, is_weekend, mois, 
                      jour_semaine, derby_top_team=None):
    """
    Prédit l'affluence pour un match donné

    Paramètres:
    -----------
    capacite : int
        Capacité du stade
    prix_billet : float
        Prix moyen du billet
    temperature : float
        Température en degrés Celsius
    is_derby : int (0 ou 1)
        1 si c'est un derby, 0 sinon
    is_important : int (0 ou 1)
        1 si match important, 0 sinon
    is_top_team : int (0 ou 1)
        1 si équipe majeure à domicile, 0 sinon
    is_weekend : int (0 ou 1)
        1 si weekend, 0 sinon
    mois : int (1-12)
        Mois du match
    jour_semaine : int (0-6)
        0=Lundi, 6=Dimanche
    derby_top_team : int (0 ou 1), optionnel
        Interaction derby x top team

    Retourne:
    ---------
    dict : Dictionnaire avec affluence_predite et taux_occupation
    """

    # Charger le modèle
    model, features, metadata = charger_modele()

    # Calculer derby_top_team si non fourni
    if derby_top_team is None:
        derby_top_team = int(is_derby and is_top_team)

    # Créer le DataFrame d'entrée
    input_data = pd.DataFrame([{
        'Capacite': capacite,
        'prix_billet_moyen': prix_billet,
        'temperature': temperature,
        'isDerby': is_derby,
        'is_important_match': is_important,
        'is_top_team_home': is_top_team,
        'est_weekend': is_weekend,
        'mois': mois,
        'jour_semaine': jour_semaine,
        'derby_top_team': derby_top_team
    }])

    # Sélectionner uniquement les features nécessaires
    X = input_data[features]

    # Faire la prédiction
    affluence_predite = model.predict(X)[0]
    taux_occupation = min(100, max(0, (affluence_predite / capacite) * 100))

    return {
        'affluence_predite': round(affluence_predite, 0),
        'taux_occupation': round(taux_occupation, 1),
        'capacite': capacite
    }

# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple : Derby important un dimanche
    resultat = predire_affluence(
        capacite=67000,
        prix_billet=150,
        temperature=25,
        is_derby=1,
        is_important=1,
        is_top_team=1,
        is_weekend=1,
        mois=5,
        jour_semaine=6
    )

    print("Prédiction:")
    print(f"  Affluence : {resultat['affluence_predite']:,.0f} spectateurs")
    print(f"  Taux d'occupation : {resultat['taux_occupation']:.1f}%")
