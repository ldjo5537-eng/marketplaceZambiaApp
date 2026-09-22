import streamlit as st
from common import inject_css, PRIMARY_COLOR

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Marketplace Zambie",
    page_icon="🇿🇲",
    layout="wide",
)

# ---------------------------------------------------------
# STYLE
# ---------------------------------------------------------
inject_css()

# ---------------------------------------------------------
# PAGE D'ACCUEIL
# ---------------------------------------------------------
st.markdown(
    f"""
    <div style="
        text-align:center;
        padding:30px 10px 20px 10px;
    ">
        <div style="font-size:60px;">🇿🇲</div>

        <h1 style="
            color:{PRIMARY_COLOR};
            margin-bottom:5px;
        ">
            Marketplace Zambie
        </h1>

        <p style="
            font-size:20px;
            color:#666;
        ">
            Étude de marché pour une future plateforme
            de commerce en ligne en Zambie
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="
        max-width:900px;
        margin:auto;
        text-align:center;
        font-size:17px;
        line-height:1.7;
    ">
        Cette étude nous permet de mieux comprendre les besoins
        des consommateurs et des vendeurs en Zambie afin de
        concevoir une marketplace adaptée au marché local.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ---------------------------------------------------------
# COLONNES
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div style="
            border:1px solid #ddd;
            border-radius:15px;
            padding:25px;
            min-height:220px;
            text-align:center;
        ">
            <div style="font-size:45px;">🛍️</div>
            <h2>Vous êtes client ?</h2>
            <p>
                Donnez-nous votre avis sur vos habitudes d'achat,
                vos besoins et vos attentes concernant une
                marketplace en ligne.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button(
        "➡️ Commencer le questionnaire Client",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/Questionnaire_Client.py")


with col2:
    st.markdown(
        """
        <div style="
            border:1px solid #ddd;
            border-radius:15px;
            padding:25px;
            min-height:220px;
            text-align:center;
        ">
            <div style="font-size:45px;">🏬</div>
            <h2>Vous êtes vendeur ?</h2>
            <p>
                Partagez votre expérience, vos difficultés et
                vos attentes concernant la vente en ligne.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button(
        "➡️ Commencer le questionnaire Vendeur",
        use_container_width=True,
    ):
        st.switch_page("pages/Questionnaire_Vendeur.py")


# ---------------------------------------------------------
# PIED DE PAGE
# ---------------------------------------------------------
st.write("")
st.write("")
st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#777;
        font-size:14px;
    ">
        🇿🇲 Marketplace Zambie — Étude de marché
    </div>
    """,
    unsafe_allow_html=True,
)
