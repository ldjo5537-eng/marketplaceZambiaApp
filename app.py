import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime


# =============================================================================
# CONFIGURATION GÉNÉRALE
# =============================================================================

st.set_page_config(
    page_title="Étude de Marché — Marketplace Zambie",
    page_icon="🇿🇲",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# IDENTITÉ VISUELLE + OUTILS PARTAGÉS
# =============================================================================

PRIMARY_COLOR = "#0F5C4C"
ACCENT_COLOR = "#E8871E"
DARK_COLOR = "#12251F"
BG_COLOR = "#F7F6F2"
MUTED_TEXT = "#5B6763"


def inject_css():
    """Injecte le style CSS global de l'application."""
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

        footer {{
            visibility: hidden;
        }}
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


# =============================================================================
# GOOGLE SHEETS
# =============================================================================

@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )
    return gspread.authorize(credentials)


def save_to_sheet(sheet_name: str, row_data: list) -> bool:
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(
            st.secrets["spreadsheet_id"]
        ).worksheet(sheet_name)
        sheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
        return False


@st.cache_data(ttl=60)
def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(
            st.secrets["spreadsheet_id"]
        ).worksheet(sheet_name)
        return pd.DataFrame(sheet.get_all_records())
    except Exception:
        return pd.DataFrame()


# =============================================================================
# OUTILS DU TABLEAU DE BORD
# =============================================================================

def render_overview(df: pd.DataFrame, label: str):
    """Affiche les métriques clés + un tableau brut téléchargeable."""
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


def render_auto_charts(
    df: pd.DataFrame,
    max_unique: int = 12,
    max_charts: int = 12,
):
    """
    Génère automatiquement des graphiques pour les colonnes catégorielles.
    Les réponses longues et les colonnes trop variées sont ignorées.
    """
    if df.empty:
        st.info("Aucune donnée disponible pour le moment.")
        return

    chart_count = 0
    cols = st.columns(2)
    col_idx = 0

    for col in df.columns:
        if chart_count >= max_charts:
            break

        series = (
            df[col]
            .astype(str)
            .replace({"nan": "", "None": ""})
        )
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
            x="Réponses",
            y=col,
            orientation="h",
            color_discrete_sequence=[PRIMARY_COLOR],
            title=col if len(col) < 60 else col[:57] + "…",
        )

        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=45, b=10),
            yaxis_title="",
            xaxis_title="",
            plot_bgcolor="white",
            paper_bgcolor="white",
        )

        with cols[col_idx % 2]:
            st.plotly_chart(fig, use_container_width=True)

        col_idx += 1
        chart_count += 1


# =============================================================================
# NAVIGATION
# =============================================================================

class Navigation:
    HOME = "accueil"
    CLIENT = "client"
    VENDEUR = "vendeur"
    ANALYSE = "analyse"

    @staticmethod
    def go(page: str):
        st.session_state.current_page = page
        st.rerun()

    @staticmethod
    def home():
        Navigation.go(Navigation.HOME)

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.markdown("## 🇿🇲 Marketplace Zambie")
            st.caption("Étude de marché")

            st.divider()

            if st.button("🏠 Accueil", use_container_width=True):
                Navigation.home()

            if st.button("🛍️ Questionnaire Client", use_container_width=True):
                Navigation.go(Navigation.CLIENT)

            if st.button("🏬 Questionnaire Vendeur", use_container_width=True):
                Navigation.go(Navigation.VENDEUR)

            if st.button("📊 Analyse", use_container_width=True):
                Navigation.go(Navigation.ANALYSE)

            st.divider()
            st.caption(
                "Vos réponses sont anonymes et utilisées uniquement "
                "dans le cadre de cette étude de marché."
            )


# =============================================================================
# QUESTIONNAIRE CLIENT
# =============================================================================

class QuestionnaireClient:
    TOTAL_STEPS = 4

    @staticmethod
    def init_state():
        if "client_step" not in st.session_state:
            st.session_state.client_step = 1

        if "client_answers" not in st.session_state:
            st.session_state.client_answers = {}

        if "client_excluded" not in st.session_state:
            st.session_state.client_excluded = False

        if "client_done" not in st.session_state:
            st.session_state.client_done = False

    @staticmethod
    def reset():
        st.session_state.client_step = 1
        st.session_state.client_answers = {}
        st.session_state.client_excluded = False
        st.session_state.client_done = False

    @staticmethod
    def render():
        QuestionnaireClient.init_state()

        page_header(
            "Questionnaire Client",
            "Vos habitudes d'achat en ligne en Zambie",
            "🛍️",
        )

        if st.session_state.client_excluded:
            st.info(
                "Merci pour votre temps ! Cette étude concerne uniquement "
                "les personnes résidant actuellement en Zambie."
            )

            if st.button("↩️ Retour à l'accueil"):
                QuestionnaireClient.reset()
                Navigation.home()

            st.stop()

        if st.session_state.client_done:
            st.balloons()
            st.success(
                "✅ Merci ! Vos réponses ont été enregistrées avec succès."
            )

            if st.button("↩️ Retour à l'accueil"):
                QuestionnaireClient.reset()
                Navigation.home()

            st.stop()

        step = st.session_state.client_step

        st.progress(
            step / QuestionnaireClient.TOTAL_STEPS,
            text=f"Étape {step} sur {QuestionnaireClient.TOTAL_STEPS}",
        )
        st.write("")

        if step == 1:
            QuestionnaireClient.step_1()

        elif step == 2:
            QuestionnaireClient.step_2()

        elif step == 3:
            QuestionnaireClient.step_3()

        elif step == 4:
            QuestionnaireClient.step_4()

    @staticmethod
    def step_1():
        with st.container(border=True):
            st.subheader("Section 1 — Vérification du répondant")

            q1 = st.radio(
                "1. Vivez-vous actuellement en Zambie ? *",
                ["Oui", "Non"],
                horizontal=True,
            )

            q2 = st.selectbox(
                "2. Dans quelle ville vivez-vous actuellement ?",
                [
                    "Lusaka",
                    "Kitwe",
                    "Ndola",
                    "Livingstone",
                    "Kabwe",
                    "Autre",
                ],
            )

            q3 = st.selectbox(
                "3. Dans quelle tranche d'âge êtes-vous ?",
                [
                    "Moins de 18 ans",
                    "18–24 ans",
                    "25–34 ans",
                    "35–44 ans",
                    "45 ans ou plus",
                ],
            )

            q4 = st.selectbox(
                "4. Quel est votre statut actuel ?",
                [
                    "Étudiant(e)",
                    "Salarié(e)",
                    "Entrepreneur(e) / indépendant(e)",
                    "Sans emploi",
                    "Autre",
                ],
            )

        _, col_next = st.columns([1, 1])

        with col_next:
            if st.button(
                "Suivant ➡️",
                type="primary",
                use_container_width=True,
            ):
                if q1 == "Non":
                    st.session_state.client_excluded = True
                else:
                    st.session_state.client_answers.update(
                        {
                            "q1": q1,
                            "q2": q2,
                            "q3": q3,
                            "q4": q4,
                        }
                    )
                    st.session_state.client_step = 2

                st.rerun()

    @staticmethod
    def step_2():
        with st.container(border=True):
            st.subheader("Section 2 — Habitudes d'achat réelles")

            q5 = st.radio(
                "5. Au cours des 3 derniers mois, avez-vous acheté un produit en ligne ?",
                ["Oui", "Non"],
                horizontal=True,
            )

            q6 = st.text_input(
                "6. Si oui, quel a été votre dernier achat en ligne ?",
                placeholder=(
                    "Ex : vêtements, chaussures, téléphone, "
                    "produits de beauté…"
                ),
            )

            q7 = st.selectbox(
                "7. Où avez-vous effectué cet achat ?",
                [
                    "WhatsApp",
                    "Facebook",
                    "Instagram",
                    "Site Internet",
                    "Application de shopping",
                    "Autre",
                ],
            )

            q8 = st.selectbox(
                "8. Comment avez-vous découvert le produit ?",
                [
                    "Publication sur les réseaux sociaux",
                    "Recommandation d'un proche",
                    "Recherche sur Internet",
                    "Publicité",
                    "Je connaissais déjà le vendeur",
                    "Autre",
                ],
            )

            q9 = st.selectbox(
                "9. Comment avez-vous payé ?",
                [
                    "Mobile money",
                    "Carte bancaire",
                    "Virement bancaire",
                    "Paiement à la livraison",
                    "Paiement à la collecte",
                    "Autre",
                ],
            )

            q10 = st.selectbox(
                "10. Comment avez-vous reçu votre commande ?",
                [
                    "Livraison à domicile",
                    "Livraison sur mon lieu de travail",
                    "Livraison à un autre endroit",
                    "Retrait en boutique",
                    "Je suis allé(e) chercher le produit chez le vendeur",
                    "Autre",
                ],
            )

            q11 = st.selectbox(
                "11. Combien avez-vous dépensé environ pour ce dernier achat ?",
                [
                    "Moins de 100 ZMW",
                    "100–300 ZMW",
                    "301–500 ZMW",
                    "501–1 000 ZMW",
                    "Plus de 1 000 ZMW",
                ],
            )

        col_back, col_next = st.columns(2)

        with col_back:
            if st.button("⬅️ Précédent", use_container_width=True):
                st.session_state.client_step = 1
                st.rerun()

        with col_next:
            if st.button(
                "Suivant ➡️",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.client_answers.update(
                    {
                        "q5": q5,
                        "q6": q6,
                        "q7": q7,
                        "q8": q8,
                        "q9": q9,
                        "q10": q10,
                        "q11": q11,
                    }
                )

                st.session_state.client_step = 3
                st.rerun()

    @staticmethod
    def step_3():
        with st.container(border=True):
            st.subheader("Section 3 — Problèmes rencontrés")

            q12 = st.radio(
                "12. Avez-vous déjà rencontré un problème lors d'un achat en ligne ?",
                ["Oui", "Non"],
                horizontal=True,
            )

            q13 = st.multiselect(
                "13. Si oui, quel problème avez-vous rencontré ?",
                [
                    "Produit différent de la photo",
                    "Produit jamais reçu",
                    "Retard de livraison",
                    "Vendeur malhonnête",
                    "Difficulté à récupérer mon argent",
                    "Frais de livraison trop élevés",
                    "Produit de mauvaise qualité",
                    "Difficulté à contacter le vendeur",
                    "Autre",
                ],
            )

            q14 = st.multiselect(
                "14. Qu'est-ce qui vous empêche le plus d'acheter en ligne ?",
                [
                    "Je ne fais pas confiance aux vendeurs",
                    "J'ai peur de perdre mon argent",
                    "Je préfère voir le produit avant d'acheter",
                    "Les frais de livraison sont trop élevés",
                    "Les délais de livraison sont trop longs",
                    "Je ne connais pas suffisamment les plateformes disponibles",
                    "Je préfère acheter directement en boutique",
                    "Je n'ai pas encore eu besoin d'acheter en ligne",
                    "Autre",
                ],
            )

        col_back, col_next = st.columns(2)

        with col_back:
            if st.button("⬅️ Précédent", use_container_width=True):
                st.session_state.client_step = 2
                st.rerun()

        with col_next:
            if st.button(
                "Suivant ➡️",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.client_answers.update(
                    {
                        "q12": q12,
                        "q13": ", ".join(q13),
                        "q14": ", ".join(q14),
                    }
                )

                st.session_state.client_step = 4
                st.rerun()

    @staticmethod
    def step_4():
        st.info(
            "💡 Imaginez une application permettant de découvrir des produits, "
            "comparer les prix, commander auprès de vendeurs locaux, payer de "
            "manière sécurisée et suivre sa livraison."
        )

        with st.container(border=True):
            st.subheader("Section 4 — Concept Marketplace")

            q15 = st.selectbox(
                "15. Si une telle application existait, seriez-vous intéressé(e) à l'utiliser ?",
                [
                    "Très intéressé(e)",
                    "Assez intéressé(e)",
                    "Peu intéressé(e)",
                    "Pas du tout intéressé(e)",
                ],
            )

            q16 = st.multiselect(
                "16. Parmi ces services, lesquels seraient les plus importants pour vous ? (max 3)",
                [
                    "Vendeurs vérifiés",
                    "Paiement sécurisé",
                    "Livraison à domicile",
                    "Possibilité de comparer les prix",
                    "Retours et remboursements",
                    "Service client",
                    "Promotions",
                    "Suivi de commande",
                    "Avis des autres clients",
                ],
                max_selections=3,
            )

            q17 = st.selectbox(
                "17. Quelle serait votre principale raison d'utiliser cette application plutôt que Facebook ou WhatsApp ?",
                [
                    "Plus de sécurité",
                    "Plus de choix",
                    "Prix plus intéressants",
                    "Livraison plus pratique",
                    "Meilleure qualité des produits",
                    "Promotions",
                    "Autre",
                ],
            )

            q18 = st.radio(
                "18. Seriez-vous prêt(e) à payer des frais de livraison pour recevoir votre commande ?",
                ["Oui", "Non", "Cela dépend du montant"],
                horizontal=True,
            )

            q19 = st.selectbox(
                "19. Quel montant vous semblerait raisonnable pour une livraison locale ?",
                [
                    "Moins de 10 ZMW",
                    "10–20 ZMW",
                    "21–30 ZMW",
                    "31–50 ZMW",
                    "Plus de 50 ZMW",
                    "Je ne sais pas",
                ],
            )

            q20 = st.multiselect(
                "20. Qu'est-ce qui vous ferait le plus confiance à une nouvelle marketplace ? (max 3)",
                [
                    "Voir les avis des clients",
                    "Savoir que les vendeurs sont vérifiés",
                    "Pouvoir payer à la livraison",
                    "Avoir une garantie de remboursement",
                    "Voir les produits dans une boutique physique",
                    "Pouvoir contacter facilement le service client",
                    "Autre",
                ],
                max_selections=3,
            )

            q21 = st.text_input(
                "21. Quel produit aimeriez-vous particulièrement trouver sur une telle application ?"
            )

            q22 = st.text_area(
                "22. Avez-vous une suggestion pour améliorer les achats en ligne en Zambie ?"
            )

            q23 = st.selectbox(
                "23. Comment avez-vous reçu ce questionnaire ?",
                [
                    "WhatsApp",
                    "Facebook",
                    "Instagram",
                    "Groupe d'étudiants",
                    "Groupe professionnel",
                    "Recommandation d'un proche",
                    "Autre",
                ],
            )

        col_back, col_submit = st.columns(2)

        with col_back:
            if st.button("⬅️ Précédent", use_container_width=True):
                st.session_state.client_step = 3
                st.rerun()

        with col_submit:
            if st.button(
                "Soumettre mes réponses 🚀",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.client_answers.update(
                    {
                        "q15": q15,
                        "q16": ", ".join(q16),
                        "q17": q17,
                        "q18": q18,
                        "q19": q19,
                        "q20": ", ".join(q20),
                        "q21": q21,
                        "q22": q22,
                        "q23": q23,
                    }
                )

                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ] + list(st.session_state.client_answers.values())

                with st.spinner("Enregistrement en cours…"):
                    success = save_to_sheet("Clients", row)

                if success:
                    st.session_state.client_done = True
                    st.rerun()


# =============================================================================
# QUESTIONNAIRE VENDEUR
# =============================================================================

class QuestionnaireVendeur:
    TOTAL_STEPS = 3

    @staticmethod
    def init_state():
        if "vendeur_step" not in st.session_state:
            st.session_state.vendeur_step = 1

        if "vendeur_answers" not in st.session_state:
            st.session_state.vendeur_answers = {}

        if "vendeur_excluded" not in st.session_state:
            st.session_state.vendeur_excluded = False

        if "vendeur_done" not in st.session_state:
            st.session_state.vendeur_done = False

    @staticmethod
    def reset():
        st.session_state.vendeur_step = 1
        st.session_state.vendeur_answers = {}
        st.session_state.vendeur_excluded = False
        st.session_state.vendeur_done = False

    @staticmethod
    def render():
        QuestionnaireVendeur.init_state()

        page_header(
            "Questionnaire Vendeur",
            "Vos besoins en tant que vendeur en Zambie",
            "🏬",
        )

        if st.session_state.vendeur_excluded:
            st.info(
                "Merci pour votre temps ! Cette étude concerne uniquement "
                "les entreprises basées en Zambie."
            )

            if st.button("↩️ Retour à l'accueil"):
                QuestionnaireVendeur.reset()
                Navigation.home()

            st.stop()

        if st.session_state.vendeur_done:
            st.balloons()
            st.success(
                "✅ Merci ! Vos réponses vendeur ont été enregistrées avec succès."
            )

            if st.button("↩️ Retour à l'accueil"):
                QuestionnaireVendeur.reset()
                Navigation.home()

            st.stop()

        step = st.session_state.vendeur_step

        st.progress(
            step / QuestionnaireVendeur.TOTAL_STEPS,
            text=f"Étape {step} sur {QuestionnaireVendeur.TOTAL_STEPS}",
        )
        st.write("")

        if step == 1:
            QuestionnaireVendeur.step_1()

        elif step == 2:
            QuestionnaireVendeur.step_2()

        elif step == 3:
            QuestionnaireVendeur.step_3()

    @staticmethod
    def step_1():
        with st.container(border=True):
            st.subheader("Section 1 — Vérification")

            vq1 = st.radio(
                "1. Votre activité est-elle actuellement située en Zambie ? *",
                ["Oui", "Non"],
                horizontal=True,
            )

            vq2 = st.selectbox(
                "2. Dans quelle ville votre activité est-elle située ?",
                [
                    "Lusaka",
                    "Kitwe",
                    "Ndola",
                    "Livingstone",
                    "Kabwe",
                    "Autre",
                ],
            )

            vq3 = st.selectbox(
                "3. Depuis combien de temps exercez-vous cette activité ?",
                [
                    "Moins de 6 mois",
                    "6 mois à 1 an",
                    "1–3 ans",
                    "Plus de 3 ans",
                ],
            )

        _, col_next = st.columns([1, 1])

        with col_next:
            if st.button(
                "Suivant ➡️",
                type="primary",
                use_container_width=True,
            ):
                if vq1 == "Non":
                    st.session_state.vendeur_excluded = True
                else:
                    st.session_state.vendeur_answers.update(
                        {
                            "vq1": vq1,
                            "vq2": vq2,
                            "vq3": vq3,
                        }
                    )
                    st.session_state.vendeur_step = 2

                st.rerun()

    @staticmethod
    def step_2():
        with st.container(border=True):
            st.subheader("Section 2 — Activité commerciale")

            vq4 = st.multiselect(
                "4. Quels produits vendez-vous ?",
                [
                    "Vêtements",
                    "Chaussures",
                    "Accessoires",
                    "Produits de beauté",
                    "Électronique",
                    "Produits pour la maison",
                    "Produits alimentaires",
                    "Autre",
                ],
            )

            vq5 = st.multiselect(
                "5. Où vendez-vous principalement vos produits ?",
                [
                    "Boutique physique",
                    "WhatsApp",
                    "Facebook",
                    "Instagram",
                    "Site Internet",
                    "Marketplace",
                    "Autre",
                ],
            )

            vq6 = st.radio(
                "6. Recevez-vous déjà des commandes en ligne ?",
                [
                    "Oui, régulièrement",
                    "Oui, occasionnellement",
                    "Non",
                ],
            )

            vq7 = st.selectbox(
                "7. Combien de commandes recevez-vous environ par mois ?",
                [
                    "0",
                    "1–10",
                    "11–30",
                    "31–100",
                    "Plus de 100",
                ],
            )

            vq8 = st.selectbox(
                "8. Quel est votre principal problème lorsque vous vendez en ligne ?",
                [
                    "Trouver des clients",
                    "Recevoir les paiements",
                    "Organiser la livraison",
                    "Gérer les retours",
                    "Manque de confiance des clients",
                    "Frais de publicité",
                    "Autre",
                ],
            )

        col_back, col_next = st.columns(2)

        with col_back:
            if st.button("⬅️ Précédent", use_container_width=True):
                st.session_state.vendeur_step = 1
                st.rerun()

        with col_next:
            if st.button(
                "Suivant ➡️",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.vendeur_answers.update(
                    {
                        "vq4": ", ".join(vq4),
                        "vq5": ", ".join(vq5),
                        "vq6": vq6,
                        "vq7": vq7,
                        "vq8": vq8,
                    }
                )

                st.session_state.vendeur_step = 3
                st.rerun()

    @staticmethod
    def step_3():
        with st.container(border=True):
            st.subheader("Section 3 — Intérêt pour le projet")

            vq9 = st.selectbox(
                "9. Seriez-vous intéressé(e) par une application permettant de vendre vos produits à des clients zambiens ?",
                [
                    "Très intéressé(e)",
                    "Assez intéressé(e)",
                    "Peu intéressé(e)",
                    "Pas du tout intéressé(e)",
                ],
            )

            vq10 = st.multiselect(
                "10. Quels services seraient les plus utiles pour vous ? (max 3)",
                [
                    "Trouver de nouveaux clients",
                    "Recevoir des commandes",
                    "Paiement sécurisé",
                    "Livraison organisée",
                    "Publicité de mes produits",
                    "Gestion des stocks",
                    "Gestion des commandes",
                    "Protection contre les clients malhonnêtes",
                    "Autre",
                ],
                max_selections=3,
            )

            vq11 = st.radio(
                "11. Accepteriez-vous de payer une petite commission sur chaque vente réalisée grâce à la plateforme ?",
                [
                    "Oui",
                    "Non",
                    "Cela dépend du pourcentage",
                ],
            )

            vq12 = st.selectbox(
                "12. Quel modèle préférez-vous ?",
                [
                    "Commission uniquement sur les ventes",
                    "Abonnement mensuel",
                    "Commission + services optionnels",
                    "Je ne sais pas encore",
                ],
            )

            vq13 = st.selectbox(
                "13. Quel pourcentage de commission vous semblerait acceptable ?",
                [
                    "Moins de 5 %",
                    "5–10 %",
                    "11–15 %",
                    "Plus de 15 %",
                    "Je ne sais pas",
                ],
            )

            vq14 = st.radio(
                "14. Seriez-vous prêt(e) à utiliser un système de paiement sécurisé où l'argent est versé après confirmation de la commande ?",
                [
                    "Oui",
                    "Non",
                    "Cela dépend des conditions",
                ],
            )

            vq15 = st.radio(
                "15. Accepteriez-vous de faire vérifier votre identité et votre activité pour vendre sur la plateforme ?",
                [
                    "Oui",
                    "Non",
                    "Cela dépend des informations demandées",
                ],
            )

            vq16 = st.radio(
                "16. Seriez-vous prêt(e) à utiliser un service de livraison proposé par la plateforme ?",
                [
                    "Oui",
                    "Non",
                    "Cela dépend du prix",
                ],
            )

            vq17 = st.multiselect(
                "17. Qu'est-ce qui vous empêcherait de vendre sur une nouvelle marketplace ?",
                [
                    "Les commissions",
                    "Le manque de clients",
                    "Les difficultés de paiement",
                    "Les difficultés de livraison",
                    "La peur des arnaques",
                    "La complexité de l'application",
                    "Autre",
                ],
            )

            vq18 = st.text_input(
                "18. Quelles catégories de produits pensez-vous être les plus demandées en ligne en Zambie ?"
            )

            vq19 = st.text_area(
                "19. Qu'est-ce qu'une marketplace devrait faire pour vous convaincre de l'utiliser ?"
            )

            vq20 = st.selectbox(
                "20. Comment avez-vous reçu ce questionnaire ?",
                [
                    "WhatsApp",
                    "Facebook",
                    "Instagram",
                    "Groupe de vendeurs",
                    "Groupe professionnel",
                    "Recommandation d'un proche",
                    "Autre",
                ],
            )

        col_back, col_submit = st.columns(2)

        with col_back:
            if st.button("⬅️ Précédent", use_container_width=True):
                st.session_state.vendeur_step = 2
                st.rerun()

        with col_submit:
            if st.button(
                "Soumettre mes réponses 🚀",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.vendeur_answers.update(
                    {
                        "vq9": vq9,
                        "vq10": ", ".join(vq10),
                        "vq11": vq11,
                        "vq12": vq12,
                        "vq13": vq13,
                        "vq14": vq14,
                        "vq15": vq15,
                        "vq16": vq16,
                        "vq17": ", ".join(vq17),
                        "vq18": vq18,
                        "vq19": vq19,
                        "vq20": vq20,
                    }
                )

                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ] + list(st.session_state.vendeur_answers.values())

                with st.spinner("Enregistrement en cours…"):
                    success = save_to_sheet("Vendeurs", row)

                if success:
                    st.session_state.vendeur_done = True
                    st.rerun()


# =============================================================================
# ANALYSE
# =============================================================================

class Analyse:
    @staticmethod
    def init_state():
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False

    @staticmethod
    def logout():
        st.session_state.authenticated = False
        Navigation.home()

    @staticmethod
    def check_password():
        admin_password = st.secrets.get("admin_password", None)

        if admin_password is None:
            st.error(
                "⚠️ Aucun mot de passe n'est configuré. Ajoutez "
                "`admin_password` dans vos secrets Streamlit pour "
                "protéger cette page."
            )
            return False

        with st.form("login_form"):
            pwd = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="••••••••",
            )

            submitted = st.form_submit_button(
                "Se connecter",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if pwd == admin_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")

        return False

    @staticmethod
    def render():
        Analyse.init_state()

        if not st.session_state.authenticated:
            st.markdown(
                """
                <div style="text-align:center; padding-top:3rem;">
                    <div style="font-size:2.5rem;">🔒</div>
                    <h2>Espace réservé</h2>
                    <p style="color:#5B6763;">
                        Cette page est privée. Entrez le mot de passe pour
                        accéder aux résultats de l'étude.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns([1, 1.2, 1])

            with col2:
                Analyse.check_password()

            st.stop()

        top_left, top_right = st.columns([5, 1])

        with top_left:
            page_header(
                "Analyse en temps réel",
                "Résultats consolidés de l'étude de marché",
                "📊",
            )

        with top_right:
            st.write("")

            if st.button("🔓 Déconnexion", use_container_width=True):
                Analyse.logout()

        if st.button("🔄 Rafraîchir les données"):
            st.cache_data.clear()
            st.rerun()

        tab_clients, tab_vendeurs = st.tabs(
            ["👥 Clients", "🏬 Vendeurs"]
        )

        with tab_clients:
            df_c = load_sheet_data("Clients")

            if df_c.empty:
                st.info(
                    "Aucune donnée client disponible pour le moment."
                )
            else:
                render_overview(df_c, "Clients")
                st.write("")
                st.subheader("Répartition des réponses")
                render_auto_charts(df_c)

        with tab_vendeurs:
            df_v = load_sheet_data("Vendeurs")

            if df_v.empty:
                st.info(
                    "Aucune donnée vendeur disponible pour le moment."
                )
            else:
                render_overview(df_v, "Vendeurs")
                st.write("")
                st.subheader("Répartition des réponses")
                render_auto_charts(df_v)


# =============================================================================
# ACCUEIL
# =============================================================================

class Accueil:
    @staticmethod
    def render():
        st.markdown(
            f"""
            <div style="text-align:center; padding: 2.2rem 1rem 1rem 1rem;">
                <div style="font-size:2.8rem;">🇿🇲</div>
                <h1 style="margin-bottom:0;">Étude de Marché</h1>
                <h3 style="color:{ACCENT_COLOR}; font-weight:600; margin-top:0.2rem;">
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

                if st.button(
                    "➡️ Commencer le questionnaire Client",
                    type="primary",
                    use_container_width=True,
                ):
                    Navigation.go(Navigation.CLIENT)

        with col2:
            with st.container(border=True):
                st.markdown("### 🏬 Je suis Vendeur / Commerçant")

                st.write(
                    "Aidez-nous à comprendre vos besoins, vos difficultés actuelles "
                    "et les conditions qui vous encourageraient à vendre en ligne."
                )

                if st.button(
                    "➡️ Commencer le questionnaire Vendeur",
                    type="primary",
                    use_container_width=True,
                ):
                    Navigation.go(Navigation.VENDEUR)

        st.write("")

        st.caption(
            "Vos réponses sont anonymes et utilisées uniquement dans le cadre de "
            "cette étude de marché. Merci pour votre participation 🙏"
        )


# =============================================================================
# POINT D'ENTRÉE UNIQUE
# =============================================================================

def main():
    inject_css()

    if "current_page" not in st.session_state:
        st.session_state.current_page = Navigation.HOME

    Navigation.render_sidebar()

    page = st.session_state.current_page

    if page == Navigation.HOME:
        Accueil.render()

    elif page == Navigation.CLIENT:
        QuestionnaireClient.render()

    elif page == Navigation.VENDEUR:
        QuestionnaireVendeur.render()

    elif page == Navigation.ANALYSE:
        Analyse.render()

    else:
        st.session_state.current_page = Navigation.HOME
        Accueil.render()


if __name__ == "__main__":
    main()
