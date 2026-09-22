import streamlit as st
from questionnaire_client import afficher_client
from questionnaire_vendeur import afficher_vendeur
from analyse import afficher_analyse

st.set_page_config(
    page_title="Marketplace Zambie",
    page_icon="🇿🇲",
    layout="wide"
)

# Navigation interne
if "page" not in st.session_state:
    st.session_state.page = "accueil"


def accueil():
    st.title("🇿🇲 Marketplace Zambie")
    st.write("Étude de marché pour une future marketplace en Zambie.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛍️ Client")
        st.write("Répondez au questionnaire destiné aux consommateurs.")

        if st.button("➡️ Questionnaire Client", use_container_width=True):
            st.session_state.page = "client"
            st.rerun()

    with col2:
        st.subheader("🏬 Vendeur")
        st.write("Répondez au questionnaire destiné aux vendeurs.")

        if st.button("➡️ Questionnaire Vendeur", use_container_width=True):
            st.session_state.page = "vendeur"
            st.rerun()


# Affichage de la page sélectionnée
if st.session_state.page == "accueil":
    accueil()

elif st.session_state.page == "client":
    afficher_client()

elif st.session_state.page == "vendeur":
    afficher_vendeur()

elif st.session_state.page == "analyse":
    afficher_analyse()
