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
