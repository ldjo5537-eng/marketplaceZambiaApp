"""
common.py
---------
Fonctions et style partagés par toutes les pages de l'application
"Étude de Marché — Marketplace Zambie".
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------------------------------
# IDENTITÉ VISUELLE
# ---------------------------------------------------------------------------
PRIMARY_COLOR = "#0F5C4C"   # vert profond
ACCENT_COLOR = "#E8871E"    # orange cuivré
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

        /* Barre de progression */
        .stProgress > div > div > div > div {{
            background-color: {ACCENT_COLOR};
        }}

        /* Boutons */
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

        /* Cartes (containers bordés) */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
            box-shadow: 0 1px 3px rgba(18, 37, 31, 0.06);
        }}

        /* Métriques */
        div[data-testid="stMetric"] {{
            background-color: white;
            border: 1px solid #E7E5DE;
            border-radius: 14px;
            padding: 1rem;
        }}

        /* Sidebar */
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


# ---------------------------------------------------------------------------
# CONNEXION GOOGLE SHEETS
# ---------------------------------------------------------------------------
@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(credentials)


def save_to_sheet(sheet_name: str, row_data: list) -> bool:
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
        sheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
        return False


@st.cache_data(ttl=60)
def load_sheet_data(sheet_name: str) -> pd.DataFrame:
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
        return pd.DataFrame(sheet.get_all_records())
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# DASHBOARD GÉNÉRIQUE (fonctionne quels que soient les intitulés de colonnes)
# ---------------------------------------------------------------------------
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


def render_auto_charts(df: pd.DataFrame, max_unique: int = 12, max_charts: int = 12):
    """
    Génère automatiquement un graphique en barres pour chaque colonne
    "catégorielle" (peu de valeurs distinctes) — y compris les colonnes
    à choix multiples enregistrées sous forme de texte séparé par virgules.
    Les colonnes de texte libre (réponses longues/variées) sont ignorées.
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
        series = df[col].astype(str).replace({"nan": "", "None": ""})
        series = series[series.str.strip() != ""]
        if series.empty:
            continue

        avg_len = series.str.len().mean()
        exploded = series.str.split(",").explode().str.strip()
        exploded = exploded[exploded != ""]
        unique_vals = exploded.nunique()

        # On ignore les colonnes qui ressemblent à du texte libre ou une date
        if unique_vals == 0 or unique_vals > max_unique or avg_len > 45:
            continue
        if unique_vals == len(series):  # probablement un identifiant / horodatage
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
