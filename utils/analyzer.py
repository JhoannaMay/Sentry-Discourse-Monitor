import torch

def load_sentiment_model():
    """
    Initializes the sentiment analysis pipeline.
    """
    from transformers import pipeline
    # Using a robust model for sentiment analysis
    return pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def get_sentiment_roberta(text, classifier):
    # 1. Intent-Specific Lexicons
    intents = {
        "Dissent": ['kulto', 'scam', 'brainwash', 'persecution', 'corrupt', 'negosyo', 'false'],
        "Inquiry": ['bakit', 'paano', 'question', 'totoo ba', 'paliwanag', 'anyone know'],
        "Sarcastic/Mockery": ['galing', 'holy', 'amazing', 'lol', 'wow', 'salamat sa', 'lods'],
        "Emotional/Distress": ['tiwalag', 'iyak', 'takot', 'pamilya', 'sad', 'depressed', 'tulong']
    }

    try:
        if not text: return {"Sentiment": "Neutral", "Magnitude": 0.0, "Explanation": "No text"}

        # AI Base Prediction
        result = classifier(text[:512])[0]
        raw_label = str(result['label']).lower()
        magnitude = round(result['score'], 4)
        text_lower = text.lower()
        
        # Determine Base Sentiment
        base_sent = "Positive" if "pos" in raw_label else "Negative" if "neg" in raw_label else "Neutral"

        # 🧠 INTENT DETECTION LOGIC
        detected_intents = [label for label, words in intents.items() if any(w in text_lower for w in words)]
        primary_intent = detected_intents[0] if detected_intents else "General Discussion"

        # ⚖️ THE INTELLIGENCE OVERRIDE
        # If it's "General Discussion" but AI says Negative, it's likely just a negative opinion.
        # If it's "Sarcastic/Mockery" and AI says Positive, we MUST classify as Sarcasm.
        
        final_sentiment = base_sent
        if primary_intent == "Sarcastic/Mockery" and base_sent == "Positive":
            final_sentiment = "Sarcasm"
        elif primary_intent == "Dissent" or (base_sent == "Neutral" and any(w in text_lower for w in intents["Dissent"])):
            final_sentiment = "Negative"

        # Build an "Intelligent" Explanation
        explanation = f"Intent: {primary_intent}. "
        if final_sentiment == "Sarcasm":
            explanation += "Detected mocking tone despite positive phrasing."
        elif final_sentiment == "Negative" and base_sent == "Neutral":
            explanation += "Re-classified from Neutral due to critical keywords."
        else:
            explanation += f"AI confirmed {base_sent} ({int(magnitude*100)}% confidence)."

        return {
            "Sentiment": final_sentiment,
            "Magnitude": magnitude,
            "Explanation": explanation,
            "Intent": primary_intent  # New field!
        }
    except Exception as e:
        return {"Sentiment": "Neutral", "Magnitude": 0.0, "Explanation": str(e), "Intent": "Error"}