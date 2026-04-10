import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Phase 5: Dashboard Configuration [cite: 172]
st.set_page_config(page_title="Sentry | Monitoring Dashboard", layout="wide")

# Sidebar for Administrative Controls [cite: 42]
st.sidebar.title("🛡️ Admin Controls")
fis_threshold = st.sidebar.slider("FIS Watchlist Threshold", 0, 10, 5)

st.title("Sentry: Religious Discourse Monitor")
st.markdown("Automated Sentiment & User Intensity Tracking ")

# --- Mock Data for UI/Component Testing ---
data = {
    'Username': ['User_X', 'User_Y', 'User_Z', 'User_X', 'User_W'],
    'Sentiment': ['Negative', 'Positive', 'Neutral', 'Negative', 'Negative'],
    'Content': ["Criticism text...", "Supportive post...", "Info...", "Hateful...", "Negative..."]
}
df = pd.DataFrame(data)

# --- Metric Triage (Phase 5: Analytical Results) [cite: 173, 175] ---
col1, col2, col3 = st.columns(3)
col1.metric("Positive Discourse", len(df[df['Sentiment']=='Positive']))
col2.metric("Neutral Discourse", len(df[df['Sentiment']=='Neutral']))
col3.metric("Negative (Alerts)", len(df[df['Sentiment']=='Negative']))

# --- User Watchlist Component (Phase 4: FIS Calculation) [cite: 38, 170] ---
st.subheader("🚩 Automated User Watchlist")
# Identifying persistent bad actors [cite: 25, 32]
user_counts = df[df['Sentiment'] == 'Negative'].groupby('Username').size().reset_index(name='FIS')
watchlist = user_counts[user_counts['FIS'] >= fis_threshold]

if not watchlist.empty:
    st.warning(f"High-Intensity Users Detected (FIS >= {fis_threshold})")
    st.table(watchlist)
else:
    st.success("No users currently exceed the intensity threshold.")