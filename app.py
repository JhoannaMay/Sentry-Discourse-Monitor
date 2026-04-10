import streamlit as st
import pandas as pd
import plotly.express as px
from utils.processor import calculate_fis

# 1. Page Configuration
st.set_page_config(page_title="Sentry | Religious Discourse Monitor", layout="wide")

# 2. Mock Data Simulation (Phase 4/5 Placeholder)
# This simulates the data we will eventually pull from Reddit PRAW
if 'mock_data' not in st.session_state:
    st.session_state.mock_data = pd.DataFrame({
        'Username': ['User_Alpha', 'User_Beta', 'User_Alpha', 'User_Gamma', 'User_Beta', 'User_Delta', 'User_Alpha'],
        'Sentiment': ['Negative', 'Neutral', 'Negative', 'Positive', 'Negative', 'Negative', 'Negative'],
        'Content': [
            'Attacking religious beliefs...', 
            'General inquiry about schedule.', 
            'Repeated hateful rhetoric.', 
            'God bless everyone!', 
            'Negative comment on leadership.', 
            'Aggressive criticism.', 
            'Persistent harassment.'
        ],
        'Timestamp': pd.to_datetime([
            '2023-10-01 10:00', '2023-10-01 10:05', '2023-10-01 11:00', 
            '2023-10-02 09:00', '2023-10-02 10:00', '2023-10-03 08:30', '2023-10-03 09:15'
        ])
    })

data = st.session_state.mock_data

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