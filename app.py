import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime

from utils.analyzer import load_sentiment_model, get_sentiment_roberta
from utils.processor import calculate_fis
from utils.reddit_client import fetch_recent_posts
from utils.ai_topic_classifier import load_topic_model, classify_topics_ai
from streamlit_autorefresh import st_autorefresh

# 1. SETTINGS & REFRESH
st_autorefresh(interval=300000, key="sentinel_refresh")
st.set_page_config(page_title="Sentinel-D: Intelligence System", layout="wide")

if 'new_post_count' not in st.session_state:
    st.session_state.new_post_count = 0

# =========================
# 🔷 CSS CUSTOM STYLING
# =========================
st.markdown("""
<style>
.header-container { background-color: #0b1220; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
.header-title { font-size: 28px; font-weight: 700; color: white; }
.stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
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
    st.warning("Please enter your credentials to access the system")
    st.stop()

# =========================
# 🤖 LOAD MODELS & DATA
# =========================
with st.spinner("Initializing Intelligence Engines..."):
    topic_classifier = load_topic_model()
    sentiment_model = load_sentiment_model()

try:
    df = pd.read_csv("sentry_history.csv")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
except Exception:
    df = pd.DataFrame()

# =========================
# 👈 SIDEBAR TOOLS
# =========================
st.sidebar.title(f"Welcome, {name}")
authenticator.logout("Logout", "sidebar")
st.sidebar.markdown("---")

subreddit = st.sidebar.text_input("Target Subreddit", "exiglesianicristo")

if st.sidebar.button("📡 Fetch & Analyze Fresh Data"):
    posts = fetch_recent_posts(subreddit)
    if posts:
        new_list = []
        for p in posts:
            intel = get_sentiment_roberta(p['Content'], sentiment_model)
            topic_data = classify_topics_ai(p['Content'], topic_classifier)
            p.update({
                'Sentiment': intel['Sentiment'],
                'Magnitude': intel['Magnitude'],
                'Explanation': intel['Explanation'],
                'Primary_Topic': topic_data['Primary']
            })
            new_list.append(p)
        
        new_df = pd.DataFrame(new_list)
        df = pd.concat([df, new_df]).drop_duplicates(subset=['Content']) if not df.empty else new_df
        df.to_csv("sentry_history.csv", index=False)
        st.sidebar.success("New data integrated!")
        st.rerun()

st.sidebar.markdown("### 🛠️ Intelligence Tools")
if st.sidebar.button("🔄 Re-Analyze Past Data"):
    if not df.empty:
        with st.spinner("Automating sentiment double-check..."):
            progress = st.progress(0)
            for i, idx in enumerate(df.index):
                intel = get_sentiment_roberta(df.at[idx, 'Content'], sentiment_model)
                df.at[idx, 'Sentiment'] = intel['Sentiment']
                df.at[idx, 'Magnitude'] = intel['Magnitude']
                df.at[idx, 'Explanation'] = intel['Explanation']
                progress.progress((i + 1) / len(df))
            df.to_csv("sentry_history.csv", index=False)
            st.sidebar.success("Re-analysis complete!")
            st.rerun()

# =========================
# 🛡️ MAIN DASHBOARD UI
# =========================
st.markdown('<div class="header-container"><span class="header-title">🛡️ Sentinel-D: Topic & Sentiment Intelligence</span></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", "Users", "🧠 Sentiment Intelligence", "High Activity", "Topic Analysis", "Archive"
])

# --- TAB 1: OVERVIEW ---
with tab1:
    if not df.empty:
        counts = df['Sentiment'].value_counts()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Negative", counts.get('Negative', 0))
        c2.metric("🟣 Sarcasm", counts.get('Sarcasm', 0))
        c3.metric("🔵 Neutral", counts.get('Neutral', 0))
        c4.metric("🟢 Positive", counts.get('Positive', 0))
        
        col_l, col_r = st.columns(2)
        with col_l:
            fig_pie = px.pie(df, names='Sentiment', hole=0.4, title="Sentiment Share",
                            color='Sentiment', color_discrete_map={
                                'Negative': '#ef4444', 'Sarcasm': '#a855f7', 
                                'Neutral': '#3b82f6', 'Positive': '#22c55e'})
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_r:
            fig_box = px.box(df, x='Sentiment', y='Magnitude', color='Sentiment', 
                             title="Classification Confidence Levels",
                             color_discrete_map={'Negative':'#ef4444','Sarcasm':'#a855f7','Neutral':'#3b82f6','Positive':'#22c55e'})
            st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No data available. Use the sidebar to fetch data.")

# --- TAB 2: USERS ---
with tab2:
    if not df.empty:
        user_analysis = calculate_fis(df)
        if not user_analysis.empty:
            c_sel, c_met = st.columns([1, 2])
            with c_sel:
                sel_user = st.selectbox("Search/Select User", user_analysis['Username'])
                u_data = user_analysis[user_analysis['Username'] == sel_user].iloc[0]
                st.metric("Avg Magnitude", u_data['Avg_Magnitude'])
                st.metric("FIS Score", u_data['FIS_Score'])
            with c_met:
                st.dataframe(user_analysis, use_container_width=True, hide_index=True)
            
            st.divider()
            st.markdown(f"### 📑 Post History for `{sel_user}`")
            u_hist = df[df['Username'] == sel_user].sort_values(by='Timestamp', ascending=False)
            st.dataframe(u_hist[['Content', 'Sentiment', 'Magnitude', 'Timestamp']], use_container_width=True, hide_index=True)

# --- TAB 3: SENTIMENT INTELLIGENCE ---
# Inside app.py Tab 3
with tab3:
    st.subheader("🧠 Sentiment Intelligence (Explainable AI)")
    if not df.empty:
        # Check if 'Intent' column exists (it will after you Re-Analyze)
        cols_to_show = ['Username', 'Content', 'Sentiment', 'Intent', 'Magnitude', 'Explanation']
        available_cols = [c for c in cols_to_show if c in df.columns]
        
        st.dataframe(
            df[available_cols], 
            column_config={
                "Magnitude": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1),
                "Intent": st.column_config.TextColumn("User Intent", help="The possible goal of the user's post"),
                "Content": st.column_config.TextColumn("Content", width="large")
            },
            use_container_width=True, hide_index=True
        )

# --- TAB 4, 5, 6: (Condensed for brevity) ---
with tab4:
    st.subheader("🔥 High Activity Posts")
    if not df.empty:
        high_act = df[(df['Upvotes'] >= 30) | (df['Comment_Count'] >= 10)]
        st.dataframe(high_act[['Username', 'Content', 'Upvotes', 'Comment_Count', 'Sentiment']], use_container_width=True, hide_index=True)

with tab5:
    st.subheader("📊 Topic Analysis")
    if not df.empty:
        t_sel = st.selectbox("Filter Topic", ["All"] + list(df['Primary_Topic'].unique()))
        f_df = df if t_sel == "All" else df[df['Primary_Topic'] == t_sel]
        st.dataframe(f_df[['Username', 'Content', 'Primary_Topic', 'Sentiment']], use_container_width=True, hide_index=True)

with tab6:
    st.subheader("📂 Dataset Archive & Verification")
    if not df.empty:
        edited_df = st.data_editor(df[['Username', 'Content', 'Sentiment', 'Magnitude', 'Timestamp']], use_container_width=True, hide_index=True)
        if st.button("💾 Save Manual Corrections"):
            df.update(edited_df)
            df.to_csv("sentry_history.csv", index=False)
            st.success("Database Updated!")