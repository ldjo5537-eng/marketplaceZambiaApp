import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from common import inject_css, load_sheet_data, page_header, render_overview, render_auto_charts

st.set_page_config(
    page_title="Analyse — Marketplace Zambie",
    page_icon="📊",
    layout="wide",
)
inject_css()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def check_password():
    admin_password = st.secrets.get("admin_password", None)
    if admin_password is None:
        st.error(
            "⚠️ Aucun mot de passe n'est configuré. Ajoutez `admin_password` "
            "dans vos secrets Streamlit pour protéger cette page."
        )
        return

    with st.form("login_form"):
        pwd = st.text_input("Mot de passe", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
    if submitted:
        if pwd == admin_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")


# ---------------------------------------------------------------------------
# ÉCRAN DE CONNEXION
# ---------------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown(
        """
        <div style="text-align:center; padding-top:3rem;">
            <div style="font-size:2.5rem;">🔒</div>
            <h2>Espace réservé</h2>
            <p style="color:#5B6763;">Cette page est privée. Entrez le mot de passe pour accéder aux résultats de l'étude.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        check_password()
    st.stop()

# ---------------------------------------------------------------------------
# TABLEAU DE BORD
# ---------------------------------------------------------------------------
top_left, top_right = st.columns([5, 1])
with top_left:
    page_header("Analyse en temps réel", "Résultats consolidés de l'étude de marché", "📊")
with top_right:
    st.write("")
    if st.button("🔓 Déconnexion", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

if st.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()

tab_clients, tab_vendeurs = st.tabs(["👥 Clients", "🏬 Vendeurs"])

with tab_clients:
    df_c = load_sheet_data("Clients")
    if df_c.empty:
        st.info("Aucune donnée client disponible pour le moment.")
    else:
        render_overview(df_c, "Clients")
        st.write("")
        st.subheader("Répartition des réponses")
        render_auto_charts(df_c)

with tab_vendeurs:
    df_v = load_sheet_data("Vendeurs")
    if df_v.empty:
        st.info("Aucune donnée vendeur disponible pour le moment.")
    else:
        render_overview(df_v, "Vendeurs")
        st.write("")
        st.subheader("Répartition des réponses")
        render_auto_charts(df_v)
