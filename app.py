"""
app.py
------
Étude de Marché — Marketplace Zambie
Application Streamlit en fichier unique, structurée en classes et fonctions.
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime


# ===========================================================================
# 1. CONFIGURATION VISUELLE
# ===========================================================================
class Config:
    """Constantes visuelles et de configuration."""
    PRIMARY_COLOR = "#0F5C4C"
    ACCENT_COLOR  = "#E8871E"
    DARK_COLOR    = "#12251F"
    BG_COLOR      = "#F7F6F2"
    MUTED_TEXT    = "#5B6763"

    APP_TITLE = "Étude de Marché — Marketplace Zambie"
    APP_ICON  = "🇿🇲"

    CLIENT_TOTAL_STEPS  = 4
    VENDEUR_TOTAL_STEPS = 3


# ===========================================================================
# 2. STYLE CSS
# ===========================================================================
class StyleManager:
    """Gère l'injection du CSS global."""

    @staticmethod
    def inject_css():
        c = Config
        st.markdown(
            f"""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

            html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
            .stApp {{ background-color: {c.BG_COLOR}; }}
            h1, h2, h3, h4 {{ font-family: 'Poppins', sans-serif; color: {c.DARK_COLOR}; }}
            p, span, label, .stMarkdown {{ color: {c.DARK_COLOR}; }}

            .stProgress > div > div > div > div {{ background-color: {c.ACCENT_COLOR}; }}

            .stButton > button {{
                border-radius: 10px;
                border: 1px solid transparent;
                padding: 0.55rem 1.4rem;
                font-weight: 600;
                transition: all 0.15s ease-in-out;
            }}
            .stButton > button[kind="primary"] {{
                background-color: {c.PRIMARY_COLOR};
                color: white;
            }}
            .stButton > button[kind="primary"]:hover {{
                background-color: {c.DARK_COLOR};
                color: white;
            }}
            .stButton > button:not([kind="primary"]) {{
                background-color: white;
                color: {c.PRIMARY_COLOR};
                border: 1px solid {c.PRIMARY_COLOR};
            }}
            .stButton > button:not([kind="primary"]):hover {{ background-color: #EAF3F0; }}

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

            section[data-testid="stSidebar"] {{ background-color: {c.DARK_COLOR}; }}
            section[data-testid="stSidebar"] * {{ color: #F1F5F3 !important; }}

            footer {{ visibility: hidden; }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# ===========================================================================
# 3. HELPERS UI
# ===========================================================================
class UI:
    """Helpers d'interface réutilisables."""

    @staticmethod
    def page_header(title: str, subtitle: str = "", icon: str = ""):
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1.2rem 0;">
                <h2 style="margin-bottom:0.1rem;">{icon} {title}</h2>
                <p style="color:{Config.MUTED_TEXT}; margin-top:0;">{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def thank_you_and_stop(message: str = "Merci pour votre temps !"):
        st.info(message)
        if st.button("↩️ Retour à l'accueil"):
            st.session_state["page"] = "home"
            st.rerun()
        st.stop()


# ===========================================================================
# 4. ACCÈS GOOGLE SHEETS
# ===========================================================================
class SheetRepository:
    """Encapsule l'accès Google Sheets."""

    @staticmethod
    @st.cache_resource
    def _get_client():
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        return gspread.authorize(credentials)

    @classmethod
    def save(cls, sheet_name: str, row_data: list) -> bool:
        try:
            client = cls._get_client()
            sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
            sheet.append_row(row_data)
            return True
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement : {e}")
            return False

    @staticmethod
    @st.cache_data(ttl=60)
    def load(sheet_name: str) -> pd.DataFrame:
        try:
            client = SheetRepository._get_client()
            sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
            return pd.DataFrame(sheet.get_all_records())
        except Exception:
            return pd.DataFrame()


# ===========================================================================
# 5. BASE COMMUNE AUX QUESTIONNAIRES
# ===========================================================================
class QuestionnaireBase:
    """
    Classe de base pour les questionnaires.
    Gère : état en session, filtre Q1, progression, soumission.
    """

    KEY_PREFIX = "base"
    TOTAL_STEPS = 1
    EXCLUDED_MESSAGE = "Merci pour votre temps !"
    SHEET_NAME = ""

    # ---------- État ----------
    @classmethod
    def state_key(cls, name: str) -> str:
        return f"{cls.KEY_PREFIX}_{name}"

    @classmethod
    def init_state(cls):
        defaults = {"step": 1, "answers": {}, "excluded": False, "done": False}
        for k, v in defaults.items():
            key = cls.state_key(k)
            if key not in st.session_state:
                st.session_state[key] = v

    @classmethod
    def get(cls, name: str):
        return st.session_state[cls.state_key(name)]

    @classmethod
    def set(cls, name: str, value):
        st.session_state[cls.state_key(name)] = value

    @classmethod
    def reset_state(cls):
        for name in ("step", "answers", "excluded", "done"):
            key = cls.state_key(name)
            if key in st.session_state:
                del st.session_state[key]

    # ---------- Helpers ----------
    @classmethod
    def update_answers(cls, data: dict):
        answers = cls.get("answers")
        answers.update(data)
        cls.set("answers", answers)

    @classmethod
    def next_step(cls):
        cls.set("step", cls.get("step") + 1)

    @classmethod
    def prev_step(cls):
        cls.set("step", cls.get("step") - 1)

    @classmethod
    def mark_done(cls):
        cls.set("done", True)

    @classmethod
    def mark_excluded(cls):
        cls.set("excluded", True)

    # ---------- Soumission ----------
    @classmethod
    def submit(cls):
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(cls.get("answers").values())
        with st.spinner("Enregistrement en cours…"):
            success = SheetRepository.save(cls.SHEET_NAME, row)
        if success:
            cls.mark_done()
            st.rerun()

    # ---------- Rendu ----------
    @classmethod
    def render_progress(cls):
        step = cls.get("step")
        st.progress(step / cls.TOTAL_STEPS, text=f"Étape {step} sur {cls.TOTAL_STEPS}")
        st.write("")

    @classmethod
    def render_excluded(cls):
        UI.thank_you_and_stop(cls.EXCLUDED_MESSAGE)

    @classmethod
    def render_done(cls):
        st.balloons()
        st.success("✅ Merci ! Vos réponses ont été enregistrées avec succès.")
        if st.button("↩️ Retour à l'accueil"):
            cls.reset_state()
            st.session_state["page"] = "home"
            st.rerun()
        st.stop()

    @classmethod
    def render_back_button(cls, col, target_step: int):
        with col:
            if st.button("⬅️ Précédent", use_container_width=True):
                cls.set("step", target_step)
                st.rerun()

    # ---------- À surcharger ----------
    @classmethod
    def render_step(cls):
        raise NotImplementedError

    @classmethod
    def run(cls):
        cls.init_state()

        if cls.get("excluded"):
            cls.render_excluded()

        if cls.get("done"):
            cls.render_done()

        cls.render_progress()
        cls.render_step()


# ===========================================================================
# 6. QUESTIONNAIRE CLIENT
# ===========================================================================
class ClientQuestionnaire(QuestionnaireBase):
    KEY_PREFIX = "client"
    TOTAL_STEPS = Config.CLIENT_TOTAL_STEPS
    SHEET_NAME = "Clients"
    EXCLUDED_MESSAGE = (
        "Merci pour votre temps ! Cette étude concerne uniquement les "
        "personnes résidant actuellement en Zambie."
    )

    # --- ÉTAPE 1 : Vérification (Q1 = filtre) ---
    @classmethod
    def render_step_1(cls):
        with st.container(border=True):
            st.subheader("Section 1 — Vérification du répondant")

            q1 = st.radio(
                "1. Vivez-vous actuellement en Zambie ? *",
                ["Oui", "Non"],
                horizontal=True,
                key="c_q1",
            )

            # 🔑 FILTRE : si Non → stop immédiat (le reste n'est jamais affiché)
            if q1 == "Non":
                cls.mark_excluded()
                st.rerun()

            q2 = st.selectbox(
                "2. Dans quelle ville vivez-vous actuellement ?",
                ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"],
                key="c_q2",
            )
            q3 = st.selectbox(
                "3. Dans quelle tranche d'âge êtes-vous ?",
                ["Moins de 18 ans", "18–24 ans", "25–34 ans", "35–44 ans", "45 ans ou plus"],
                key="c_q3",
            )
            q4 = st.selectbox(
                "4. Quel est votre statut actuel ?",
                ["Étudiant(e)", "Salarié(e)", "Entrepreneur(e) / indépendant(e)",
                 "Sans emploi", "Autre"],
                key="c_q4",
            )

        _, col_next = st.columns([1, 1])
        with col_next:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                cls.update_answers({"q1": q1, "q2": q2, "q3": q3, "q4": q4})
                cls.next_step()
                st.rerun()

    # --- ÉTAPE 2 : Habitudes d'achat ---
    @classmethod
    def render_step_2(cls):
        with st.container(border=True):
            st.subheader("Section 2 — Habitudes d'achat réelles")
            q5 = st.radio("5. Au cours des 3 derniers mois, avez-vous acheté un produit en ligne ?",
                          ["Oui", "Non"], horizontal=True, key="c_q5")
            q6 = st.text_input("6. Si oui, quel a été votre dernier achat en ligne ?",
                               placeholder="Ex : vêtements, chaussures, téléphone…", key="c_q6")
            q7 = st.selectbox("7. Où avez-vous effectué cet achat ?",
                              ["WhatsApp", "Facebook", "Instagram", "Site Internet",
                               "Application de shopping", "Autre"], key="c_q7")
            q8 = st.selectbox("8. Comment avez-vous découvert le produit ?",
                              ["Publication sur les réseaux sociaux", "Recommandation d'un proche",
                               "Recherche sur Internet", "Publicité",
                               "Je connaissais déjà le vendeur", "Autre"], key="c_q8")
            q9 = st.selectbox("9. Comment avez-vous payé ?",
                              ["Mobile money", "Carte bancaire", "Virement bancaire",
                               "Paiement à la livraison", "Paiement à la collecte", "Autre"],
                              key="c_q9")
            q10 = st.selectbox("10. Comment avez-vous reçu votre commande ?",
                               ["Livraison à domicile", "Livraison sur mon lieu de travail",
                                "Livraison à un autre endroit", "Retrait en boutique",
                                "Je suis allé(e) chercher le produit chez le vendeur", "Autre"],
                               key="c_q10")
            q11 = st.selectbox("11. Combien avez-vous dépensé environ pour ce dernier achat ?",
                               ["Moins de 100 ZMW", "100–300 ZMW", "301–500 ZMW",
                                "501–1 000 ZMW", "Plus de 1 000 ZMW"], key="c_q11")

        col_back, col_next = st.columns(2)
        cls.render_back_button(col_back, target_step=1)
        with col_next:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                cls.update_answers({"q5": q5, "q6": q6, "q7": q7, "q8": q8,
                                    "q9": q9, "q10": q10, "q11": q11})
                cls.next_step()
                st.rerun()

    # --- ÉTAPE 3 : Problèmes ---
    @classmethod
    def render_step_3(cls):
        with st.container(border=True):
            st.subheader("Section 3 — Problèmes rencontrés")
            q12 = st.radio("12. Avez-vous déjà rencontré un problème lors d'un achat en ligne ?",
                           ["Oui", "Non"], horizontal=True, key="c_q12")
            q13 = st.multiselect("13. Si oui, quel problème avez-vous rencontré ?", [
                "Produit différent de la photo", "Produit jamais reçu", "Retard de livraison",
                "Vendeur malhonnête", "Difficulté à récupérer mon argent",
                "Frais de livraison trop élevés", "Produit de mauvaise qualité",
                "Difficulté à contacter le vendeur", "Autre"
            ], key="c_q13")
            q14 = st.multiselect("14. Qu'est-ce qui vous empêche le plus d'acheter en ligne ?", [
                "Je ne fais pas confiance aux vendeurs", "J'ai peur de perdre mon argent",
                "Je préfère voir le produit avant d'acheter",
                "Les frais de livraison sont trop élevés",
                "Les délais de livraison sont trop longs",
                "Je ne connais pas suffisamment les plateformes disponibles",
                "Je préfère acheter directement en boutique",
                "Je n'ai pas encore eu besoin d'acheter en ligne", "Autre"
            ], key="c_q14")

        col_back, col_next = st.columns(2)
        cls.render_back_button(col_back, target_step=2)
        with col_next:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                cls.update_answers({"q12": q12, "q13": ", ".join(q13), "q14": ", ".join(q14)})
                cls.next_step()
                st.rerun()

    # --- ÉTAPE 4 : Concept Marketplace ---
    @classmethod
    def render_step_4(cls):
        st.info(
            "💡 Imaginez une application permettant de découvrir des produits, "
            "comparer les prix, commander auprès de vendeurs locaux, payer de "
            "manière sécurisée et suivre sa livraison."
        )
        with st.container(border=True):
            st.subheader("Section 4 — Concept Marketplace")
            q15 = st.selectbox("15. Si une telle application existait, seriez-vous intéressé(e) ?",
                               ["Très intéressé(e)", "Assez intéressé(e)",
                                "Peu intéressé(e)", "Pas du tout intéressé(e)"], key="c_q15")
            q16 = st.multiselect("16. Quels services seraient les plus importants pour vous ? (max 3)", [
                "Vendeurs vérifiés", "Paiement sécurisé", "Livraison à domicile",
                "Possibilité de comparer les prix", "Retours et remboursements",
                "Service client", "Promotions", "Suivi de commande", "Avis des autres clients"
            ], max_selections=3, key="c_q16")
            q17 = st.selectbox("17. Principale raison d'utiliser cette application ?",
                               ["Plus de sécurité", "Plus de choix", "Prix plus intéressants",
                                "Livraison plus pratique", "Meilleure qualité des produits",
                                "Promotions", "Autre"], key="c_q17")
            q18 = st.radio("18. Prêt(e) à payer des frais de livraison ?",
                           ["Oui", "Non", "Cela dépend du montant"],
                           horizontal=True, key="c_q18")
            q19 = st.selectbox("19. Montant raisonnable pour une livraison locale ?",
                               ["Moins de 10 ZMW", "10–20 ZMW", "21–30 ZMW",
                                "31–50 ZMW", "Plus de 50 ZMW", "Je ne sais pas"], key="c_q19")
            q20 = st.multiselect("20. Qu'est-ce qui vous ferait confiance ? (max 3)", [
                "Voir les avis des clients", "Savoir que les vendeurs sont vérifiés",
                "Pouvoir payer à la livraison", "Avoir une garantie de remboursement",
                "Voir les produits dans une boutique physique",
                "Pouvoir contacter facilement le service client", "Autre"
            ], max_selections=3, key="c_q20")
            q21 = st.text_input("21. Quel produit aimeriez-vous trouver sur une telle application ?",
                                key="c_q21")
            q22 = st.text_area("22. Suggestion pour améliorer les achats en ligne en Zambie ?",
                               key="c_q22")
            q23 = st.selectbox("23. Comment avez-vous reçu ce questionnaire ?",
                               ["WhatsApp", "Facebook", "Instagram", "Groupe d'étudiants",
                                "Groupe professionnel", "Recommandation d'un proche", "Autre"],
                               key="c_q23")

        col_back, col_submit = st.columns(2)
        cls.render_back_button(col_back, target_step=3)
        with col_submit:
            if st.button("Soumettre mes réponses 🚀", type="primary", use_container_width=True):
                cls.update_answers({
                    "q15": q15, "q16": ", ".join(q16), "q17": q17, "q18": q18,
                    "q19": q19, "q20": ", ".join(q20), "q21": q21, "q22": q22, "q23": q23
                })
                cls.submit()

    @classmethod
    def render_step(cls):
        step = cls.get("step")
        {
            1: cls.render_step_1,
            2: cls.render_step_2,
            3: cls.render_step_3,
            4: cls.render_step_4,
        }[step]()


# ===========================================================================
# 7. QUESTIONNAIRE VENDEUR
# ===========================================================================
class VendeurQuestionnaire(QuestionnaireBase):
    KEY_PREFIX = "vendeur"
    TOTAL_STEPS = Config.VENDEUR_TOTAL_STEPS
    SHEET_NAME = "Vendeurs"
    EXCLUDED_MESSAGE = (
        "Merci pour votre temps ! Cette étude concerne uniquement les "
        "entreprises basées en Zambie."
    )

    # --- ÉTAPE 1 ---
    @classmethod
    def render_step_1(cls):
        with st.container(border=True):
            st.subheader("Section 1 — Vérification")
            vq1 = st.radio("1. Votre activité est-elle actuellement située en Zambie ? *",
                           ["Oui", "Non"], horizontal=True, key="v_q1")

            # 🔑 FILTRE : si Non → stop immédiat
            if vq1 == "Non":
                cls.mark_excluded()
                st.rerun()

            vq2 = st.selectbox("2. Dans quelle ville votre activité est-elle située ?",
                               ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"],
                               key="v_q2")
            vq3 = st.selectbox("3. Depuis combien de temps exercez-vous cette activité ?",
                               ["Moins de 6 mois", "6 mois à 1 an", "1–3 ans", "Plus de 3 ans"],
                               key="v_q3")

        _, col_next = st.columns([1, 1])
        with col_next:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                cls.update_answers({"vq1": vq1, "vq2": vq2, "vq3": vq3})
                cls.next_step()
                st.rerun()

    # --- ÉTAPE 2 ---
    @classmethod
    def render_step_2(cls):
        with st.container(border=True):
            st.subheader("Section 2 — Activité commerciale")
            vq4 = st.multiselect("4. Quels produits vendez-vous ?",
                                 ["Vêtements", "Chaussures", "Accessoires", "Produits de beauté",
                                  "Électronique", "Produits pour la maison",
                                  "Produits alimentaires", "Autre"], key="v_q4")
            vq5 = st.multiselect("5. Où vendez-vous principalement vos produits ?",
                                 ["Boutique physique", "WhatsApp", "Facebook", "Instagram",
                                  "Site Internet", "Marketplace", "Autre"], key="v_q5")
            vq6 = st.radio("6. Recevez-vous déjà des commandes en ligne ?",
                           ["Oui, régulièrement", "Oui, occasionnellement", "Non"], key="v_q6")
            vq7 = st.selectbox("7. Combien de commandes recevez-vous environ par mois ?",
                               ["0", "1–10", "11–30", "31–100", "Plus de 100"], key="v_q7")
            vq8 = st.selectbox("8. Principal problème lorsque vous vendez en ligne ?",
                               ["Trouver des clients", "Recevoir les paiements",
                                "Organiser la livraison", "Gérer les retours",
                                "Manque de confiance des clients", "Frais de publicité", "Autre"],
                               key="v_q8")

        col_back, col_next = st.columns(2)
        cls.render_back_button(col_back, target_step=1)
        with col_next:
            if st.button("Suivant ➡️", type="primary", use_container_width=True):
                cls.update_answers({"vq4": ", ".join(vq4), "vq5": ", ".join(vq5),
                                    "vq6": vq6, "vq7": vq7, "vq8": vq8})
                cls.next_step()
                st.rerun()

    # --- ÉTAPE 3 ---
    @classmethod
    def render_step_3(cls):
        with st.container(border=True):
            st.subheader("Section 3 — Intérêt pour le projet")
            vq9 = st.selectbox("9. Intéressé(e) par une application pour vendre à des clients zambiens ?",
                               ["Très intéressé(e)", "Assez intéressé(e)",
                                "Peu intéressé(e)", "Pas du tout intéressé(e)"], key="v_q9")
            vq10 = st.multiselect("10. Quels services seraient les plus utiles ? (max 3)", [
                "Trouver de nouveaux clients", "Recevoir des commandes", "Paiement sécurisé",
                "Livraison organisée", "Publicité de mes produits", "Gestion des stocks",
                "Gestion des commandes", "Protection contre les clients malhonnêtes", "Autre"
            ], max_selections=3, key="v_q10")
            vq11 = st.radio("11. Accepteriez-vous de payer une petite commission ?",
                            ["Oui", "Non", "Cela dépend du pourcentage"], key="v_q11")
            vq12 = st.selectbox("12. Quel modèle préférez-vous ?",
                                ["Commission uniquement sur les ventes", "Abonnement mensuel",
                                 "Commission + services optionnels", "Je ne sais pas encore"],
                                key="v_q12")
            vq13 = st.selectbox("13. Quel pourcentage de commission serait acceptable ?",
                                ["Moins de 5 %", "5–10 %", "11–15 %", "Plus de 15 %",
                                 "Je ne sais pas"], key="v_q13")
            vq14 = st.radio("14. Prêt(e) à utiliser un système de paiement sécurisé ?",
                            ["Oui", "Non", "Cela dépend des conditions"], key="v_q14")
            vq15 = st.radio("15. Accepteriez-vous de faire vérifier votre identité et activité ?",
                            ["Oui", "Non", "Cela dépend des informations demandées"], key="v_q15")
            vq16 = st.radio("16. Prêt(e) à utiliser un service de livraison de la plateforme ?",
                            ["Oui", "Non", "Cela dépend du prix"], key="v_q16")
            vq17 = st.multiselect("17. Qu'est-ce qui vous empêcherait de vendre sur une nouvelle marketplace ?",
                                  ["Les commissions", "Le manque de clients",
                                   "Les difficultés de paiement", "Les difficultés de livraison",
                                   "La peur des arnaques", "La complexité de l'application",
                                   "Autre"], key="v_q17")
            vq18 = st.text_input("18. Quelles catégories de produits sont les plus demandées en ligne en Zambie ?",
                                 key="v_q18")
            vq19 = st.text_area("19. Qu'est-ce qu'une marketplace devrait faire pour vous convaincre ?",
                                key="v_q19")
            vq20 = st.selectbox("20. Comment avez-vous reçu ce questionnaire ?",
                                ["WhatsApp", "Facebook", "Instagram", "Groupe de vendeurs",
                                 "Groupe professionnel", "Recommandation d'un proche", "Autre"],
                                key="v_q20")

        col_back, col_submit = st.columns(2)
        cls.render_back_button(col_back, target_step=2)
        with col_submit:
            if st.button("Soumettre mes réponses 🚀", type="primary", use_container_width=True):
                cls.update_answers({
                    "vq9": vq9, "vq10": ", ".join(vq10), "vq11": vq11, "vq12": vq12,
                    "vq13": vq13, "vq14": vq14, "vq15": vq15, "vq16": vq16,
                    "vq17": ", ".join(vq17), "vq18": vq18, "vq19": vq19, "vq20": vq20
                })
                cls.submit()

    @classmethod
    def render_step(cls):
        step = cls.get("step")
        {1: cls.render_step_1, 2: cls.render_step_2, 3: cls.render_step_3}[step]()


# ===========================================================================
# 8. DASHBOARD (ANALYSE)
# ===========================================================================
class Dashboard:
    """Tableau de bord admin protégé par mot de passe."""

    SESSION_KEY = "authenticated"

    @classmethod
    def is_authenticated(cls) -> bool:
        return st.session_state.get(cls.SESSION_KEY, False)

    @classmethod
    def login_form(cls):
        admin_password = st.secrets.get("admin_password", None)
        if admin_password is None:
            st.error(
                "⚠️ Aucun mot de passe n'est configuré. Ajoutez `admin_password` "
                "dans vos secrets Streamlit."
            )
            return
        with st.form("login_form"):
            pwd = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Se connecter", type="primary",
                                              use_container_width=True)
        if submitted:
            if pwd == admin_password:
                st.session_state[cls.SESSION_KEY] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")

    @staticmethod
    def render_overview(df: pd.DataFrame, label: str):
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Réponses {label}", len(df))

        timestamp_col = df.columns[0] if len(df.columns) > 0 else None
        last_date = "—"
        if timestamp_col is not None and len(df) > 0:
            try:
                parsed = pd.to_datetime(df[timestamp_col], errors="coerce")
                if parsed.notna().any():
                    last_date = parsed.max().strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
        col2.metric("Dernière réponse", last_date)
        col3.metric("Colonnes collectées", len(df.columns))

        with st.expander("📄 Voir les données brutes"):
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "⬇️ Télécharger en CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name=f"{label.lower()}_reponses.csv",
                mime="text/csv",
            )

    @staticmethod
    def render_auto_charts(df: pd.DataFrame, max_unique: int = 12, max_charts: int = 12):
        if df.empty:
            st.info("Aucune donnée disponible pour le moment.")
            return
        chart_count = 0
        cols = st.columns(2)
        col_idx = 0
        for col in df.columns:
            if chart_count >= max_charts:
                break
            series = df[col].astype(str).replace({"nan": "", "None": ""})
            series = series[series.str.strip() != ""]
            if series.empty:
                continue
            avg_len = series.str.len().mean()
            exploded = series.str.split(",").explode().str.strip()
            exploded = exploded[exploded != ""]
            unique_vals = exploded.nunique()
            if unique_vals == 0 or unique_vals > max_unique or avg_len > 45:
                continue
            if unique_vals == len(series):
                continue
            counts = exploded.value_counts().reset_index()
            counts.columns = [col, "Réponses"]
            fig = px.bar(
                counts.sort_values("Réponses", ascending=True),
                x="Réponses", y=col, orientation="h",
                color_discrete_sequence=[Config.PRIMARY_COLOR],
                title=col if len(col) < 60 else col[:57] + "…",
            )
            fig.update_layout(
                height=320, margin=dict(l=10, r=10, t=45, b=10),
                yaxis_title="", xaxis_title="",
                plot_bgcolor="white", paper_bgcolor="white",
            )
            with cols[col_idx % 2]:
                st.plotly_chart(fig, use_container_width=True)
            col_idx += 1
            chart_count += 1

    @classmethod
    def render(cls):
        if not cls.is_authenticated():
            st.markdown(
                """
                <div style="text-align:center; padding-top:3rem;">
                    <div style="font-size:2.5rem;">🔒</div>
                    <h2>Espace réservé</h2>
                    <p style="color:#5B6763;">Cette page est privée. Entrez le mot de passe
                    pour accéder aux résultats de l'étude.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns([1, 1.2, 1])
            with col2:
                cls.login_form()
            st.stop()

        top_left, top_right = st.columns([5, 1])
        with top_left:
            UI.page_header("Analyse en temps réel",
                           "Résultats consolidés de l'étude de marché", "📊")
        with top_right:
            st.write("")
            if st.button("🔓 Déconnexion", use_container_width=True):
                st.session_state[cls.SESSION_KEY] = False
                st.rerun()

        if st.button("🔄 Rafraîchir les données"):
            st.cache_data.clear()
            st.rerun()

        tab_clients, tab_vendeurs = st.tabs(["👥 Clients", "🏬 Vendeurs"])
        with tab_clients:
            df_c = SheetRepository.load("Clients")
            if df_c.empty:
                st.info("Aucune donnée client disponible pour le moment.")
            else:
                cls.render_overview(df_c, "Clients")
                st.write("")
                st.subheader("Répartition des réponses")
                cls.render_auto_charts(df_c)
        with tab_vendeurs:
            df_v = SheetRepository.load("Vendeurs")
            if df_v.empty:
                st.info("Aucune donnée vendeur disponible pour le moment.")
            else:
                cls.render_overview(df_v, "Vendeurs")
                st.write("")
                st.subheader("Répartition des réponses")
                cls.render_auto_charts(df_v)


# ===========================================================================
# 9. PAGE D'ACCUEIL
# ===========================================================================
class HomePage:
    @staticmethod
    def render():
        st.markdown(
            f"""
            <div style="text-align:center; padding: 2.2rem 1rem 1rem 1rem;">
                <div style="font-size:2.8rem;">🇿🇲</div>
                <h1 style="margin-bottom:0;">Étude de Marché</h1>
                <h3 style="color:{Config.ACCENT_COLOR}; font-weight:600; margin-top:0.2rem;">
                    Projet Marketplace — Zambie
                </h3>
                <p style="max-width:640px; margin:1rem auto; font-size:1.05rem; color:#4b5563;">
                    Nous préparons le lancement d'une marketplace connectant vendeurs
                    et clients en Zambie. Ce questionnaire anonyme prend environ
                    5 minutes et nous aide à concevoir un service qui répond
                    réellement à vos besoins.
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
                st.write(
                    "Parlez-nous de vos habitudes d'achat en ligne, des difficultés "
                    "rencontrées et de ce que vous attendez d'une nouvelle marketplace."
                )
                if st.button("Commencer le questionnaire Client ➡️",
                             type="primary", use_container_width=True,
                             key="home_go_client"):
                    ClientQuestionnaire.reset_state()
                    st.session_state["page"] = "client"
                    st.rerun()

        with col2:
            with st.container(border=True):
                st.markdown("### 🏬 Je suis Vendeur / Commerçant")
                st.write(
                    "Aidez-nous à comprendre vos besoins, vos difficultés actuelles "
                    "et les conditions qui vous encourageraient à vendre en ligne."
                )
                if st.button("Commencer le questionnaire Vendeur ➡️",
                             type="primary", use_container_width=True,
                             key="home_go_vendeur"):
                    VendeurQuestionnaire.reset_state()
                    st.session_state["page"] = "vendeur"
                    st.rerun()

        st.write("")
        st.caption(
            "Vos réponses sont anonymes et utilisées uniquement dans le cadre de "
            "cette étude de marché. Merci pour votre participation 🙏"
        )


# ===========================================================================
# 10. ROUTEUR PRINCIPAL
# ===========================================================================
class Router:
    """Gère la navigation entre les pages dans un seul fichier."""

    DEFAULT_PAGE = "home"

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.markdown("### 🇿🇲 Marketplace Zambie")
            st.caption("Étude de marché")
            st.divider()

            page = st.session_state.get("page", Router.DEFAULT_PAGE)

            if st.button("🏠 Accueil", use_container_width=True,
                         type="primary" if page == "home" else "secondary",
                         key="nav_home"):
                st.session_state["page"] = "home"
                st.rerun()

            if st.button("🛍️ Questionnaire Client", use_container_width=True,
                         type="primary" if page == "client" else "secondary",
                         key="nav_client"):
                ClientQuestionnaire.reset_state()
                st.session_state["page"] = "client"
                st.rerun()

            if st.button("🏬 Questionnaire Vendeur", use_container_width=True,
                         type="primary" if page == "vendeur" else "secondary",
                         key="nav_vendeur"):
                VendeurQuestionnaire.reset_state()
                st.session_state["page"] = "vendeur"
                st.rerun()

            if st.button("📊 Analyse (admin)", use_container_width=True,
                         type="primary" if page == "analyse" else "secondary",
                         key="nav_analyse"):
                st.session_state["page"] = "analyse"
                st.rerun()

    @classmethod
    def render(cls):
        if "page" not in st.session_state:
            st.session_state["page"] = cls.DEFAULT_PAGE

        cls.render_sidebar()

        page = st.session_state["page"]
        if page == "home":
            HomePage.render()
        elif page == "client":
            ClientQuestionnaire.run()
        elif page == "vendeur":
            VendeurQuestionnaire.run()
        elif page == "analyse":
            Dashboard.render()
        else:
            HomePage.render()


# ===========================================================================
# 11. POINT D'ENTRÉE
# ===========================================================================
def main():
    st.set_page_config(
        page_title=Config.APP_TITLE,
        page_icon=Config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    StyleManager.inject_css()
    Router.render()


if __name__ == "__main__":
    main()
