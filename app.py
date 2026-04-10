import streamlit as st
import pandas as pd
import plotly.express as px
from utils.processor import calculate_fis
from utils.analyzer import load_sentiment_model, get_sentiment_roberta # NEW

# 1. Load the AI Model (shows a spinner while loading)
with st.spinner("Initializing RoBERTa Intelligence Engine..."):
    classifier = load_sentiment_model()

# 2. Update Mock Data with REAL AI analysis
if 'mock_data' not in st.session_state:
    raw_texts = [
        "This church leadership is doing a great job.",
        "I am so tired of the constant criticism here.",
        "Does anyone know the schedule for Sunday?",
        "This community is becoming a toxic echo chamber.",
        "The recent event was very inspiring and peaceful."
    ]
    usernames = ["User_Alpha", "User_Beta", "User_Gamma", "User_Alpha", "User_Delta"]
    
    # Run the model on each text
    processed_data = []
    for text, user in zip(raw_texts, usernames):
        sentiment = get_sentiment_roberta(text, classifier)
        processed_data.append({
            'Username': user,
            'Sentiment': sentiment,
            'Content': text,
            'Timestamp': pd.Timestamp.now()
        })
    
    st.session_state.mock_data = pd.DataFrame(processed_data)

# 3. Sidebar - Global Controls & Alert System
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1063/1063073.png", width=80)
st.sidebar.title("Sentry Controls")
st.sidebar.markdown("---")

# Slider for FIS Threshold
threshold = st.sidebar.slider("FIS Alert Threshold", 1.0, 15.0, 5.0)

# Global Alert Logic (Visible on all tabs)
user_analysis = calculate_fis(data)
flagged_users = user_analysis[user_analysis['FIS_Score'] >= threshold]

if not flagged_users.empty:
    st.sidebar.error(f"🚨 ALERT: {len(flagged_users)} Users Flagged")
    st.sidebar.warning(f"Top Offender: {flagged_users.iloc[0]['Username']}")
else:
    st.sidebar.success("✅ Discourse Intensity Stable")

st.sidebar.markdown("---")
st.sidebar.info("Sentry: Monitoring Religious Discourse on Reddit (Thesis v1.0)")

# 4. Main Dashboard UI
st.title("🛡️ Sentry Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Discourse Overview", "🚩 Flagged Users", "🔍 Content Archive"])

with tab1:
    # Contextual Alert for Administrators
    counts = data['Sentiment'].value_counts()
    neg_perc = (counts.get('Negative', 0) / len(data)) * 100
    
    if neg_perc > 50:
        st.warning(f"Critically High Negative Sentiment Detected ({neg_perc:.1f}%)")

    st.subheader("Real-Time Sentiment Triage")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Posts", len(data))
    m2.metric("Negative", counts.get('Negative', 0), delta="High Intensity", delta_color="inverse")
    m3.metric("Positive", counts.get('Positive', 0))

    # Visualization
    fig = px.pie(data, names='Sentiment', color='Sentiment', hole=0.4,
                 color_discrete_map={'Negative':'#EF553B', 'Neutral':'#636EFA', 'Positive':'#00CC96'})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Persistent Bad Actors (User Watchlist)")
    
    if not flagged_users.empty:
        # 1. Display the table
        st.dataframe(
            flagged_users.style.background_gradient(subset=['FIS_Score'], cmap='Reds'),
            use_container_width=True
        )
        
        # 2. Add a 'Confirm Flag' action
        st.markdown("### Administrative Actions")
        target_user = st.selectbox("Select User to Officialy Flag:", flagged_users['Username'])
        
        if st.button(f"Confirm Flag for {target_user}"):
            from utils.processor import save_flagged_user
            score = flagged_users[flagged_users['Username'] == target_user]['FIS_Score'].values[0]
            
            if save_flagged_user(target_user, score):
                st.success(f"User {target_user} has been added to the Permanent Watchlist.")
                st.toast("Database Updated!")
            else:
                st.info(f"User {target_user} is already in the database.")
    else:
        st.write("No users currently exceed the threshold.")

with tab3:
    st.subheader("Raw Activity Log")
    search = st.text_input("Search Username", "")
    if search:
        filtered_data = data[data['Username'].str.contains(search, case=False)]
        st.table(filtered_data)
    else:
        st.table(data.sort_values(by='Timestamp', ascending=False))