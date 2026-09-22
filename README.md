# Étude de Marché — Marketplace Zambie

Application Streamlit multipage pour collecter les réponses de l'étude de
marché (Clients + Vendeurs) et suivre les résultats en temps réel.

## Structure du projet

```
marketplace_zambie_app/
├── app.py                              # Page d'accueil
├── common.py                           # Style, connexion Google Sheets, dashboard
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example            # Modèle de secrets à compléter
└── pages/
    ├── 1_📝_Questionnaire_Client.py     # 23 questions / 4 sections
    ├── 2_🏬_Questionnaire_Vendeur.py    # 20 questions / 3 sections
    └── 3_📊_Analyse.py                  # Dashboard protégé par mot de passe
```

Streamlit détecte automatiquement le dossier `pages/` et affiche la
navigation dans la barre latérale — aucune configuration supplémentaire
n'est nécessaire.

## Configuration (Google Sheets + mot de passe)

1. Renommez `.streamlit/secrets.toml.example` en `.streamlit/secrets.toml`
   (en local) — sur Streamlit Cloud, collez plutôt son contenu dans
   **Settings → Secrets** de votre application.
2. Complétez :
   - `spreadsheet_id` : l'ID de votre Google Sheet (dans l'URL, entre
     `/d/` et `/edit`).
   - `admin_password` : le mot de passe que **vous seul** connaîtrez pour
     ouvrir la page "Analyse".
   - `[gcp_service_account]` : les identifiants du compte de service
     Google (fichier JSON téléchargé depuis Google Cloud Console).
3. Dans votre Google Sheet, créez deux feuilles nommées exactement
   `Clients` et `Vendeurs`, et partagez le classeur avec l'adresse
   `client_email` de votre compte de service (rôle "Éditeur").

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déployer sur Streamlit Community Cloud

1. Poussez ce dossier sur un dépôt GitHub (n'incluez **pas** votre vrai
   `secrets.toml`).
2. Sur [share.streamlit.io](https://share.streamlit.io), créez une
   nouvelle application en pointant sur `app.py`.
3. Ajoutez vos secrets dans **Settings → Secrets** (contenu identique à
   `secrets.toml.example`, complété avec vos vraies valeurs).

## Page Analyse

La page `📊 Analyse` est verrouillée par mot de passe (`admin_password`
dans les secrets). Elle génère automatiquement :
- le nombre total de réponses et la date de la dernière réponse,
- un graphique en barres pour chaque question à choix (y compris les
  questions à choix multiples),
- un tableau des données brutes, exportable en CSV.

Ce dashboard s'adapte automatiquement aux colonnes de votre feuille
Google Sheets : vous n'avez rien à reconfigurer si l'ordre des questions
change légèrement.
