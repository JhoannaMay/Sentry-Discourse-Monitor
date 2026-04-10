from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_sentiment_model():
    """
    Loads the RoBERTa model. 
    Using 'cardiffnlp/twitter-roberta-base-sentiment-latest' 
    because it's fine-tuned on social media text like Reddit.
    """
    # This might take a minute to download the first time (approx 500MB)
    model_path = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    return pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)

def get_sentiment_roberta(text, classifier):
    """
    Takes text, runs it through RoBERTa, and returns 
    Positive, Neutral, or Negative.
    """
    try:
        # RoBERTa output: 0 -> Negative, 1 -> Neutral, 2 -> Positive
        result = classifier(text[:512])[0] # Limit to 512 tokens (BERT limit)
        label = result['label'].capitalize()
        return label
    except Exception as e:
        return "Neutral"