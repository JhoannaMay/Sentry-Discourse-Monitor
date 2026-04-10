import streamlit as st
import pandas as pd
import plotly.express as px
from utils.processor import calculate_fis
from utils.analyzer import load_sentiment_model, get_sentiment_roberta

# 1. Page Configuration
st.set_page_config(page_title="Sentry | Religious Discourse Monitor", layout="wide")

# 2. Initialize AI Model
with st.spinner("Initializing Multilingual Sentiment Engine..."):
    classifier = load_sentiment_model()

# 3. Data Initialization & Persistence (Includes Datetime Fix)
if 'mock_data' not in st.session_state:
    try:
        df_loaded = pd.read_csv("sentry_history.csv")
        # Ensure Timestamp is converted from string to datetime objects
        df_loaded['Timestamp'] = pd.to_datetime(df_loaded['Timestamp'], errors='coerce')
        st.session_state.mock_data = df_loaded.dropna(subset=['Timestamp'])
    except FileNotFoundError:
        st.session_state.mock_data = pd.DataFrame(columns=['Username', 'Sentiment', 'Content', 'Timestamp', 'Mentions_INC'])

data = st.session_state.mock_data

# 4. Sidebar Controls
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1063/1063073.png", width=80)
st.sidebar.title("Sentry Controls")

st.sidebar.markdown("### Live Data Feed")
subreddit_input = st.sidebar.text_input("Enter Subreddit", "exiglesianicristo")

if st.sidebar.button("Fetch & Analyze Live Data"):
    from utils.reddit_client import fetch_recent_posts
    with st.spinner(f"Fetching from r/{subreddit_input}..."):
        new_posts = fetch_recent_posts(subreddit_input)
        if new_posts:
            for p in new_posts:
                p['Sentiment'] = get_sentiment_roberta(p['Content'], classifier)
            
            new_df = pd.DataFrame(new_posts)
            new_df['Timestamp'] = pd.to_datetime(new_df['Timestamp'])
            
            # Combine, deduplicate, and save
            combined_df = pd.concat([data, new_df]).drop_duplicates(subset=['Content'])
            combined_df.to_csv("sentry_history.csv", index=False)
            
            st.session_state.mock_data = combined_df
            st.sidebar.success(f"Added {len(new_posts)} new posts!")
            st.rerun()

st.sidebar.markdown("---")
threshold = st.sidebar.slider("FIS Alert Threshold", 1.0, 15.0, 5.0)

user_analysis = calculate_fis(data)
flagged_users = user_analysis[user_analysis['FIS_Score'] >= threshold] if not user_analysis.empty else pd.DataFrame()

if not flagged_users.empty:
    st.sidebar.error(f"🚨 ALERT: {len(flagged_users)} Users Flagged")
else:
    st.sidebar.success("✅ Discourse Stable")

# 5. Main Dashboard UI
st.title("🛡️ Sentry Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Discourse Overview", "🚩 Flagged Users", "🔍 Content Archive"])

with tab1:
    if not data.empty:
        st.subheader("Discourse Sentiment Analysis")
        sentiment_colors = {'Negative': '#ff4b4b', 'Neutral': '#00ccff', 'Positive': '#00cc96'}
        
        c1, c2, c3 = st.columns(3)
        counts = data['Sentiment'].value_counts()
        c1.metric("🔴 Negative", counts.get('Negative', 0))
        c2.metric("🔵 Neutral", counts.get('Neutral', 0))
        c3.metric("🟢 Positive", counts.get('Positive', 0))

        col_left, col_right = st.columns(2)
        with col_left:
            fig_bar = px.bar(counts.reset_index(), x='count', y='Sentiment', orientation='h',
                             color='Sentiment', color_discrete_map=sentiment_colors, title="Sentiment Frequency")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col_right:
            # Re-ensure datetime for grouping
            data['Timestamp'] = pd.to_datetime(data['Timestamp'])
            trend_data = data.groupby([data['Timestamp'].dt.date, 'Sentiment']).size().reset_index(name='Count')
            fig_line = px.line(trend_data, x='Timestamp', y='Count', color='Sentiment',
                               color_discrete_map=sentiment_colors, title="Sentiment Trends Over Time")
            st.plotly_chart(fig_line, use_container_width=True)

        if 'Mentions_INC' in data.columns:
            st.markdown("---")
            inc_data = data[data['Mentions_INC'] == "Yes"]
            st.subheader(f"Church-Specific Analysis ({len(inc_data)} mentions detected)")
            if not inc_data.empty:
                st.dataframe(inc_data[['Username', 'Sentiment', 'Content']].head(10), use_container_width=True)
    else:
        st.info("Dashboard empty. Please fetch data from the sidebar.")

with tab2:
    st.subheader("Persistent Bad Actors (User Watchlist)")
    if not flagged_users.empty:
        st.dataframe(flagged_users.style.background_gradient(subset=['FIS_Score'], cmap='Reds'), use_container_width=True)
    else:
        st.write("No users currently flagged.")

with tab3:
    st.subheader("Raw Activity Log")
    st.dataframe(data.sort_values(by='Timestamp', ascending=False), use_container_width=True)