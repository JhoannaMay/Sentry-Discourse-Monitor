import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Custom modules
from utils.analyzer import load_sentiment_model, get_sentiment_roberta
from utils.processor import calculate_fis
from utils.reddit_client import fetch_recent_posts
from utils.ai_topic_classifier import load_topic_model, classify_topics_ai

# =========================
# INITIALIZATION
# =========================
st.set_page_config(page_title="Sentinel-D: Intelligence System", layout="wide")
st_autorefresh(interval=300000, key="sentinel_refresh")

if 'new_post_count' not in st.session_state:
    st.session_state.new_post_count = 0

# =========================
# HELPERS
# =========================
def get_time_ago(timestamp):
    now = datetime.now()
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    diff = now - timestamp
    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours}h ago"
    return timestamp.strftime("%b %d")

def detect_sarcasm(text, raw_label):
    sarcasm_triggers = ["pala", "wow", "talaga", "claps", "naman", "daw"]
    if raw_label == "Positive" and any(w in text.lower() for w in sarcasm_triggers):
        return "Sarcasm"
    return raw_label

# =========================
# LOAD MODELS & DATA
# =========================
with st.spinner("Initializing Intelligence Engines..."):
    topic_classifier = load_topic_model()
    sentiment_model = load_sentiment_model()

try:
    df = pd.read_csv("sentry_history.csv")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    if 'Magnitude' in df.columns:
        df['Magnitude'] = df['Magnitude'].astype(float)
except:
    df = pd.DataFrame()

# =========================
# AUTHENTICATION
# =========================
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login(location='main')

# =========================
# MAIN APP (PROTECTED)
# =========================
if st.session_state.get("authentication_status"):

    st.sidebar.title(f"Welcome, {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar", key="logout_btn")
    st.sidebar.markdown("---")

    # Sidebar
    subreddit = st.sidebar.text_input("Subreddit", "exiglesianicristo")

    if subreddit:
        raw_posts = fetch_recent_posts(subreddit, limit=10)
        if raw_posts:
            new_entries = []
            for p in raw_posts:
                if not df.empty and p['Content'] in df['Content'].values:
                    continue

                intel = get_sentiment_roberta(p['Content'], sentiment_model)
                topic_data = classify_topics_ai(p['Content'], topic_classifier)

                p.update({
                    'Sentiment': detect_sarcasm(p['Content'], intel['Sentiment']),
                    'Magnitude': intel['Magnitude'],
                    'Primary_Topic': topic_data['Primary']
                })

                new_entries.append(p)

            if new_entries:
                df = pd.concat([df, pd.DataFrame(new_entries)]).drop_duplicates(subset=['Content'])
                df.to_csv("sentry_history.csv", index=False)
                st.session_state.new_post_count = len(new_entries)

    st.sidebar.divider()
    st.sidebar.caption(f"System Time: {datetime.now().strftime('%I:%M %p')}")

    # =========================
    # DASHBOARD
    # =========================
    st.markdown("## 🛡️ Sentinel-D Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview", "Users", "Sentiment Intel",
        "High Activity", "Topic Analysis", "Archive"
    ])

    # -------- TAB 1 --------
    with tab1:
        if not df.empty:
            counts = df['Sentiment'].value_counts()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Negative", counts.get('Negative', 0))
            c2.metric("Sarcasm", counts.get('Sarcasm', 0))
            c3.metric("Neutral", counts.get('Neutral', 0))
            c4.metric("Positive", counts.get('Positive', 0))

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(px.pie(df, names='Sentiment'), use_container_width=True)

            with col2:
                df['Date'] = df['Timestamp'].dt.date
                timeline = df.groupby('Date').size().reset_index(name='Posts')
                st.plotly_chart(px.line(timeline, x='Date', y='Posts'), use_container_width=True)
        else:
            st.info("No data yet.")

    # -------- TAB 2 --------
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
            st.markdown(f"Post History for `{sel_user}`")
            u_hist = df[df['Username'] == sel_user].sort_values(by='Timestamp', ascending=False)
            st.dataframe(u_hist[['Content', 'Sentiment', 'Magnitude', 'Timestamp']], use_container_width=True, hide_index=True)


    # -------- TAB 3 --------
    with tab3:
         st.subheader("Sentiment Intelligence (Explainable AI)")
         if not df.empty:
          cols_to_show = ['Username', 'Content', 'Sentiment', 'Intent', 'Magnitude', 'Explanation']
          available_cols = [c for c in cols_to_show if c in df.columns]

         st.dataframe(
            df[available_cols], 
            column_config={

                "Magnitude": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1),
                "Intent": st.column_config.TextColumn("User Intent", help="The possible goal of the user's post"),
                "Content": st.column_config.TextColumn("Content", width="large")

            },
            use_container_width=True, hide_index=True)

    # -------- TAB 4 --------
    with tab4:
        st.subheader("High Activity Posts")
        if not df.empty:
         high_act = df[(df['Upvotes'] >= 30) | (df['Comment_Count'] >= 10)]
        st.dataframe(high_act[['Username', 'Content', 'Upvotes', 'Comment_Count', 'Sentiment']], use_container_width=True, hide_index=True)


    # -------- TAB 5 --------
    with tab5:
        st.subheader("Topic Analysis")
        if not df.empty:
         t_sel = st.selectbox("Filter Topic", ["All"] + list(df['Primary_Topic'].unique()))
         f_df = df if t_sel == "All" else df[df['Primary_Topic'] == t_sel]
        st.dataframe(f_df[['Username', 'Content', 'Primary_Topic', 'Sentiment']], use_container_width=True, hide_index=True)  

    # -------- TAB 6 --------
    with tab6:
        st.subheader("Archive")
        if not df.empty:
         edited_df = st.data_editor(
            df[['Username', 'Content', 'Sentiment', 'Magnitude', 'Timestamp']], 
            column_config={
                "Username": st.column_config.TextColumn("User", disabled=True),
                "Content": st.column_config.TextColumn("Content", width="large", disabled=True),
                "Magnitude": st.column_config.NumberColumn("Magnitude", disabled=True, format="%.2f"),
                "Timestamp": st.column_config.DatetimeColumn("Timestamp", disabled=True),
                "Sentiment": st.column_config.SelectboxColumn(
                    "Sentiment", options=["Negative", "Sarcasm", "Neutral", "Positive"]
                )
            },
            hide_index=True, use_container_width=True, key="archive_editor"
        )
        
        if st.button("Save Manual Corrections"):
            df.update(edited_df)
            df.to_csv("sentry_history.csv", index=False)
            st.success("Database refined!")
            st.rerun()

# =========================
# AUTH STATES
# =========================
elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect")

else:
    st.warning("Please enter your username and password")