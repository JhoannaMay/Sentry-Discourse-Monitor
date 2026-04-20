from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_topic_model():
    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )

TOPIC_LABELS = [
    "Leadership and Administration",
    "Infrastructure and Projects",
    "Doctrines and Beliefs",
    "General Discussion"
]

def simplify_topic(label):
    if label is None:
        return None
    if "Leadership" in label:
        return "Leadership"
    elif "Infrastructure" in label:
        return "Infrastructure"
    elif "Doctrines" in label:
        return "Doctrines"
    else:
        return "General"

def classify_topics_ai(text, classifier):
    try:
        result = classifier(
            text[:512],
            candidate_labels=TOPIC_LABELS,
            multi_label=True
        )

        labels = result["labels"]
        scores = result["scores"]

        topic_scores = dict(zip(labels, scores))
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        primary = simplify_topic(sorted_topics[0][0])
        secondary = simplify_topic(sorted_topics[1][0]) if len(sorted_topics) > 1 else None

        return {
            "Primary": primary,
            "Secondary": secondary,
            "Confidence": topic_scores
        }

    except:
        return {
            "Primary": "General",
            "Secondary": None,
            "Confidence": {"General": 1.0}
        }