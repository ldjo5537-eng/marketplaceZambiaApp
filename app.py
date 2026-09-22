import streamlit as st
from common import inject_css, PRIMARY_COLOR

st.set_page_config(
    page_title="Marketplace Zambie",
    page_icon="🇿🇲",
    layout="wide",
)

inject_css()

st.title("🇿🇲 Marketplace Zambie")

st.markdown(
    """
    ## Étude de marché

    Cette étude vise à comprendre les besoins des clients
    et des vendeurs pour une future marketplace en Zambie.
    """
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🛍️ Client")
    st.write(
        "Vous êtes consommateur ? "
        "Répondez à quelques questions concernant vos habitudes d'achat."
    )

    if st.button(
        "➡️ Questionnaire Client",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/Questionnaire_Client.py")


with col2:
    st.subheader("🏬 Vendeur")
    st.write(
        "Vous êtes vendeur ? "
        "Partagez votre expérience et vos besoins."
    )

    if st.button(
        "➡️ Questionnaire Vendeur",
        use_container_width=True,
    ):
        st.switch_page("pages/Questionnaire_Vendeur.py")

st.divider()

st.caption("🇿🇲 Marketplace Zambie — Étude de marché")
