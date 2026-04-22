from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_sentiment_model():
    model_path = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    return pipeline("sentiment-analysis", model=model_path)
from transformers import pipeline
import streamlit as st

def get_sentiment_roberta(text, classifier):
    # 🚩 List of words that usually indicate criticism in this context
    critical_triggers = ['manalo', 'kulto', 'scam', 'pera', 'negosyo', 'brainwash', 'aliw']
    
    # 🚩 Sarcasm indicators (common in Tagalog critical posts)
    sarcasm_indicators = ['pala', 'daw', 'diba', 'kunwari', 'grabe']

    try:
        # 1. Get initial AI Prediction
        result = classifier(text[:512])[0]
        label = result['label'].capitalize()
        mapping = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral",
                   "Positive": "Positive", "Negative": "Negative", "Neutral": "Neutral"}
        sentiment = mapping.get(label, "Neutral")

        text_lower = text.lower()

        # 2. 🧠 THE INTELLIGENCE OVERRIDE
        # If AI says Positive, but the text contains 'critical' keywords + 'sarcasm' indicators
        if sentiment == "Positive":
            # Check if it hits critical triggers
            has_critical = any(word in text_lower for word in critical_triggers)
            has_sarcasm = any(word in text_lower for word in sarcasm_indicators)

            if has_critical and has_sarcasm:
                # This is likely satire (like in your image)
                return "Negative"
            elif "manalo" in text_lower and ("diyos" in text_lower or "god" in text_lower):
                # Specific check for deification/satire
                return "Negative"

        return sentiment
    except:
        return "Neutral"