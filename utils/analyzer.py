from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_sentiment_model():
    model_path = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    return pipeline("sentiment-analysis", model=model_path)

def get_sentiment_roberta(text, classifier):
    # Expanded triggers for better context detection
    critical_triggers = [
        'kulto', 'brainwash', 'scam', 'pera', 'hipokrito', 
        'incoolto', 'corrupt', 'negosyo', 'pagsamba'
    ]

    try:
        result = classifier(text[:512])[0]
        raw_label = str(result['label']).lower()
        magnitude = round(result['score'], 4)

        # Mapping for the specific student model
        if "pos" in raw_label:
            sentiment = "Positive"
        elif "neg" in raw_label:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        text_lower = text.lower()
        is_sarcastic = False
        
        # Sarcasm/Context Check: 
        # If it's Positive/Neutral but uses critical slang, force Negative
        if sentiment in ["Positive", "Neutral"]:
            if any(word in text_lower for word in critical_triggers):
                sentiment = "Negative"
                is_sarcastic = True

        return sentiment, magnitude, is_sarcastic

    except Exception:
        return "Neutral", 0.0, False