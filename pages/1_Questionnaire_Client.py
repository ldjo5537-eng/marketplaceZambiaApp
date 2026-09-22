import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from common import inject_css, save_to_sheet, page_header, PRIMARY_COLOR

st.set_page_config(
    page_title="Questionnaire Client — Marketplace Zambie",
    page_icon="🛍️",
    layout="centered",
)
inject_css()

TOTAL_STEPS = 4

if "client_step" not in st.session_state:
    st.session_state.client_step = 1
if "client_answers" not in st.session_state:
    st.session_state.client_answers = {}
if "client_excluded" not in st.session_state:
    st.session_state.client_excluded = False
if "client_done" not in st.session_state:
    st.session_state.client_done = False

page_header("Questionnaire Client", "Vos habitudes d'achat en ligne en Zambie", "🛍️")

# --- FIN : NON RÉSIDENT ---
if st.session_state.client_excluded:
    st.info(
        "Merci pour votre temps ! Cette étude concerne uniquement les "
        "personnes résidant actuellement en Zambie."
    )
    if st.button("↩️ Retour à l'accueil"):
        st.session_state.client_step = 1
        st.session_state.client_excluded = False
        st.switch_page("app.py")
    st.stop()

# --- FIN : QUESTIONNAIRE SOUMIS ---
if st.session_state.client_done:
    st.balloons()
    st.success("✅ Merci ! Vos réponses ont été enregistrées avec succès.")
    if st.button("↩️ Retour à l'accueil"):
        st.session_state.client_step = 1
        st.session_state.client_answers = {}
        st.session_state.client_done = False
        st.switch_page("app.py")
    st.stop()

step = st.session_state.client_step
st.progress(step / TOTAL_STEPS, text=f"Étape {step} sur {TOTAL_STEPS}")
st.write("")

# ===========================================================================
# ÉTAPE 1 — VÉRIFICATION DU RÉPONDANT
# ===========================================================================
if step == 1:
    with st.container(border=True):
        st.subheader("Section 1 — Vérification du répondant")
        q1 = st.radio("1. Vivez-vous actuellement en Zambie ? *", ["Oui", "Non"], horizontal=True)
        q2 = st.selectbox("2. Dans quelle ville vivez-vous actuellement ?",
                           ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"])
        q3 = st.selectbox("3. Dans quelle tranche d'âge êtes-vous ?",
                           ["Moins de 18 ans", "18–24 ans", "25–34 ans", "35–44 ans", "45 ans ou plus"])
        q4 = st.selectbox("4. Quel est votre statut actuel ?",
                           ["Étudiant(e)", "Salarié(e)", "Entrepreneur(e) / indépendant(e)", "Sans emploi", "Autre"])

    _, col_next = st.columns([1, 1])
    with col_next:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            if q1 == "Non":
                st.session_state.client_excluded = True
            else:
                st.session_state.client_answers.update({"q1": q1, "q2": q2, "q3": q3, "q4": q4})
                st.session_state.client_step = 2
            st.rerun()

# ===========================================================================
# ÉTAPE 2 — HABITUDES D'ACHAT RÉELLES
# ===========================================================================
elif step == 2:
    with st.container(border=True):
        st.subheader("Section 2 — Habitudes d'achat réelles")
        q5 = st.radio("5. Au cours des 3 derniers mois, avez-vous acheté un produit en ligne ?", ["Oui", "Non"], horizontal=True)
        q6 = st.text_input("6. Si oui, quel a été votre dernier achat en ligne ?",
                            placeholder="Ex : vêtements, chaussures, téléphone, produits de beauté…")
        q7 = st.selectbox("7. Où avez-vous effectué cet achat ?",
                           ["WhatsApp", "Facebook", "Instagram", "Site Internet", "Application de shopping", "Autre"])
        q8 = st.selectbox("8. Comment avez-vous découvert le produit ?",
                           ["Publication sur les réseaux sociaux", "Recommandation d'un proche", "Recherche sur Internet",
                            "Publicité", "Je connaissais déjà le vendeur", "Autre"])
        q9 = st.selectbox("9. Comment avez-vous payé ?",
                           ["Mobile money", "Carte bancaire", "Virement bancaire", "Paiement à la livraison",
                            "Paiement à la collecte", "Autre"])
        q10 = st.selectbox("10. Comment avez-vous reçu votre commande ?",
                            ["Livraison à domicile", "Livraison sur mon lieu de travail", "Livraison à un autre endroit",
                             "Retrait en boutique", "Je suis allé(e) chercher le produit chez le vendeur", "Autre"])
        q11 = st.selectbox("11. Combien avez-vous dépensé environ pour ce dernier achat ?",
                            ["Moins de 100 ZMW", "100–300 ZMW", "301–500 ZMW", "501–1 000 ZMW", "Plus de 1 000 ZMW"])

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.client_step = 1
            st.rerun()
    with col_next:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            st.session_state.client_answers.update({
                "q5": q5, "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10, "q11": q11
            })
            st.session_state.client_step = 3
            st.rerun()

# ===========================================================================
# ÉTAPE 3 — PROBLÈMES RENCONTRÉS
# ===========================================================================
elif step == 3:
    with st.container(border=True):
        st.subheader("Section 3 — Problèmes rencontrés")
        q12 = st.radio("12. Avez-vous déjà rencontré un problème lors d'un achat en ligne ?", ["Oui", "Non"], horizontal=True)
        q13 = st.multiselect("13. Si oui, quel problème avez-vous rencontré ?", [
            "Produit différent de la photo", "Produit jamais reçu", "Retard de livraison",
            "Vendeur malhonnête", "Difficulté à récupérer mon argent", "Frais de livraison trop élevés",
            "Produit de mauvaise qualité", "Difficulté à contacter le vendeur", "Autre"
        ])
        q14 = st.multiselect("14. Qu'est-ce qui vous empêche le plus d'acheter en ligne ?", [
            "Je ne fais pas confiance aux vendeurs", "J'ai peur de perdre mon argent",
            "Je préfère voir le produit avant d'acheter", "Les frais de livraison sont trop élevés",
            "Les délais de livraison sont trop longs", "Je ne connais pas suffisamment les plateformes disponibles",
            "Je préfère acheter directement en boutique", "Je n'ai pas encore eu besoin d'acheter en ligne", "Autre"
        ])

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.client_step = 2
            st.rerun()
    with col_next:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            st.session_state.client_answers.update({
                "q12": q12, "q13": ", ".join(q13), "q14": ", ".join(q14)
            })
            st.session_state.client_step = 4
            st.rerun()

# ===========================================================================
# ÉTAPE 4 — CONCEPT MARKETPLACE
# ===========================================================================
elif step == 4:
    st.info(
        "💡 Imaginez une application permettant de découvrir des produits, "
        "comparer les prix, commander auprès de vendeurs locaux, payer de "
        "manière sécurisée et suivre sa livraison."
    )
    with st.container(border=True):
        st.subheader("Section 4 — Concept Marketplace")
        q15 = st.selectbox("15. Si une telle application existait, seriez-vous intéressé(e) à l'utiliser ?",
                            ["Très intéressé(e)", "Assez intéressé(e)", "Peu intéressé(e)", "Pas du tout intéressé(e)"])
        q16 = st.multiselect("16. Parmi ces services, lesquels seraient les plus importants pour vous ? (max 3)", [
            "Vendeurs vérifiés", "Paiement sécurisé", "Livraison à domicile", "Possibilité de comparer les prix",
            "Retours et remboursements", "Service client", "Promotions", "Suivi de commande", "Avis des autres clients"
        ], max_selections=3)
        q17 = st.selectbox("17. Quelle serait votre principale raison d'utiliser cette application plutôt que Facebook ou WhatsApp ?",
                            ["Plus de sécurité", "Plus de choix", "Prix plus intéressants", "Livraison plus pratique",
                             "Meilleure qualité des produits", "Promotions", "Autre"])
        q18 = st.radio("18. Seriez-vous prêt(e) à payer des frais de livraison pour recevoir votre commande ?",
                        ["Oui", "Non", "Cela dépend du montant"], horizontal=True)
        q19 = st.selectbox("19. Quel montant vous semblerait raisonnable pour une livraison locale ?",
                            ["Moins de 10 ZMW", "10–20 ZMW", "21–30 ZMW", "31–50 ZMW", "Plus de 50 ZMW", "Je ne sais pas"])
        q20 = st.multiselect("20. Qu'est-ce qui vous ferait le plus confiance à une nouvelle marketplace ? (max 3)", [
            "Voir les avis des clients", "Savoir que les vendeurs sont vérifiés", "Pouvoir payer à la livraison",
            "Avoir une garantie de remboursement", "Voir les produits dans une boutique physique",
            "Pouvoir contacter facilement le service client", "Autre"
        ], max_selections=3)
        q21 = st.text_input("21. Quel produit aimeriez-vous particulièrement trouver sur une telle application ?")
        q22 = st.text_area("22. Avez-vous une suggestion pour améliorer les achats en ligne en Zambie ?")
        q23 = st.selectbox("23. Comment avez-vous reçu ce questionnaire ?",
                            ["WhatsApp", "Facebook", "Instagram", "Groupe d'étudiants", "Groupe professionnel",
                             "Recommandation d'un proche", "Autre"])

    col_back, col_submit = st.columns(2)
    with col_back:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.client_step = 3
            st.rerun()
    with col_submit:
        if st.button("Soumettre mes réponses 🚀", type="primary", use_container_width=True):
            st.session_state.client_answers.update({
                "q15": q15, "q16": ", ".join(q16), "q17": q17, "q18": q18, "q19": q19,
                "q20": ", ".join(q20), "q21": q21, "q22": q22, "q23": q23
            })
            row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(st.session_state.client_answers.values())
            with st.spinner("Enregistrement en cours…"):
                success = save_to_sheet("Clients", row)
            if success:
                st.session_state.client_done = True
                st.rerun()
