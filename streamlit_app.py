import os
import requests
import streamlit as st

# -----------------------------
# Configuration de la page
# -----------------------------
st.set_page_config(
    page_title="Tweet Likes Predictor",
    page_icon="💬",
    layout="centered"
)

# -----------------------------
# Secrets Azure ML (Cloud-first)
# App Service -> variables d'env
# Fallback -> st.secrets (si dispo)
# -----------------------------
def get_secret(key: str, default: str = "") -> str:
    # 1) Azure App Service env var
    v = os.getenv(key)
    if v:
        return v.strip()
    # 2) Streamlit secrets (si fichier/secret existe)
    try:
        return str(st.secrets.get(key, default)).strip()
    except Exception:
        return default

SCORING_URL = get_secret("AZUREML_SCORING_URL")
API_KEY = get_secret("AZUREML_API_KEY")
DEPLOYMENT_NAME = get_secret("AZUREML_DEPLOYMENT_NAME", "")

# -----------------------------
# Fonctions métier
# -----------------------------
def engagement_label(likes: int) -> str:
    if likes < 10:
        return "Low engagement"
    elif likes < 100:
        return "Medium engagement"
    return "High engagement"


def call_endpoint(tweet_text: str):
    """
    Appelle l'endpoint Azure ML.
    Ton score.py attend STRICTEMENT :
    { "text": "tweet" }
    """
    if not SCORING_URL or not API_KEY:
        raise RuntimeError(
            "AZUREML_SCORING_URL / AZUREML_API_KEY manquants. "
            "Ajoute-les dans App Service > Variables d’environnement."
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    if DEPLOYMENT_NAME:
        headers["azureml-model-deployment"] = DEPLOYMENT_NAME

    # ✅ Payload correct pour ton score.py
    payload = {"text": tweet_text}

    response = requests.post(
        SCORING_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    return response.json()

# -----------------------------
# Interface utilisateur
# -----------------------------
st.title("💬 Tweet Likes Prediction (Azure ML)")
st.write(
    "Entre un tweet → appel REST vers Azure ML → "
    "affichage du **nombre de likes prédits** et de l’**engagement**."
)

# (Optionnel) mini check de config pour debug cloud
with st.expander("🔧 Debug config (cloud)"):
    st.write("SCORING_URL défini :", bool(SCORING_URL))
    st.write("API_KEY défini :", bool(API_KEY))
    st.write("DEPLOYMENT_NAME :", DEPLOYMENT_NAME if DEPLOYMENT_NAME else "(vide)")

tweet = st.text_area(
    "Texte du tweet",
    height=140,
    placeholder="Ex: Just deployed my first model on Azure ML 🚀"
)

if st.button("Prédire", type="primary"):
    if not tweet.strip():
        st.warning("Merci d'entrer un texte de tweet.")
    else:
        try:
            with st.spinner("Appel de l'endpoint Azure ML..."):
                result = call_endpoint(tweet)

            preds = result.get("predictions")

            if preds is None:
                st.error("Réponse inattendue de l'endpoint.")
                st.json(result)
            else:
                likes = int(preds[0])
                label = engagement_label(likes)

                st.success("✅ Prédiction reçue")
                st.metric("Likes prédits", likes)
                st.info(f"Interprétation : **{label}**")

                with st.expander("Réponse brute de l'endpoint"):
                    st.json(result)

        except requests.HTTPError as e:
            st.error("Erreur HTTP lors de l'appel à l'endpoint.")
            # Affiche aussi le body si possible (utile en cloud)
            try:
                st.code(e.response.text)
            except Exception:
                pass
            st.code(str(e))
        except Exception as e:
            st.error("Erreur inattendue.")
            st.code(str(e))
