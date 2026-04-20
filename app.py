import streamlit as st
import pandas as pd
import plotly.express as px
import time
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime

from utils.analyzer import load_sentiment_model, get_sentiment_roberta
from utils.processor import calculate_fis
from utils.reddit_client import fetch_recent_posts
from utils.ai_topic_classifier import load_topic_model, classify_topics_ai

# PAGE CONFIG
st.set_page_config(page_title="Sentinel-D: INC Intelligence", layout="wide")

# =========================
# 🔷 HEADER STYLE
# =========================z
st.markdown("""
<style>
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #0b1220;
    padding: 18px 25px;
    border-radius: 10px;
    margin-bottom: 20px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-title {
    font-size: 26px;
    font-weight: 700;
    color: white;
}

.header-right {
    text-align: right;
    color: white;
}

.status-label {
    font-size: 14px;
    color: #9ca3af;
}

.status-value {
    font-size: 22px;
    font-weight: 600;
    color: #22c55e;
}

.status-time {
    font-size: 12px;
    color: #4ade80;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔐 AUTHENTICATION
# =========================
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, auth_status, username = authenticator.login('Login', 'main')

if auth_status is False:
    st.error("Incorrect credentials")
    st.stop()
elif auth_status is None:
    st.warning("Enter your login credentials")
    st.stop()

# =========================
# 🛡️ HEADER DISPLAY
# =========================

# Notification Button 
st.markdown("""
<style>
.notification-box {
    position: fixed;
    top: 20px;
    right: 30px;
    background: #111827;
    padding: 12px 18px;
    border-radius: 10px;
    color: white;
    font-weight: 500;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)



current_time = datetime.now().strftime("%H:%M:%S")

st.markdown("<h1>🛡️ Sentinel-D: Topic Intelligence</h1>", unsafe_allow_html=True)


st.sidebar.write(f"Welcome, {name}")
authenticator.logout("Logout", "sidebar")

# =========================
# 🤖 LOAD MODEL
# =========================

with st.spinner("Loading AI Topic Classifier..."):
    topic_classifier = load_topic_model()

# =========================
# 📂 LOAD DATA
# =========================
try:
    df = pd.read_csv("sentry_history.csv")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

      # 🔧 FIX NULL TOPICS HERE
    if 'Primary_Topic' in df.columns:
        df['Primary_Topic'] = df['Primary_Topic'].fillna("General")

    if 'Secondary_Topic' in df.columns:
        df['Secondary_Topic'] = df['Secondary_Topic'].fillna("None")

except:
    df = pd.DataFrame()


# =========================
# 📡 FETCH DATA
# =========================
subreddit = st.sidebar.text_input("Subreddit", "exiglesianicristo")

if st.sidebar.button("Fetch & Analyze"):
    posts = fetch_recent_posts(subreddit)

    
    new_df = pd.DataFrame(posts)
    df = pd.concat([df, new_df]).drop_duplicates(subset=['Content'])

    df.to_csv("sentry_history.csv", index=False)
    st.rerun()

# =========================
# 🔔 SMART ALERTS
# =========================
if not df.empty:
    high = df[(df['Upvotes'] > 50) | (df['Comment_Count'] > 20)]
    if not high.empty:
        st.sidebar.error(f"🔥 {len(high)} High Activity Posts")
    else:
        st.sidebar.success("✅ No Alerts")

# =========================
# 📊 TABS
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "👤 Users",
    "📂 Dataset",
    "🧠 Topic Analysis"
])

# =========================
# 📊 OVERVIEW TAB
# =========================
with tab1:
    st.subheader("Sentiment Overview")

    if not df.empty:
        counts = df['Sentiment'].value_counts()

        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Negative", counts.get('Negative', 0))
        c2.metric("🔵 Neutral", counts.get('Neutral', 0))
        c3.metric("🟢 Positive", counts.get('Positive', 0))

        # Topic Distribution
        st.markdown("### Topic Distribution")
        fig = px.pie(df, names='Primary_Topic')
        st.plotly_chart(fig, use_container_width=True)

        # Trending Keywords
        from collections import Counter
        import re

        text = " ".join(df['Content'].dropna()).lower()
        words = re.findall(r'\b[a-z]{4,}\b', text)

        common = Counter(words).most_common(10)
        kw_df = pd.DataFrame(common, columns=['Keyword', 'Count'])

        fig_kw = px.bar(kw_df, x='Keyword', y='Count', title="Trending Keywords")
        st.plotly_chart(fig_kw, use_container_width=True)

        # Main Feed
        st.markdown("### 📰 Main Feed")

        df['Topic_Tag'] = df.apply(
            lambda x: f"[{x['Primary_Topic']}] [{x['Secondary_Topic']}]",
            axis=1
        )

        st.dataframe(df[['Username', 'Content', 'Topic_Tag', 'Sentiment']], use_container_width=True)

    else:
        st.info("No data yet. Fetch from sidebar.")

# =========================
# 👤 USERS TAB
# =========================
with tab2:
    st.subheader("User Insights")

    if not df.empty:
        users = df['Username'].value_counts().reset_index()
        users.columns = ['Username', 'Posts']

        st.dataframe(users)

        selected = st.selectbox("Select User", users['Username'])

        user_df = df[df['Username'] == selected]

        st.markdown("### User Activity")
        st.dataframe(user_df)

# =========================
# 📂 DATASET TAB
# =========================
with tab3:
    st.subheader("Dataset Archive")
    st.dataframe(df.sort_values(by='Timestamp', ascending=False), use_container_width=True)

# 🧠 TOPIC ANALYSIS TAB
with tab4:
    st.subheader("🧠 Multi-Topic Analysis")

    if not df.empty:

        topic_options = [
            "All",
            "Leadership",
            "Doctrines",
            "Infrastructure"
        ]

        selected_topic = st.selectbox("Filter by Topic", topic_options)

        # 🔹 Filtering logic (IMPORTANT FIX)
        if selected_topic == "All":
            filtered = df
        else:
            filtered = df[
                (df['Primary_Topic'] == selected_topic) |
                (df['Secondary_Topic'] == selected_topic)
            ]

        # 🔹 Display results
        st.write(f"Showing posts related to: **{selected_topic}**")
        st.write(f"Total Posts: {len(filtered)}")

        st.dataframe(filtered[[
            'Username',
            'Content',
            'Sentiment'
        ]], use_container_width=True)

    else:
        st.info("No topic data available.")