# Sentry Discourse Monitor
# 🛡️ Sentry: Religious Discourse Monitor

Sentry is an intelligent, real-time sentiment analysis and monitoring dashboard designed for academic research. It leverages Natural Language Processing (NLP) to track discourse in online communities, specifically focusing on religious-centric conversations in Philippine-based subreddits.

## 🚀 Key Features
- **Multilingual Sentiment Engine:** Powered by a distilled multilingual transformer model, capable of analyzing English, Tagalog, and Taglish content with high emotional sensitivity.
- **Contextual Filtering:** Uses a custom keyword-based detection layer to isolate discourse related to the Iglesia Ni Cristo (INC) and related entities.
- **FIS Algorithm:** Implements a proprietary "Frequency-Intensity Score" (FIS) to rank and flag users based on persistent negative behavior rather than just single-post sentiment.
- **Longitudinal Tracking:** Persistent data logging that tracks sentiment shifts over time.
- **Research-Ready Export:** Integrated functionality to export analyzed datasets into Excel format for thesis documentation.

## 🛠️ Technology Stack
- **Framework:** Streamlit (UI & Dashboarding)
- **NLP Engine:** HuggingFace `transformers` (DistilBERT Multilingual)
- **Data Processing:** Pandas (for statistical analysis and FIS calculation)
- **Visualization:** Plotly (for trend analysis and sentiment frequency charts)
- **Data Source:** Reddit API

## 📋 Thesis Objectives
This project aims to demonstrate the capability of automated tools in performing:
1. **Behavioral Risk Assessment:** Identifying community members whose repetitive negative discourse may indicate polarized or extremist viewpoints.
2. **Sentiment Trend Analysis:** Mapping the correlation between specific real-world events and shifts in online sentiment.
3. **Automated Content Audit:** Reducing the time required for qualitative content analysis by categorizing massive amounts of social media data.

## ⚙️ Setup Instructions
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

---
