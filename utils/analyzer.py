import torch

def load_sentiment_model():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def get_sentiment_roberta(text, classifier):
    # 1. Intent Lexicons (The "Intelligence" Layer)
    intents = {
        "Dissent": ['kulto', 'scam', 'brainwash', 'persecution', 'corrupt', 'negosyo', 'false', 'bulag'],
        "Inquiry": ['bakit', 'paano', 'question', 'totoo ba', 'paliwanag', 'sugo'],
        "Sarcastic/Mockery": ['salamat', 'galing', 'very holy', 'lol', 'wow', 'grabe', 'nice one', 'amazing', 'lods'],
        "Emotional/Distress": ['tiwalag', 'iyak', 'takot', 'pamilya', 'sad', 'tulong']
    }
    
    critical_triggers = intents["Dissent"] + ['hipokrito', 'incoolto', 'handog']

    try:
        if not text or len(str(text).strip()) == 0:
            return {"Sentiment": "Neutral", "Magnitude": 0.0, "Explanation": "Empty", "Intent": "None"}

        result = classifier(text[:512])[0]
        raw_label = str(result['label']).lower()
        magnitude = round(result['score'], 4)
        text_lower = text.lower()
        
        base_sent = "Positive" if "pos" in raw_label else "Negative" if "neg" in raw_label else "Neutral"

        detected_intents = [label for label, words in intents.items() if any(w in text_lower for w in words)]
        primary_intent = detected_intents[0] if detected_intents else "General Discussion"

        
        if primary_intent == "Sarcastic/Mockery":
            final_sentiment = "Sarcasm"
            explanation = "Intelligence Override: Intent identified as Mockery/Sarcasm."
        
        elif (primary_intent == "Dissent") or (base_sent == "Neutral" and any(w in text_lower for w in critical_triggers)):
            final_sentiment = "Negative"
            explanation = "Intelligence Override: Critical keywords/Dissent intent detected."
            magnitude = max(magnitude, 0.75) # Boost confidence for critical terms
            
        else:
            final_sentiment = base_sent
            explanation = f"AI confirmed {base_sent} ({int(magnitude*100)}% confidence)."

        return {
            "Sentiment": final_sentiment,
            "Magnitude": magnitude,
            "Explanation": explanation,
            "Intent": primary_intent
        }
    except Exception as e:
        return {"Sentiment": "Neutral", "Magnitude": 0.0, "Explanation": str(e), "Intent": "Error"}