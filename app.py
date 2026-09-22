import streamlit as st
from common import inject_css, PRIMARY_COLOR, ACCENT_COLOR

st.set_page_config(
    page_title="Étude de Marché — Marketplace Zambie",
    page_icon="🇿🇲",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

st.markdown(
    f"""
    <div style="text-align:center; padding: 2.2rem 1rem 1rem 1rem;">
        <div style="font-size:2.8rem;">🇿🇲</div>

        <h1 style="margin-bottom:0;">
            Étude de Marché
        </h1>

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


# ============================================================
# CLIENT
# ============================================================

with col1:

    with st.container(border=True):

        st.markdown("### 🛍️ Je suis Client / Acheteur")

        st.write(
            "Parlez-nous de vos habitudes d'achat en ligne, des difficultés "
            "rencontrées et de ce que vous attendez d'une nouvelle marketplace."
        )

        if st.button(
            "➡️ Commencer le questionnaire Client",
            use_container_width=True,
            key="client_button",
        ):
            st.switch_page("pages/Questionnaire_Client.py")


# ============================================================
# VENDEUR
# ============================================================

with col2:

    with st.container(border=True):

        st.markdown("### 🏬 Je suis Vendeur / Commerçant")

        st.write(
            "Aidez-nous à comprendre vos besoins, vos difficultés actuelles "
            "et les conditions qui vous encourageraient à vendre en ligne."
        )

        if st.button(
            "➡️ Commencer le questionnaire Vendeur",
            use_container_width=True,
            key="vendeur_button",
        ):
            st.switch_page("pages/Questionnaire_Vendeur.py")


st.write("")

st.caption(
    "Vos réponses sont anonymes et utilisées uniquement dans le cadre de "
    "cette étude de marché. Merci pour votre participation 🙏"
)
