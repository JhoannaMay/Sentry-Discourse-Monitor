import streamlit as st
import pandas as pd
import plotly.express as px
import time
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import datetime

from streamlit_autorefresh import st_autorefresh

from utils.analyzer import load_sentiment_model, get_sentiment_roberta
from utils.processor import calculate_fis
from utils.reddit_client import fetch_recent_posts
from utils.ai_topic_classifier import load_topic_model, classify_topics_ai



count = st_autorefresh(interval=300000, key="fitchcounter")

# PAGE CONFIG
st.set_page_config(page_title="Sentinel-D: INC Intelligence", layout="wide")

if 'new_post_count' not in st.session_state:
    st.session_state.new_post_count = 0


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

# 🔔 NOTIFICATION OVERLAY

if st.session_state.new_post_count > 0:
    st.markdown(f"""
        <div class="notification-box">
            🔔 {st.session_state.new_post_count} New Posts Detected
        </div>
    """, unsafe_allow_html=True)
    
    # Add a small clear button right below the header or in the sidebar
    if st.sidebar.button("Clear Notifications"):
        st.session_state.new_post_count = 0
        st.rerun()

st.sidebar.write(f"Welcome, {name}")
authenticator.logout("Logout", "sidebar")
# Sidebar Badge
notif_label = f"🔔 Notifications ({st.session_state.new_post_count})"
if st.sidebar.button(notif_label):
    st.toast(f"You have {st.session_state.new_post_count} new updates to review in the Dataset tab!")

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

    # 🛡️ SAFETY CHECK: Create missing columns if they don't exist
    if 'Upvotes' not in df.columns:
        df['Upvotes'] = 0
    if 'Comment_Count' not in df.columns:
        df['Comment_Count'] = 0
        
    # Standard cleaning
    df['Sentiment'] = df['Sentiment'].fillna("Neutral")
    df['Primary_Topic'] = df['Primary_Topic'].fillna("General")

except Exception as e:
    df = pd.DataFrame()



# =========================
# 📡 FETCH DATA & NOTIFICATION LOGIC
# =========================
subreddit = st.sidebar.text_input("Subreddit", "exiglesianicristo")

# Initialize session state for notifications if it doesn't exist
if 'new_post_count' not in st.session_state:
    st.session_state.new_post_count = 0

if st.sidebar.button("Fetch & Analyze"):
    posts = fetch_recent_posts(subreddit)
    
    if posts:
        new_fetched_df = pd.DataFrame(posts)
        
        # Compare with existing data to find truly 'new' entries
        if not df.empty:
            # We identify new posts by checking which 'Content' isn't in our current CSV
            new_entries = new_fetched_df[~new_fetched_df['Content'].isin(df['Content'])]
            st.session_state.new_post_count = len(new_entries)
        else:
            st.session_state.new_post_count = len(new_fetched_df)

        # Merge and save
        df = pd.concat([df, new_fetched_df]).drop_duplicates(subset=['Content'])
        df.to_csv("sentry_history.csv", index=False)
        
        # Immediate feedback
        if st.session_state.new_post_count > 0:
            st.toast(f"🚀 Found {st.session_state.new_post_count} new posts!")
        
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "👤 Users",
    "📂 Dataset",
    "🧠 Topic Analysis",
    "High Activity Posts"
])

# =========================
# 📊 OVERVIEW TAB
# =========================
with tab1:
    st.subheader("System Intelligence Overview")

    # --- 1. METRICS ROW ---
    if not df.empty:
    # 🟢 FIX: Clean the sentiment column before counting
    # This replaces anything not in the 'Big Three' with 'Neutral'
        df['Sentiment'] = df['Sentiment'].fillna('Neutral')
        df.loc[~df['Sentiment'].isin(['Positive', 'Neutral', 'Negative']), 'Sentiment'] = 'Neutral'
    
        counts = df['Sentiment'].value_counts()

        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Negative", counts.get('Negative', 0))
        c2.metric("🔵 Neutral", counts.get('Neutral', 0))
        c3.metric("🟢 Positive", counts.get('Positive', 0))
    
        st.divider()

        # --- 2. TOPIC & KEYWORDS ROW ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### 📂 Topic Distribution")
            fig = px.pie(df, names='Primary_Topic', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("### 📈 Key Intelligence Terms")
            
            # Professional Keyword Extraction
            import re
            from collections import Counter

            # Filter for non-useful words
            STOP_WORDS = set([
                'about', 'would', 'there', 'their', 'what', 'which', 'will', 'your', 
                'from', 'they', 'have', 'this', 'that', 'with', 'here', 'also', 'some'
            ])

            all_text = " ".join(df['Content'].dropna()).lower()
            # Regex [a-z]{3,} allows 'inc' and 'evm' to be caught
            raw_words = re.findall(r'\b[a-z]{3,}\b', all_text)
            meaningful_words = [w for w in raw_words if w not in STOP_WORDS]

            common = Counter(meaningful_words).most_common(10)
            kw_df = pd.DataFrame(common, columns=['Term', 'Frequency'])

            fig_kw = px.bar(
                kw_df, 
                x='Frequency', 
                y='Term', 
                orientation='h',
                color='Frequency',
                color_continuous_scale='Blues'
            )
            fig_kw.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_kw, use_container_width=True)

        st.divider()

        # --- 3. REFINED MAIN FEED ---
        st.markdown("### 📰 Recent Intelligence Feed")
        
        # Display only the columns you need
        display_cols = ['Username', 'Content', 'Sentiment', 'Timestamp']
        
        # Sort by newest first and clean the view
        feed_df = df.sort_values(by='Timestamp', ascending=False)[display_cols]
        
        st.dataframe(
            feed_df, 
            use_container_width=True, 
            hide_index=True
        )

    else:
        st.info("📡 No data available. Use the sidebar to fetch recent posts from Reddit.")

with tab2:
    st.subheader("User Activity Insights")

    if not df.empty:
        # 1. Create a clean summary table of active users
        user_counts = df['Username'].value_counts().reset_index()
        user_counts.columns = ['Username', 'Total Posts']

        # 2. Layout: Sidebar-style selection within the tab
        col_select, col_stats = st.columns([1, 2])

        with col_select:
            selected_user = st.selectbox("Search/Select a User", user_counts['Username'])
            
            # Simple User Metric
            user_total = user_counts[user_counts['Username'] == selected_user]['Total Posts'].values[0]
            st.info(f"**User:** {selected_user}  \n**Activity:** {user_total} Post(s)")

        # 3. Filter data for the selected user
        user_activity_df = df[df['Username'] == selected_user]

        # 4. Display the filtered feed (Only your 4 requested columns)
        st.markdown(f"### 📑 Post History for `{selected_user}`")
        
        # Defining the "Strict 4" columns
        clean_user_df = user_activity_df[['Username', 'Content', 'Sentiment', 'Timestamp']]
        
        # Sort by newest first
        clean_user_df = clean_user_df.sort_values(by='Timestamp', ascending=False)

        st.dataframe(
            clean_user_df, 
            use_container_width=True, 
            hide_index=True
        )

        # 5. Sentiment breakdown for this specific user
        st.markdown("---")
        user_sent_counts = clean_user_df['Sentiment'].value_counts()
        
        # Mini metrics for the individual user
        m1, m2, m3 = st.columns(3)
        m1.metric("🔴 Negative", user_sent_counts.get('Negative', 0))
        m2.metric("🔵 Neutral", user_sent_counts.get('Neutral', 0))
        m3.metric("🟢 Positive", user_sent_counts.get('Positive', 0))

    else:
        st.info("No user data found. Please fetch data from the sidebar first.")

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

# =========================
# 🔥 HIGH ACTIVITY TAB (TAB 5)
# =========================
with tab5:
    st.subheader("🔥 High Activity Intelligence")
    
    if not df.empty:
        # Define Thresholds
        UPVOTE_THRESHOLD = 50
        COMMENT_THRESHOLD = 20

        # 1. Filter for High Activity
        high_df = df[(df['Upvotes'] >= UPVOTE_THRESHOLD) | (df['Comment_Count'] >= COMMENT_THRESHOLD)].copy()

        if not high_df.empty:
            # 2. Add Status Badge
            high_df['Status'] = "🟢 Saved"

            st.caption("The only editable column is **Sentiment**. Double-click a sentiment cell to change it.")

            # 3. 🎯 THE SELECTIVE EDITOR
            # We list all columns, but 'disabled' locks the ones you don't want to touch
            edited_df = st.data_editor(
                high_df[['Status', 'Username', 'Content', 'Sentiment', 'Upvotes', 'Comment_Count', 'Timestamp']],
                column_config={
                    "Sentiment": st.column_config.SelectboxColumn(
                        "Sentiment",
                        help="Change the AI's classification",
                        options=["Negative", "Neutral", "Positive"],
                        required=True,
                    ),
                    # Lock all other columns here:
                    "Status": st.column_config.TextColumn("Status", disabled=True),
                    "Username": st.column_config.TextColumn("Username", disabled=True),
                    "Content": st.column_config.TextColumn("Content", width="large", disabled=True),
                    "Upvotes": st.column_config.NumberColumn("Upvotes", disabled=True),
                    "Comment_Count": st.column_config.NumberColumn("Comments", disabled=True),
                    "Timestamp": st.column_config.DatetimeColumn("Timestamp", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                key="high_activity_editor"
            )

            # 4. Check for unsaved changes
            has_changes = not edited_df['Sentiment'].equals(high_df['Sentiment'])

            if has_changes:
                st.warning("🟡 Changes detected. Click below to save to your database.")
                if st.button("💾 Commit Changes"):
                    # Update main df by matching Content
                    for index, row in edited_df.iterrows():
                        df.loc[df['Content'] == row['Content'], 'Sentiment'] = row['Sentiment']
                    
                    # Save to CSV
                    df.to_csv("sentry_history.csv", index=False)
                    st.success("✅ Dataset updated!")
                    st.rerun()
            else:
                st.write("✨ Database is up to date.")

        else:
            st.success("✅ No posts currently meet the High Activity threshold.")
    else:
        st.info("No data available.")