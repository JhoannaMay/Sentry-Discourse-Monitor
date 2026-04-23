import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime
from streamlit_autorefresh import st_autorefresh



from utils.analyzer import load_sentiment_model, get_sentiment_roberta
from utils.processor import calculate_fis
from utils.reddit_client import fetch_recent_posts
from utils.ai_topic_classifier import load_topic_model, classify_topics_ai


st_autorefresh(interval=300000, key="sentinel_refresh")
st.set_page_config(page_title="Sentinel-D: Intelligence System", layout="wide")


if 'new_post_count' not in st.session_state:
    st.session_state.new_post_count = 0

def get_time_ago(timestamp):
    now = datetime.now()
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    diff = now - timestamp
    seconds = diff.total_seconds()
    if seconds < 60: return "Just now"
    minutes = int(seconds // 60)
    if minutes < 60: return f"{minutes}m ago"
    hours = int(minutes // 60)
    if hours < 24: return f"{hours}h ago"
    return timestamp.strftime("%b %d")

def detect_sarcasm(text, raw_label):
    """Simple keyword check to flip Positive results to Sarcasm."""
    sarcasm_triggers = ["pala", "wow", "talaga", "claps", "naman", "daw"]
    text_lower = text.lower()
    if raw_label == "Positive" and any(word in text_lower for word in sarcasm_triggers):
        return "Sarcasm"
    return raw_label


with st.spinner("Initializing Intelligence Engines..."):
    topic_classifier = load_topic_model()
    sentiment_model = load_sentiment_model()

try:
    df = pd.read_csv("sentry_history.csv")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    # Ensure Magnitude is a float
    if 'Magnitude' in df.columns:
        df['Magnitude'] = df['Magnitude'].astype(float)
except Exception:
    df = pd.DataFrame()


# 1. Load the config file
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 2. Initialize the authenticator 
# In v0.4.2, 'pre-authorized' is optional, but it's safer to use .get()
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 3. Render the login widget
# Using the new syntax: location must be 'main', 'sidebar', or 'unrendered'
authenticator.login(location='main')

# 4. BRIDGE VARIABLES: This fixes the NameErrors in the rest of your app
auth_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")

# 5. Handle Authentication Logic
if auth_status:
    # Logic for successful login
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{name}*')
    
    # --- YOUR ACTUAL APP CODE STARTS HERE ---
    st.title("My Dashboard")
    # ... everything else you built ...

elif auth_status is False:
    st.error('Username/password is incorrect')
elif auth_status is None:
    st.warning('Please enter your username and password')

st.sidebar.title(f"Welcome, {name}")
authenticator.logout("Logout", "sidebar")
st.sidebar.markdown("---")

if st.session_state.new_post_count > 0 and not df.empty:
    with st.sidebar.popover(f"🔔 Notifications ({st.session_state.new_post_count})", use_container_width=True):
        st.markdown("### Recent Intelligence")
        recent_hits = df.sort_values(by='Timestamp', ascending=False).head(st.session_state.new_post_count)
        
        for _, row in recent_hits.iterrows():
            time_label = get_time_ago(row['Timestamp'])
            cols = st.columns([0.2, 0.8])
            with cols[0]:
                icon = {"Negative": "🚨", "Sarcasm": "🧐", "Positive": "✅"}.get(row['Sentiment'], "📄")
                st.write(icon)
            with cols[1]:
                st.markdown(f"**{row['Username']}**")
                st.caption(f"{row['Content'][:45]}... • {time_label}")
            st.divider()
        
        if st.button("Mark all as Read", use_container_width=True):
            st.session_state.new_post_count = 0
            st.rerun()

subreddit = st.sidebar.text_input("Subreddit", "exiglesianicristo")

if subreddit:
    raw_posts = fetch_recent_posts(subreddit, limit=10)
    if raw_posts:
        auto_new = []
        new_entries = []
        for p in raw_posts:
            if not df.empty and p['Content'] in df['Content'].values:
                continue
            
            intel = get_sentiment_roberta(p['Content'], sentiment_model)
            topic_data = classify_topics_ai(p['Content'], topic_classifier)
            
            final_sent = detect_sarcasm(p['Content'], intel['Sentiment'])
            
            p.update({
                'Sentiment': final_sent,
                'Magnitude': intel['Magnitude'],
                'Explanation': intel.get('Explanation', ''),
                'Primary_Topic': topic_data['Primary']
            })
            new_entries.append(p)

        if auto_new:
            st.session_state.new_post_count += len(auto_new)
            
            st.toast(f"{len(auto_new)} new intelligence entries detected!")
            
            new_df = pd.DataFrame(auto_new)
            df = pd.concat([df, new_df]).drop_duplicates(subset=['Content'])
            df.to_csv("sentry_history.csv", index=False)
        else:
            # 4. Show the "Up to Date" Toast
            st.toast("Scan complete: Database is up to date.")

        if new_entries:
            new_df = pd.DataFrame(new_entries)
            df = pd.concat([df, new_df]).drop_duplicates(subset=['Content'])
            df.to_csv("sentry_history.csv", index=False)
            st.session_state.new_post_count = len(new_entries)


if st.sidebar.button("Fetch & Analyze Fresh Data"):
    with st.status(f"Manual Scan: r/{subreddit}...", expanded=True) as status:
        manual_posts = fetch_recent_posts(subreddit, limit=25) 
        if manual_posts:
            manual_new = []
            for p in manual_posts:
                if not df.empty and p['Content'] in df['Content'].values:
                    continue
                
                st.write(f"Analyzing: {p['Content'][:30]}...")
                intel = get_sentiment_roberta(p['Content'], sentiment_model)
                topic_data = classify_topics_ai(p['Content'], topic_classifier)
                
                p.update({
                    'Sentiment': detect_sarcasm(p['Content'], intel['Sentiment']),
                    'Magnitude': intel['Magnitude'],
                    'Explanation': intel.get('Explanation', ''),
                    'Primary_Topic': topic_data['Primary']
                })
                manual_new.append(p)
            
            if manual_new:
                new_df = pd.DataFrame(manual_new)
                df = pd.concat([df, new_df]).drop_duplicates(subset=['Content'])
                df.to_csv("sentry_history.csv", index=False)
                st.session_state.new_post_count += len(manual_new)
                status.update(label="Manual Sync Complete!", state="complete")
                st.rerun()
            else:
                status.update(label="Already up to date.", state="complete")
        else:
            st.sidebar.warning("No posts found.")
st.sidebar.divider()
st.sidebar.caption(f"System Heartbeat: {datetime.now().strftime('%I:%M %p')}")
st.sidebar.caption("Auto-refresh active (5m interval)")
# =========================
#  MAIN DASHBOARD UI
# =========================
st.markdown("""
<style>
.header-container { background-color: #0b1220; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
.header-title { font-size: 28px; font-weight: 700; color: white; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="header-container"><span class="header-title">🛡️ Sentinel-D: Intelligence Dashboard</span></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", "Users", "Sentiment Intel", "High Activity", "Topic Analysis", "Archive"
])

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
            fig_pie = px.pie(df, names='Sentiment', hole=0.4, title="Sentiment Distribution",
                            color='Sentiment', color_discrete_map={
                                'Negative': '#ef4444', 'Sarcasm': '#a855f7', 
                                'Neutral': '#3b82f6', 'Positive': '#22c55e'})
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_r:
            df['Date'] = df['Timestamp'].dt.date
            timeline = df.groupby('Date').size().reset_index(name='Posts')
            fig_line = px.line(timeline, x='Date', y='Posts', title="Daily Posting Activity", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

        st.divider()

        st.subheader(" Main Feed: Latest Activity")
        
        feed_df = df.sort_values(by='Timestamp', ascending=False)
        
        st.dataframe(
            feed_df[['Timestamp', 'Username', 'Content', 'Sentiment', 'Magnitude']], 
            column_config={
                "Timestamp": st.column_config.DatetimeColumn(
                    "Time Posted",
                    format="D MMM, h:mm a",
                ),
                "Username": st.column_config.TextColumn("User"),
                "Content": st.column_config.TextColumn("Post Content", width="large"),
                "Sentiment": st.column_config.TextColumn("Sentiment Tag"),
                "Magnitude": st.column_config.NumberColumn("Intensity", format="%.2f")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("The feed is currently empty. Fetch some data from the sidebar to begin.")


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

with tab4:
    st.subheader("High Activity Posts")
    if not df.empty:
        high_act = df[(df['Upvotes'] >= 30) | (df['Comment_Count'] >= 10)]
        st.dataframe(high_act[['Username', 'Content', 'Upvotes', 'Comment_Count', 'Sentiment']], use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Topic Analysis")
    if not df.empty:
        t_sel = st.selectbox("Filter Topic", ["All"] + list(df['Primary_Topic'].unique()))
        f_df = df if t_sel == "All" else df[df['Primary_Topic'] == t_sel]
        st.dataframe(f_df[['Username', 'Content', 'Primary_Topic', 'Sentiment']], use_container_width=True, hide_index=True)   

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