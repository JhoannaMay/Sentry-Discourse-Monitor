from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_sentiment_model():
    """
    Distilled Multilingual model for optimized Tagalog/English detection.
    """
    model_path = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    return pipeline("sentiment-analysis", model=model_path)

def get_sentiment_roberta(text, classifier):
    try:
        result = classifier(text[:512])[0]
        label = result['label'].capitalize()
        # Mapping labels to standard names
        mapping = {"Pos": "Positive", "Neg": "Negative", "Neu": "Neutral"}
        return mapping.get(label, label)
    except:
        return "Neutral"
    
    