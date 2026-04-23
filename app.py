import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pytz

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
# AUTH
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

    # Sidebar
    st.sidebar.title(f"Welcome, {st.session_state['name']}")
    authenticator.logout("Logout", "sidebar", key="logout_btn")
    st.sidebar.markdown("---")

    # 🔔 Notifications
    if st.session_state.new_post_count > 0 and not df.empty:
        with st.sidebar.popover(f"🔔 Notifications ({st.session_state.new_post_count})"):
            recent_hits = df.sort_values(by='Timestamp', ascending=False).head(st.session_state.new_post_count)
            for _, row in recent_hits.iterrows():
                st.markdown(f"**{row['Username']}**")
                st.caption(f"{row['Content'][:45]}... • {get_time_ago(row['Timestamp'])}")
            if st.button("Mark all as Read"):
                st.session_state.new_post_count = 0
                st.rerun()

    # 🔎 Subreddit
    subreddit = st.sidebar.text_input("Subreddit", "exiglesianicristo")

    # 🔄 AUTO FETCH
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
                    'Explanation': intel.get('Explanation', ''),
                    'Primary_Topic': topic_data['Primary']
                })

                new_entries.append(p)

            if new_entries:
                df = pd.concat([df, pd.DataFrame(new_entries)]).drop_duplicates(subset=['Content'])
                df.to_csv("sentry_history.csv", index=False)
                st.session_state.new_post_count = len(new_entries)

    # 🔘 FETCH BUTTON (RESTORED)
    if st.sidebar.button("Fetch & Analyze Fresh Data"):
        with st.status(f"Scanning r/{subreddit}...", expanded=True) as status:
            posts = fetch_recent_posts(subreddit, limit=25)
            if posts:
                new_entries = []
                for p in posts:
                    if not df.empty and p['Content'] in df['Content'].values:
                        continue

                    intel = get_sentiment_roberta(p['Content'], sentiment_model)
                    topic_data = classify_topics_ai(p['Content'], topic_classifier)

                    p.update({
                        'Sentiment': detect_sarcasm(p['Content'], intel['Sentiment']),
                        'Magnitude': intel['Magnitude'],
                        'Explanation': intel.get('Explanation', ''),
                        'Primary_Topic': topic_data['Primary']
                    })

                    new_entries.append(p)

                if new_entries:
                    df = pd.concat([df, pd.DataFrame(new_entries)]).drop_duplicates(subset=['Content'])
                    df.to_csv("sentry_history.csv", index=False)
                    st.session_state.new_post_count += len(new_entries)
                    status.update(label="Scan Complete!", state="complete")
                    st.rerun()
                else:
                    status.update(label="Already up to date.", state="complete")

    local_tz = pytz.timezone('Asia/Manila') 
    local_time = datetime.now(local_tz) 
    # ❤️ SYSTEM HEARTBEAT (RESTORED)
    st.sidebar.divider()
    st.sidebar.caption(f"System Heartbeat: {local_time.now().strftime('%I:%M %p')}")
    st.sidebar.caption("Auto-refresh active (5m interval)")

    # =========================
    # DASHBOARD
    # =========================
    st.markdown("## 🛡️ Sentinel-D Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview", "Users", "Sentiment Intel",
        "High Activity", "Topic Analysis", "Archive"
    ])

    # TAB 1
    with tab1:
        if not df.empty:
            counts = df['Sentiment'].value_counts()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔴 Negative", counts.get('Negative', 0))
            c2.metric("🟣 Sarcasm", counts.get('Sarcasm', 0))
            c3.metric("🔵 Neutral", counts.get('Neutral', 0))
            c4.metric("🟢 Positive", counts.get('Positive', 0))

            st.divider()

            col_l, col_r = st.columns(2)

            with col_l:
                fig_pie = px.pie(df, names='Sentiment', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_r:
                df['Date'] = df['Timestamp'].dt.date
                timeline = df.groupby('Date').size().reset_index(name='Posts')
                fig_line = px.line(timeline, x='Date', y='Posts')
                st.plotly_chart(fig_line, use_container_width=True)

            st.divider()

            st.dataframe(
                df[['Timestamp', 'Username', 'Content', 'Sentiment', 'Magnitude']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data available.")

    # TAB 2
    with tab2:
        if not df.empty:
            st.dataframe(calculate_fis(df), use_container_width=True)

    # TAB 3
    with tab3:
        if not df.empty:
            st.dataframe(df[['Username','Content','Sentiment','Magnitude','Explanation']], use_container_width=True)

    # TAB 4
    with tab4:
        if not df.empty:
            st.dataframe(df[(df['Upvotes']>=30)|(df['Comment_Count']>=10)])

    # TAB 5
    with tab5:
        if not df.empty:
            topic = st.selectbox("Topic", ["All"] + list(df['Primary_Topic'].unique()))
            st.dataframe(df if topic=="All" else df[df['Primary_Topic']==topic])

    # TAB 6
    with tab6:
        if not df.empty:
            edited = st.data_editor(df)
            if st.button("Save Manual Corrections"):
                df.update(edited)
                df.to_csv("sentry_history.csv", index=False)
                st.success("Saved!")
                st.rerun()

# =========================
# AUTH STATES
# =========================
elif st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect")

else:
    st.warning("Please enter your username and password")