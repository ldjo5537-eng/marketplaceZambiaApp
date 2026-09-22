import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION PAGE ---
st.set_page_config(
    page_title="Étude de Marché — Marketplace Zambie",
    page_icon="🇿🇲",
    layout="centered"
)

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #008080;
    }
    .stButton>button {
        background-color: #008080;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #005656;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION GOOGLE SHEETS ---
@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(credentials)

def save_to_sheet(sheet_name, row_data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
        sheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")
        return False

def load_sheet_data(sheet_name):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).worksheet(sheet_name)
        return pd.DataFrame(sheet.get_all_records())
    except Exception:
        return pd.DataFrame()

# --- INITIALISATION DE L'ÉTAT DE SESSION ---
if "profile" not in st.session_state:
    st.session_state.profile = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}

# --- NAVIGATION SIDEBAR ---
st.sidebar.title("🇿🇲 Marketplace Study")
mode = st.sidebar.radio("Mode", ["📝 Répondre au Questionnaire", "📊 Dashboard Temps Réel"])

if mode == "📝 Répondre au Questionnaire":
    
    # -------------------------------------------------------------------------
    # ÉTAPE 0 : CHOIX DU PROFIL
    # -------------------------------------------------------------------------
    if st.session_state.step == 0:
        st.title("🇿🇲 Étude de Marché — Marketplace Zambie")
        st.markdown("Bienvenue ! Veuillez sélectionner votre profil pour commencer.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛍️ Je suis un Client / Acheteur", use_container_width=True):
                st.session_state.profile = "Client"
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("🏬 Je suis un Vendeur / Commerçant", use_container_width=True):
                st.session_state.profile = "Vendeur"
                st.session_state.step = 1
                st.rerun()

    # -------------------------------------------------------------------------
    # PARCOURS CLIENT (23 QUESTIONS SUR 4 PAGES)
    # -------------------------------------------------------------------------
    elif st.session_state.profile == "Client":
        
        # BARRE DE PROGRESSION
        total_steps = 4
        st.progress(st.session_state.step / total_steps, text=f"Étape {st.session_state.step} sur {total_steps}")

        # PAGE 1 : VÉRIFICATION DU RÉPONDANT
        if st.session_state.step == 1:
            st.subheader("Section 1 — Vérification du répondant")
            
            q1 = st.radio("1. Vivez-vous actuellement en Zambie ? *", ["Oui", "Non"])
            q2 = st.selectbox("2. Dans quelle ville vivez-vous actuellement ?", ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"])
            q3 = st.selectbox("3. Dans quelle tranche d’âge êtes-vous ?", ["Moins de 18 ans", "18–24 ans", "25–34 ans", "35–44 ans", "45 ans ou plus"])
            q4 = st.selectbox("4. Quel est votre statut actuel ?", ["Étudiant(e)", "Salarié(e)", "Entrepreneur(e) / indépendant(e)", "Sans emploi", "Autre"])

            col_back, col_next = st.columns([1, 1])
            with col_next:
                if st.button("Suivant ➡️"):
                    if q1 == "Non":
                        st.warning("Merci pour votre temps. Cette étude concerne uniquement les résidents en Zambie.")
                    else:
                        st.session_state.answers.update({"q1": q1, "q2": q2, "q3": q3, "q4": q4})
                        st.session_state.step = 2
                        st.rerun()

        # PAGE 2 : HABITUDES D'ACHAT
        elif st.session_state.step == 2:
            st.subheader("Section 2 — Habitudes d’achat réelles")

            q5 = st.radio("5. Au cours des 3 derniers mois, avez-vous acheté un produit en ligne ?", ["Oui", "Non"])
            q6 = st.text_input("6. Si oui, quel a été votre dernier achat en ligne ? (ex: vêtements, téléphone...)")
            q7 = st.selectbox("7. Où avez-vous effectué cet achat ?", ["WhatsApp", "Facebook", "Instagram", "Site Internet", "Application de shopping", "Autre"])
            q8 = st.selectbox("8. Comment avez-vous découvert le produit ?", ["Publication sur les réseaux sociaux", "Recommandation d’un proche", "Recherche sur Internet", "Publicité", "Je connaissais déjà le vendeur", "Autre"])
            q9 = st.selectbox("9. Comment avez-vous payé ?", ["Mobile money", "Carte bancaire", "Virement bancaire", "Paiement à la livraison", "Paiement à la collecte", "Autre"])
            q10 = st.selectbox("10. Comment avez-vous reçu votre commande ?", ["Livraison à domicile", "Livraison sur mon lieu de travail", "Livraison à un autre endroit", "Retrait en boutique", "Je suis allé(e) chercher le produit chez le vendeur", "Autre"])
            q11 = st.selectbox("11. Combien avez-vous dépensé environ pour ce dernier achat ?", ["Moins de 100 ZMW", "100–300 ZMW", "301–500 ZMW", "501–1 000 ZMW", "Plus de 1 000 ZMW"])

            col_back, col_next = st.columns([1, 1])
            with col_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 1
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡️"):
                    st.session_state.answers.update({
                        "q5": q5, "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10, "q11": q11
                    })
                    st.session_state.step = 3
                    st.rerun()

        # PAGE 3 : PROBLÈMES RENCONTRÉS
        elif st.session_state.step == 3:
            st.subheader("Section 3 — Problèmes rencontrés")

            q12 = st.radio("12. Avez-vous déjà rencontré un problème lors d’un achat en ligne ?", ["Oui", "Non"])
            q13 = st.multiselect("13. Si oui, quel problème avez-vous rencontré ?", [
                "Produit différent de la photo", "Produit jamais reçu", "Retard de livraison",
                "Vendeur malhonnête", "Difficulté à récupérer mon argent", "Frais de livraison trop élevés",
                "Produit de mauvaise qualité", "Difficulté à contacter le vendeur", "Autre"
            ])
            q14 = st.multiselect("14. Qu’est-ce qui vous empêche le plus d’acheter en ligne ?", [
                "Je ne fais pas confiance aux vendeurs", "J’ai peur de perdre mon argent", "Je préfère voir le produit avant d’acheter",
                "Les frais de livraison sont trop élevés", "Les délais de livraison sont trop longs", "Je ne connais pas suffisamment les plateformes disponibles",
                "Je préfère acheter directement en boutique", "Je n’ai pas encore eu besoin d’acheter en ligne", "Autre"
            ])

            col_back, col_next = st.columns([1, 1])
            with col_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 2
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡️"):
                    st.session_state.answers.update({
                        "q12": q12, "q13": ", ".join(q13), "q14": ", ".join(q14)
                    })
                    st.session_state.step = 4
                    st.rerun()

        # PAGE 4 : ÉVALUATION DU CONCEPT MARKETPLACE
        elif st.session_state.step == 4:
            st.subheader("Section 4 — Concept Marketplace")
            st.info("Imaginez une application permettant de découvrir des produits, comparer les prix, commander auprès de vendeurs locaux, payer de manière sécurisée et se faire livrer.")

            q15 = st.selectbox("15. Si une telle application existait, seriez-vous intéressé(e) à l’utiliser ?", ["Très intéressé(e)", "Assez intéressé(e)", "Peu intéressé(e)", "Pas du tout intéressé(e)"])
            q16 = st.multiselect("16. Parmi ces services, lesquels seraient les plus importants pour vous ? (max 3)", [
                "Vendeurs vérifiés", "Paiement sécurisé", "Livraison à domicile", "Possibilité de comparer les prix",
                "Retours et remboursements", "Service client", "Promotions", "Suivi de commande", "Avis des autres clients"
            ], max_selections=3)
            q17 = st.selectbox("17. Principale raison d’utiliser cette application plutôt que Facebook/WhatsApp ?", ["Plus de sécurité", "Plus de choix", "Prix plus intéressants", "Livraison plus pratique", "Meilleure qualité des produits", "Promotions", "Autre"])
            q18 = st.radio("18. Seriez-vous prêt(e) à payer des frais de livraison ?", ["Oui", "Non", "Cela dépend du montant"])
            q19 = st.selectbox("19. Montant raisonnable pour une livraison locale ?", ["Moins de 10 ZMW", "10–20 ZMW", "21–30 ZMW", "31–50 ZMW", "Plus de 50 ZMW", "Je ne sais pas"])
            q20 = st.multiselect("20. Qu’est-ce qui vous ferait le plus confiance ? (max 3)", [
                "Voir les avis des clients", "Savoir que les vendeurs sont vérifiés", "Pouvoir payer à la livraison",
                "Avoir une garantie de remboursement", "Voir les produits dans une boutique physique", "Pouvoir contacter facilement le service client", "Autre"
            ], max_selections=3)
            q21 = st.text_input("21. Quel produit aimeriez-vous particulièrement trouver sur cette application ?")
            q22 = st.text_area("22. Avez-vous une suggestion pour améliorer les achats en ligne en Zambie ?")
            q23 = st.selectbox("23. Comment avez-vous reçu ce questionnaire ?", ["WhatsApp", "Facebook", "Instagram", "Groupe d’étudiants", "Groupe professionnel", "Recommandation d’un proche", "Autre"])

            col_back, col_submit = st.columns([1, 1])
            with col_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 3
                    st.rerun()
            with col_submit:
                if st.button("Soumettre mes réponses 🚀"):
                    st.session_state.answers.update({
                        "q15": q15, "q16": ", ".join(q16), "q17": q17, "q18": q18, "q19": q19,
                        "q20": ", ".join(q20), "q21": q21, "q22": q22, "q23": q23
                    })
                    
                    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(st.session_state.answers.values())
                    if save_to_sheet("Clients", row):
                        st.balloons()
                        st.success("Merci ! Vos réponses ont été soumises avec succès.")
                        st.session_state.step = 0
                        st.session_state.answers = {}

    # -------------------------------------------------------------------------
    # PARCOURS VENDEUR (20 QUESTIONS SUR 3 PAGES)
    # -------------------------------------------------------------------------
    elif st.session_state.profile == "Vendeur":
        
        total_steps = 3
        st.progress(st.session_state.step / total_steps, text=f"Étape {st.session_state.step} sur {total_steps}")

        # PAGE 1 : VÉRIFICATION
        if st.session_state.step == 1:
            st.subheader("Section 1 — Vérification Vendeur")

            vq1 = st.radio("1. Votre activité est-elle actuellement située en Zambie ? *", ["Oui", "Non"])
            vq2 = st.selectbox("2. Dans quelle ville votre activité est-elle située ?", ["Lusaka", "Kitwe", "Ndola", "Livingstone", "Kabwe", "Autre"])
            vq3 = st.selectbox("3. Depuis combien de temps exercez-vous cette activité ?", ["Moins de 6 mois", "6 mois à 1 an", "1–3 ans", "Plus de 3 ans"])

            col_back, col_next = st.columns([1, 1])
            with col_next:
                if st.button("Suivant ➡️"):
                    if vq1 == "Non":
                        st.warning("Merci. L'étude concerne uniquement les entreprises basées en Zambie.")
                    else:
                        st.session_state.answers.update({"vq1": vq1, "vq2": vq2, "vq3": vq3})
                        st.session_state.step = 2
                        st.rerun()

        # PAGE 2 : ACTIVITÉ COMMERCIALE
        elif st.session_state.step == 2:
            st.subheader("Section 2 — Activité commerciale")

            vq4 = st.multiselect("4. Quels produits vendez-vous ?", ["Vêtements", "Chaussures", "Accessoires", "Produits de beauté", "Électronique", "Produits pour la maison", "Produits alimentaires", "Autre"])
            vq5 = st.multiselect("5. Où vendez-vous principalement vos produits ?", ["Boutique physique", "WhatsApp", "Facebook", "Instagram", "Site Internet", "Marketplace", "Autre"])
            vq6 = st.radio("6. Recevez-vous déjà des commandes en ligne ?", ["Oui, régulièrement", "Oui, occasionnellement", "Non"])
            vq7 = st.selectbox("7. Combien de commandes recevez-vous environ par mois ?", ["0", "1–10", "11–30", "31–100", "Plus de 100"])
            vq8 = st.selectbox("8. Quel est votre principal problème lorsque vous vendez en ligne ?", ["Trouver des clients", "Recevoir les paiements", "Organiser la livraison", "Gérer les retours", "Manque de confiance des clients", "Frais de publicité", "Autre"])

            col_back, col_next = st.columns([1, 1])
            with col_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 1
                    st.rerun()
            with col_next:
                if st.button("Suivant ➡️"):
                    st.session_state.answers.update({
                        "vq4": ", ".join(vq4), "vq5": ", ".join(vq5), "vq6": vq6, "vq7": vq7, "vq8": vq8
                    })
                    st.session_state.step = 3
                    st.rerun()

        # PAGE 3 : INTÉRÊT POUR LA MARKETPLACE
        elif st.session_state.step == 3:
            st.subheader("Section 3 — Intérêt pour le projet")

            vq9 = st.selectbox("9. Seriez-vous intéressé(e) par une application pour vendre vos produits ?", ["Très intéressé(e)", "Assez intéressé(e)", "Peu intéressé(e)", "Pas du tout intéressé(e)"])
            vq10 = st.multiselect("10. Quels services seraient les plus utiles pour vous ? (max 3)", [
                "Trouver de nouveaux clients", "Recevoir des commandes", "Paiement sécurisé", "Livraison organisée",
                "Publicité de mes produits", "Gestion des stocks", "Gestion des commandes", "Protection contre les clients malhonnêtes", "Autre"
            ], max_selections=3)
            vq11 = st.radio("11. Accepteriez-vous de payer une petite commission sur chaque vente ?", ["Oui", "Non", "Cela dépend du pourcentage"])
            vq12 = st.selectbox("12. Quel modèle préférez-vous ?", ["Commission uniquement sur les ventes", "Abonnement mensuel", "Commission + services optionnels", "Je ne sais pas encore"])
            vq13 = st.selectbox("13. Quel pourcentage de commission vous semblerait acceptable ?", ["Moins de 5 %", "5–10 %", "11–15 %", "Plus de 15 %", "Je ne sais pas"])
            vq14 = st.radio("14. Prêt(e) à utiliser un paiement sécurisé versé après livraison ?", ["Oui", "Non", "Cela dépend des conditions"])
            vq15 = st.radio("15. Accepteriez-vous de faire vérifier votre identité/activité ?", ["Oui", "Non", "Cela dépend des informations demandées"])
            vq16 = st.radio("16. Prêt(e) à utiliser un service de livraison proposé par la plateforme ?", ["Oui", "Non", "Cela dépend du prix"])
            vq17 = st.multiselect("17. Qu’est-ce qui vous empêcherait de vendre sur une nouvelle marketplace ?", ["Les commissions", "Le manque de clients", "Les difficultés de paiement", "Les difficultés de livraison", "La peur des arnaques", "La complexité de l’application", "Autre"])
            vq18 = st.text_input("18. Quelles catégories de produits sont selon vous les plus demandées en ligne ?")
            vq19 = st.text_area("19. Que devrait faire la marketplace pour vous convaincre ?")
            vq20 = st.selectbox("20. Comment avez-vous reçu ce questionnaire ?", ["WhatsApp", "Facebook", "Instagram", "Groupe de vendeurs", "Groupe professionnel", "Recommandation d’un proche", "Autre"])

            col_back, col_submit = st.columns([1, 1])
            with col_back:
                if st.button("⬅️ Précédent"):
                    st.session_state.step = 2
                    st.rerun()
            with col_submit:
                if st.button("Soumettre mes réponses (Vendeur) 🚀"):
                    st.session_state.answers.update({
                        "vq9": vq9, "vq10": ", ".join(vq10), "vq11": vq11, "vq12": vq12, "vq13": vq13,
                        "vq14": vq14, "vq15": vq15, "vq16": vq16, "vq17": ", ".join(vq17), "vq18": vq18,
                        "vq19": vq19, "vq20": vq20
                    })
                    
                    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + list(st.session_state.answers.values())
                    if save_to_sheet("Vendeurs", row):
                        st.balloons()
                        st.success("Merci ! Vos réponses vendeur ont été enregistrées.")
                        st.session_state.step = 0
                        st.session_state.answers = {}

# -----------------------------------------------------------------------------
# MODE 2 : DASHBOARD TEMPS RÉEL
# -----------------------------------------------------------------------------
else:
    st.title("📊 Analyse en Temps Réel — Zambie")
    tab1, tab2 = st.tabs(["👥 Clients", "🏬 Vendeurs"])

    with tab1:
        df_c = load_sheet_data("Clients")
        if not df_c.empty:
            st.metric("Nombre total de réponses Clients", len(df_c))
            st.dataframe(df_c)
        else:
            st.info("Aucune donnée client disponible.")

    with tab2:
        df_v = load_sheet_data("Vendeurs")
        if not df_v.empty:
            st.metric("Nombre total de réponses Vendeurs", len(df_v))
            st.dataframe(df_v)
        else:
            st.info("Aucune donnée vendeur disponible.")
