import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from common import inject_css, save_to_sheet, page_header

st.set_page_config(
    page_title="Questionnaire Vendeur — Marketplace Zambie",
    page_icon="🏬",
    layout="centered",
)
inject_css()

TOTAL_STEPS = 3

if "vendeur_step" not in st.session_state:
    st.session_state.vendeur_step = 1
if "vendeur_answers" not in st.session_state:
    st.session_state.vendeur_answers = {}
if "vendeur_excluded" not in st.session_state:
    st.session_state.vendeur_excluded = False
if "vendeur_done" not in st.session_state:
    st.session_state.vendeur_done = False

page_header("Questionnaire Vendeur", "Vos besoins en tant que vendeur en Zambie", "🏬")

# --- FIN : ACTIVITÉ HORS ZAMBIE ---
if st.session_state.vendeur_excluded:
    st.info("Merci pour votre temps ! Cette étude concerne uniquement les entreprises basées en Zambie.")
    if st.button("↩️ Retour à l'accueil"):
        st.session_state.vendeur_step = 1
        st.session_state.vendeur_excluded = False
        st.switch_page("app.py")
    st.stop()

# --- FIN : QUESTIONNAIRE SOUMIS ---
if st.session_state.vendeur_done:
    st.balloons()
    st.success("✅ Merci ! Vos réponses vendeur ont été enregistrées avec succès.")
    if st.button("↩️ Retour à l'accueil"):
        st.session_state.vendeur_step = 1
        st.session_state.vendeur_answers = {}
        st.session_state.vendeur_done = False
        st.switch_page("app.py")
    st.stop()

step = st.session_state.vendeur_step
st.progress(step / TOTAL_STEPS, text=f"Étape {step} sur {TOTAL_STEPS}")
st.write("")

# ===========================================================================
# ÉTAPE 1 — VÉRIFICATION
# ===========================================================================
if step == 1:
    with st.container(border=True):
        st.subheader("Section 1 — Vérification")
        vq1 = st.radio("1. Votre activité est-elle actuellement située en Zambie ? *", ["Oui", "Non"], horizontal=True)
        vq2 = st.selectbox("2. Dans quelle ville votre activité est-elle située ?",
                            ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"])
        vq3 = st.selectbox("3. Depuis combien de temps exercez-vous cette activité ?",
                            ["Moins de 6 mois", "6 mois à 1 an", "1–3 ans", "Plus de 3 ans"])

    _, col_next = st.columns([1, 1])
    with col_next:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            if vq1 == "Non":
                st.session_state.vendeur_excluded = True
            else:
                st.session_state.vendeur_answers.update({"vq1": vq1, "vq2": vq2, "vq3": vq3})
                st.session_state.vendeur_step = 2
            st.rerun()

# ===========================================================================
# ÉTAPE 2 — ACTIVITÉ COMMERCIALE
# ===========================================================================
elif step == 2:
    with st.container(border=True):
        st.subheader("Section 2 — Activité commerciale")
        vq4 = st.multiselect("4. Quels produits vendez-vous ?",
                              ["Vêtements", "Chaussures", "Accessoires", "Produits de beauté", "Électronique",
                               "Produits pour la maison", "Produits alimentaires", "Autre"])
        vq5 = st.multiselect("5. Où vendez-vous principalement vos produits ?",
                              ["Boutique physique", "WhatsApp", "Facebook", "Instagram", "Site Internet",
                               "Marketplace", "Autre"])
        vq6 = st.radio("6. Recevez-vous déjà des commandes en ligne ?",
                        ["Oui, régulièrement", "Oui, occasionnellement", "Non"])
        vq7 = st.selectbox("7. Combien de commandes recevez-vous environ par mois ?",
                            ["0", "1–10", "11–30", "31–100", "Plus de 100"])
        vq8 = st.selectbox("8. Quel est votre principal problème lorsque vous vendez en ligne ?",
                            ["Trouver des clients", "Recevoir les paiements", "Organiser la livraison",
                             "Gérer les retours", "Manque de confiance des clients", "Frais de publicité", "Autre"])

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

# ===========================================================================
# ÉTAPE 3 — INTÉRÊT POUR LE PROJET
# ===========================================================================
elif step == 3:
    with st.container(border=True):
        st.subheader("Section 3 — Intérêt pour le projet")
        vq9 = st.selectbox("9. Seriez-vous intéressé(e) par une application permettant de vendre vos produits à des clients zambiens ?",
                            ["Très intéressé(e)", "Assez intéressé(e)", "Peu intéressé(e)", "Pas du tout intéressé(e)"])
        vq10 = st.multiselect("10. Quels services seraient les plus utiles pour vous ? (max 3)", [
            "Trouver de nouveaux clients", "Recevoir des commandes", "Paiement sécurisé", "Livraison organisée",
            "Publicité de mes produits", "Gestion des stocks", "Gestion des commandes",
            "Protection contre les clients malhonnêtes", "Autre"
        ], max_selections=3)
        vq11 = st.radio("11. Accepteriez-vous de payer une petite commission sur chaque vente réalisée grâce à la plateforme ?",
                         ["Oui", "Non", "Cela dépend du pourcentage"])
        vq12 = st.selectbox("12. Quel modèle préférez-vous ?",
                             ["Commission uniquement sur les ventes", "Abonnement mensuel",
                              "Commission + services optionnels", "Je ne sais pas encore"])
        vq13 = st.selectbox("13. Quel pourcentage de commission vous semblerait acceptable ?",
                             ["Moins de 5 %", "5–10 %", "11–15 %", "Plus de 15 %", "Je ne sais pas"])
        vq14 = st.radio("14. Seriez-vous prêt(e) à utiliser un système de paiement sécurisé où l'argent est versé après confirmation de la commande ?",
                         ["Oui", "Non", "Cela dépend des conditions"])
        vq15 = st.radio("15. Accepteriez-vous de faire vérifier votre identité et votre activité pour vendre sur la plateforme ?",
                         ["Oui", "Non", "Cela dépend des informations demandées"])
        vq16 = st.radio("16. Seriez-vous prêt(e) à utiliser un service de livraison proposé par la plateforme ?",
                         ["Oui", "Non", "Cela dépend du prix"])
        vq17 = st.multiselect("17. Qu'est-ce qui vous empêcherait de vendre sur une nouvelle marketplace ?",
                               ["Les commissions", "Le manque de clients", "Les difficultés de paiement",
                                "Les difficultés de livraison", "La peur des arnaques",
                                "La complexité de l'application", "Autre"])
        vq18 = st.text_input("18. Quelles catégories de produits pensez-vous être les plus demandées en ligne en Zambie ?")
        vq19 = st.text_area("19. Qu'est-ce qu'une marketplace devrait faire pour vous convaincre de l'utiliser ?")
        vq20 = st.selectbox("20. Comment avez-vous reçu ce questionnaire ?",
                             ["WhatsApp", "Facebook", "Instagram", "Groupe de vendeurs", "Groupe professionnel",
                              "Recommandation d'un proche", "Autre"])

    col_back, col_submit = st.columns(2)
    with col_back:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.vendeur_step = 2
            st.rerun()
    with col_submit:
        if st.button("Soumettre mes réponses 🚀", type="primary", use_container_width=True):
            st.session_state.vendeur_answers.update({
                "vq9": vq9, "vq10": ", ".join(vq10), "vq11": vq11, "vq12": vq12, "vq13": vq13,
                "vq14": vq14, "vq15": vq15, "vq16": vq16, "vq17": ", ".join(vq17), "vq18": vq18,
                "vq19": vq19, "vq20": vq20
            })
            row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(st.session_state.vendeur_answers.values())
            with st.spinner("Enregistrement en cours…"):
                success = save_to_sheet("Vendeurs", row)
            if success:
                st.session_state.vendeur_done = True
                st.rerun()
