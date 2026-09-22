"""
app.py
------
Application unique regroupant l'accueil, le questionnaire client,
le questionnaire vendeur et l'espace d'analyse sécurisé.
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime

# ===========================================================================
# 1. DESIGN ET STYLES CSS (Fonctions utilitaires)
# ===========================================================================

PRIMARY_COLOR = "#0F5C4C"   # Vert profond
ACCENT_COLOR = "#E8871E"    # Orange cuivré
DARK_COLOR = "#12251F"
BG_COLOR = "#F7F6F2"
MUTED_TEXT = "#5B6763"


def inject_css():
    """Injecte le style CSS personnalisé dans l'application."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background-color: {BG_COLOR};
        }}

        h1, h2, h3, h4 {{
            font-family: 'Poppins', sans-serif;
            color: {DARK_COLOR};
        }}

        p, span, label, .stMarkdown {{
            color: {DARK_COLOR};
        }}

        .stProgress > div > div > div > div {{
            background-color: {ACCENT_COLOR};
        }}

        .stButton > button {{
            border-radius: 10px;
            border: 1px solid transparent;
            padding: 0.55rem 1.4rem;
            font-weight: 600;
            transition: all 0.15s ease-in-out;
        }}
        .stButton > button[kind="primary"] {{
            background-color: {PRIMARY_COLOR};
            color: white;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: {DARK_COLOR};
            color: white;
        }}
        .stButton > button:not([kind="primary"]) {{
            background-color: white;
            color: {PRIMARY_COLOR};
            border: 1px solid {PRIMARY_COLOR};
        }}
        .stButton > button:not([kind="primary"]):hover {{
            background-color: #EAF3F0;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
            box-shadow: 0 1px 3px rgba(18, 37, 31, 0.06);
        }}

        div[data-testid="stMetric"] {{
            background-color: white;
            border: 1px solid #E7E5DE;
            border-radius: 14px;
            padding: 1rem;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {DARK_COLOR};
        }}
        section[data-testid="stSidebar"] * {{
            color: #F1F5F3 !important;
        }}

        footer {{visibility: hidden;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(
        f"""
        <div style="padding: 0.5rem 0 1.2rem 0;">
            <h2 style="margin-bottom:0.1rem;">{icon} {title}</h2>
            <p style="color:{MUTED_TEXT}; margin-top:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# 2. GESTION DE LA BASE DE DONNÉES GOOGLE SHEETS
# ===========================================================================

class DatabaseManager:
    """Classe chargée des interactions avec Google Sheets API."""

    @staticmethod
    @st.cache_resource
    def get_client():
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        return gspread.authorize(credentials)

    @classmethod
    def save_row(cls, sheet_name: str, row_data: list) -> bool:
        try:
            client = cls.get_client()
            sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
            sheet.append_row(row_data)
            return True
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement : {e}")
            return False

    @classmethod
    @st.cache_data(ttl=60)
    def load_data(cls, sheet_name: str) -> pd.DataFrame:
        try:
            client = cls.get_client()
            sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
            return pd.DataFrame(sheet.get_all_records())
        except Exception:
            return pd.DataFrame()


# ===========================================================================
# 3. COMPOSANTS DE FORMULAIRES (Classes Questionnaire)
# ===========================================================================

class ClientQuestionnaire:
    """Gestion du parcours et des questions du profil Client."""

    TOTAL_STEPS = 4

    @classmethod
    def render(cls):
        page_header("Questionnaire Client", "Vos habitudes d'achat en ligne en Zambie", "🛍️")

        if st.session_state.get("client_excluded", False):
            st.info("Merci pour votre temps ! Cette étude concerne uniquement les personnes résidant en Zambie.")
            if st.button("↩️ Retour au choix du profil"):
                st.session_state.current_page = "Home"
                st.session_state.client_excluded = False
                st.rerun()
            return

        if st.session_state.get("client_done", False):
            st.balloons()
            st.success("✅ Merci ! Vos réponses ont été enregistrées avec succès.")
            if st.button("↩️ Retour à l'accueil"):
                st.session_state.client_step = 1
                st.session_state.client_answers = {}
                st.session_state.client_done = False
                st.session_state.current_page = "Home"
                st.rerun()
            return

        step = st.session_state.get("client_step", 1)
        st.progress(step / cls.TOTAL_STEPS, text=f"Étape {step} sur {cls.TOTAL_STEPS}")
        st.write("")

        if step == 1:
            with st.container(border=True):
                st.subheader("Section 1 — Vérification du répondant")
                q1 = st.radio("1. Vivez-vous actuellement en Zambie ? *", ["Oui", "Non"], horizontal=True)
                q2 = st.selectbox("2. Dans quelle ville vivez-vous actuellement ?", ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"])
                q3 = st.selectbox("3. Dans quelle tranche d'âge êtes-vous ?", ["Moins de 18 ans", "18–24 ans", "25–34 ans", "35–44 ans", "45 ans ou plus"])
                q4 = st.selectbox("4. Quel est votre statut actuel ?", ["Étudiant(e)", "Salarié(e)", "Entrepreneur(e) / indépendant(e)", "Sans emploi", "Autre"])

            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                if q1 == "Non":
                    st.session_state.client_excluded = True
                else:
                    st.session_state.client_answers.update({"q1": q1, "q2": q2, "q3": q3, "q4": q4})
                    st.session_state.client_step = 2
                st.rerun()

        elif step == 2:
            with st.container(border=True):
                st.subheader("Section 2 — Habitudes d'achat réelles")
                q5 = st.radio("5. Au cours des 3 derniers mois, avez-vous acheté un produit en ligne ?", ["Oui", "Non"], horizontal=True)
                q6 = st.text_input("6. Si oui, quel a été votre dernier achat en ligne ?", placeholder="Ex : vêtements, téléphone...")
                q7 = st.selectbox("7. Où avez-vous effectué cet achat ?", ["WhatsApp", "Facebook", "Instagram", "Site Internet", "Application", "Autre"])
                q8 = st.selectbox("8. Comment avez-vous découvert le produit ?", ["Réseaux sociaux", "Proche", "Recherche Internet", "Publicité", "Autre"])
                q9 = st.selectbox("9. Comment avez-vous payé ?", ["Mobile money", "Carte bancaire", "Virement", "Paiement à la livraison", "Autre"])
                q10 = st.selectbox("10. Comment avez-vous reçu votre commande ?", ["Livraison à domicile", "Livraison travail", "Retrait boutique", "Autre"])
                q11 = st.selectbox("11. Combien avez-vous dépensé environ ?", ["Moins de 100 ZMW", "100–300 ZMW", "301–500 ZMW", "501–1 000 ZMW", "Plus de 1 000 ZMW"])

            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.client_step = 1
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡️", type="primary", use_container_width=True):
                    st.session_state.client_answers.update({"q5": q5, "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10, "q11": q11})
                    st.session_state.client_step = 3
                    st.rerun()

        elif step == 3:
            with st.container(border=True):
                st.subheader("Section 3 — Problèmes rencontrés")
                q12 = st.radio("12. Avez-vous déjà rencontré un problème lors d'un achat en ligne ?", ["Oui", "Non"], horizontal=True)
                q13 = st.multiselect("13. Si oui, quel problème avez-vous rencontré ?", [
                    "Produit différent de la photo", "Produit jamais reçu", "Retard de livraison",
                    "Vendeur malhonnête", "Frais de livraison trop élevés", "Autre"
                ])
                q14 = st.multiselect("14. Qu'est-ce qui vous empêche le plus d'acheter en ligne ?", [
                    "Manque de confiance", "Peur de perdre l'argent", "Préférence pour voir le produit", "Frais de livraison élevés", "Autre"
                ])

            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.client_step = 2
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡️", type="primary", use_container_width=True):
                    st.session_state.client_answers.update({"q12": q12, "q13": ", ".join(q13), "q14": ", ".join(q14)})
                    st.session_state.client_step = 4
                    st.rerun()

        elif step == 4:
            with st.container(border=True):
                st.subheader("Section 4 — Concept Marketplace")
                q15 = st.selectbox("15. Seriez-vous intéressé(e) par une application dédiée ?", ["Très intéressé(e)", "Assez intéressé(e)", "Peu intéressé(e)", "Pas du tout"])
                q16 = st.multiselect("16. Services importants (max 3)", ["Vendeurs vérifiés", "Paiement sécurisé", "Livraison à domicile", "Comparateur de prix", "Service client"], max_selections=3)
                q17 = st.selectbox("17. Raison principale d'utilisation ?", ["Plus de sécurité", "Plus de choix", "Prix intéressants", "Livraison pratique"])
                q18 = st.radio("18. Prêt(e) à payer des frais de livraison ?", ["Oui", "Non", "Selon le montant"], horizontal=True)
                q19 = st.selectbox("19. Montant raisonnable de livraison ?", ["Moins de 10 ZMW", "10–20 ZMW", "21–30 ZMW", "31–50 ZMW", "Plus de 50 ZMW"])
                q20 = st.multiselect("20. Ce qui donnerait le plus confiance ?", ["Avis clients", "Vendeurs vérifiés", "Paiement à la livraison", "Garantie remboursement"], max_selections=3)
                q21 = st.text_input("21. Produit particulièrement recherché ?")
                q22 = st.text_area("22. Suggestions ?")
                q23 = st.selectbox("23. Comment avez-vous reçu ce questionnaire ?", ["WhatsApp", "Facebook", "Instagram", "Groupe", "Autre"])

            col_back, col_submit = st.columns(2)
            with col_back:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.client_step = 3
                    st.rerun()
            with col_submit:
                if st.button("Soumettre 🚀", type="primary", use_container_width=True):
                    st.session_state.client_answers.update({
                        "q15": q15, "q16": ", ".join(q16), "q17": q17, "q18": q18, "q19": q19,
                        "q20": ", ".join(q20), "q21": q21, "q22": q22, "q23": q23
                    })
                    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(st.session_state.client_answers.values())
                    with st.spinner("Enregistrement..."):
                        if DatabaseManager.save_row("Clients", row):
                            st.session_state.client_done = True
                            st.rerun()


class VendorQuestionnaire:
    """Gestion du parcours et des questions du profil Vendeur."""

    TOTAL_STEPS = 3

    @classmethod
    def render(cls):
        page_header("Questionnaire Vendeur", "Vos besoins en tant que commerçant en Zambie", "🏬")

        if st.session_state.get("vendeur_excluded", False):
            st.info("Merci pour votre temps ! Cette étude concerne uniquement les entreprises basées en Zambie.")
            if st.button("↩️ Retour au choix du profil"):
                st.session_state.current_page = "Home"
                st.session_state.vendeur_excluded = False
                st.rerun()
            return

        if st.session_state.get("vendeur_done", False):
            st.balloons()
            st.success("✅ Merci ! Vos réponses vendeur ont été enregistrées avec succès.")
            if st.button("↩️ Retour à l'accueil"):
                st.session_state.vendeur_step = 1
                st.session_state.vendeur_answers = {}
                st.session_state.vendeur_done = False
                st.session_state.current_page = "Home"
                st.rerun()
            return

        step = st.session_state.get("vendeur_step", 1)
        st.progress(step / cls.TOTAL_STEPS, text=f"Étape {step} sur {cls.TOTAL_STEPS}")
        st.write("")

        if step == 1:
            with st.container(border=True):
                st.subheader("Section 1 — Vérification")
                vq1 = st.radio("1. Votre activité est-elle située en Zambie ? *", ["Oui", "Non"], horizontal=True)
                vq2 = st.selectbox("2. Ville principale ?", ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Autre"])
                vq3 = st.selectbox("3. Ancienneté ?", ["Moins de 6 mois", "6 mois à 1 an", "1–3 ans", "Plus de 3 ans"])

            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                if vq1 == "Non":
                    st.session_state.vendeur_excluded = True
                else:
                    st.session_state.vendeur_answers.update({"vq1": vq1, "vq2": vq2, "vq3": vq3})
                    st.session_state.vendeur_step = 2
                st.rerun()

        elif step == 2:
            with st.container(border=True):
                st.subheader("Section 2 — Activité commerciale")
                vq4 = st.multiselect("4. Produits vendus ?", ["Vêtements", "Chaussures", "Électronique", "Maison", "Nourriture", "Autre"])
                vq5 = st.multiselect("5. Canaux actuels de vente ?", ["Boutique physique", "WhatsApp", "Facebook", "Instagram", "Autre"])
                vq6 = st.radio("6. Commandes en ligne actuelles ?", ["Oui, régulièrement", "Oui, occasionnellement", "Non"])
                vq7 = st.selectbox("7. Volume de commandes mensuel ?", ["0", "1–10", "11–30", "31–100", "Plus de 100"])
                vq8 = st.selectbox("8. Principal obstacle en ligne ?", ["Trouver des clients", "Recevoir les paiements", "Livraison", "Méfiance des clients"])

            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.vendeur_step = 1
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡️", type="primary", use_container_width=True):
                    st.session_state.vendeur_answers.update({
                        "vq4": ", ".join(vq4), "vq5": ", ".join(vq5), "vq6": vq6, "vq7": vq7, "vq8": vq8
                    })
                    st.session_state.vendeur_step = 3
                    st.rerun()

        elif step == 3:
            with st.container(border=True):
                st.subheader("Section 3 — Intérêt pour le projet")
                vq9 = st.selectbox("9. Intérêt pour une application dédiée ?", ["Très intéressé(e)", "Assez intéressé(e)", "Peu intéressé(e)", "Pas du tout"])
                vq10 = st.multiselect("10. Services les plus utiles (max 3)", ["Trouver des clients", "Paiement sécurisé", "Livraison organisée", "Publicité"], max_selections=3)
                vq11 = st.radio("11. Prêt à payer une commission par vente ?", ["Oui", "Non", "Selon le %"])
                vq12 = st.selectbox("12. Modèle préféré ?", ["Commission par vente", "Abonnement mensuel", "Mixte", "Incertain"])
                vq13 = st.selectbox("13. Pourcentage raisonnable ?", ["Moins de 5 %", "5–10 %", "11–15 %", "Plus de 15 %"])
                vq14 = st.radio("14. Paiement sécurisé avec versement à la livraison ?", ["Oui", "Non", "Selon conditions"])
                vq15 = st.radio("15. Vérification d'identité acceptée ?", ["Oui", "Non", "Selon informations"])
                vq16 = st.radio("16. Service de livraison intégré ?", ["Oui", "Non", "Selon le prix"])
                vq17 = st.multiselect("17. Freins principaux ?", ["Commissions", "Manque de clients", "Arnaques", "Complexité"])
                vq18 = st.text_input("18. Catégories les plus demandées selon vous ?")
                vq19 = st.text_area("19. Qu'est-ce qui vous convaincrait d'utiliser l'application ?")
                vq20 = st.selectbox("20. Origine du questionnaire ?", ["WhatsApp", "Facebook", "Instagram", "Groupe", "Autre"])

            col_back, col_submit = st.columns(2)
            with col_back:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.vendeur_step = 2
                    st.rerun()
            with col_submit:
                if st.button("Soumettre 🚀", type="primary", use_container_width=True):
                    st.session_state.vendeur_answers.update({
                        "vq9": vq9, "vq10": ", ".join(vq10), "vq11": vq11, "vq12": vq12, "vq13": vq13,
                        "vq14": vq14, "vq15": vq15, "vq16": vq16, "vq17": ", ".join(vq17), "vq18": vq18,
                        "vq19": vq19, "vq20": vq20
                    })
                    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(st.session_state.vendeur_answers.values())
                    with st.spinner("Enregistrement..."):
                        if DatabaseManager.save_row("Vendeurs", row):
                            st.session_state.vendeur_done = True
                            st.rerun()


# ===========================================================================
# 4. DASHBOARD & VISUALISATION (Espace d'analyse)
# ===========================================================================

class AnalyticsDashboard:
    """Gestion du tableau de bord privé d'analyse des données."""

    @classmethod
    def render(cls):
        page_header("Analyse en temps réel", "Résultats consolidés de l'étude de marché", "📊")

        if not st.session_state.get("authenticated", False):
            st.warning("🔒 Cet espace est réservé à l'administration.")
            pwd = st.text_input("Mot de passe d'accès :", type="password")
            if st.button("Connexion", type="primary"):
                admin_pwd = st.secrets.get("admin_password", "admin123")
                if pwd == admin_pwd:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")
            return

        if st.button("🔓 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()

        st.divider()
        tab_clients, tab_vendeurs = st.tabs(["👥 Réponses Clients", "🏬 Réponses Vendeurs"])

        with tab_clients:
            df_c = DatabaseManager.load_data("Clients")
            cls._render_tab_content(df_c, "Clients")

        with tab_vendeurs:
            df_v = DatabaseManager.load_data("Vendeurs")
            cls._render_tab_content(df_v, "Vendeurs")

    @classmethod
    def _render_tab_content(cls, df: pd.DataFrame, label: str):
        if df.empty:
            st.info(f"Aucune réponse {label.lower()} enregistrée pour le moment.")
            return

        c1, c2, c3 = st.columns(3)
        c1.metric("Total réponses", len(df))
        c2.metric("Colonnes", len(df.columns))
        c3.metric("Statut", "Actif")

        with st.expander("📄 Voir les données brutes"):
            st.dataframe(df, use_container_width=True)

        st.subheader("Graphiques automatiques")
        cols = st.columns(2)
        idx = 0
        for col in df.columns[1:]:
            series = df[col].astype(str).str.split(",").explode().str.strip()
            series = series[series != ""]
            if series.nunique() > 0 and series.nunique() <= 12:
                counts = series.value_counts().reset_index()
                counts.columns = [col, "Nombre"]
                fig = px.bar(counts, x="Nombre", y=col, orientation="h", color_discrete_sequence=[PRIMARY_COLOR])
                fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
                with cols[idx % 2]:
                    st.plotly_chart(fig, use_container_width=True)
                idx += 1


# ===========================================================================
# 5. PAGE D'ACCUEIL & NAVIGATION PRINCIPALE
# ===========================================================================

def render_home():
    """Affiche la page d'accueil avec les cartes de sélection du profil."""
    st.markdown(
        f"""
        <div style="text-align:center; padding: 2rem 1rem 1rem 1rem;">
            <div style="font-size:2.8rem;">🇿🇲</div>
            <h1 style="margin-bottom:0;">Étude de Marché</h1>
            <h3 style="color:{ACCENT_COLOR}; font-weight:600; margin-top:0.2rem;">
                Projet Marketplace — Zambie
            </h3>
            <p style="max-width:640px; margin:1rem auto; font-size:1.05rem; color:#4b5563;">
                Nous préparons le lancement d'une marketplace connectant vendeurs
                et clients en Zambie. Choisissez votre profil pour commencer le questionnaire anonyme.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.markdown("### 🛍️ Je suis Client / Acheteur")
            st.write("Vos habitudes d'achat en ligne et vos attentes.")
            if st.button("Commencer le questionnaire Client ➡️", use_container_width=True, type="primary"):
                st.session_state.current_page = "Client"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 🏬 Je suis Vendeur / Commerçant")
            st.write("Vos besoins commerciaux et les conditions pour vendre en ligne.")
            if st.button("Commencer le questionnaire Vendeur ➡️", use_container_width=True, type="primary"):
                st.session_state.current_page = "Vendeur"
                st.rerun()


def main():
    """Point d'entrée principal de l'application."""
    st.set_page_config(
        page_title="Marketplace Zambia — Étude de Marché",
        page_icon="🇿🇲",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    inject_css()

    # Initialisation de l'état de navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    # Menu de navigation latéral
    with st.sidebar:
        st.title("🇿🇲 Menu")
        selection = st.radio(
            "Navigation :",
            ["Accueil", "Questionnaire Client", "Questionnaire Vendeur", "Espace Analyse"],
            index=["Home", "Client", "Vendeur", "Analytics"].index(st.session_state.current_page)
            if st.session_state.current_page in ["Home", "Client", "Vendeur", "Analytics"] else 0
        )

        # Synchronisation de la sélection radio avec l'état global
        page_mapping = {
            "Accueil": "Home",
            "Questionnaire Client": "Client",
            "Questionnaire Vendeur": "Vendeur",
            "Espace Analyse": "Analytics"
        }
        if page_mapping[selection] != st.session_state.current_page:
            st.session_state.current_page = page_mapping[selection]
            st.rerun()

    # Routage de l'affichage
    if st.session_state.current_page == "Home":
        render_home()
    elif st.session_state.current_page == "Client":
        ClientQuestionnaire.render()
    elif st.session_state.current_page == "Vendeur":
        VendorQuestionnaire.render()
    elif st.session_state.current_page == "Analytics":
        AnalyticsDashboard.render()


if __name__ == "__main__":
    main()
