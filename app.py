import streamlit as st
import pandas as pd
from utils.processor import calculate_fis  # Import our logic
import plotly.express as px

st.set_page_config(page_title="Sentry Dashboard", layout="wide")

# --- DATASET SIMULATION ---
# (In the future, this is where the Reddit API data will go)
mock_data = pd.DataFrame({
    'Username': ['User_Alpha', 'User_Beta', 'User_Alpha', 'User_Gamma', 'User_Beta'],
    'Sentiment': ['Negative', 'Neutral', 'Negative', 'Positive', 'Negative'],
    'Content': ['Hate speech sample', 'Info post', 'Another attack', 'God bless', 'Harassment'],
    'Timestamp': pd.to_datetime(['2023-10-01', '2023-10-01', '2023-10-02', '2023-10-02', '2023-10-03'])
})

# --- SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1063/1063073.png", width=100)
st.sidebar.title("Sentry Controls")
threshold = st.sidebar.slider("FIS Alert Threshold", 1.0, 10.0, 5.0)

# --- MAIN UI TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Discourse Overview", "🚩 Flagged Users", "🔍 Content Archive"])

with tab1:
    st.subheader("Real-Time Sentiment Triage")
    col1, col2, col3 = st.columns(3)
    
    counts = mock_data['Sentiment'].value_counts()
    col1.metric("Total Analyzed", len(mock_data))
    col2.metric("Negative Sentiment", counts.get('Negative', 0), delta="Critical", delta_color="inverse")
    col3.metric("Positive Sentiment", counts.get('Positive', 0))

    # Sentiment Chart
    fig = px.pie(mock_data, names='Sentiment', color='Sentiment',
                 color_discrete_map={'Negative':'#EF553B', 'Neutral':'#636EFA', 'Positive':'#00CC96'})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Persistent Bad Actors (High FIS)")
    user_analysis = calculate_fis(mock_data)
    
    # Flagging logic
    flagged = user_analysis[user_analysis['FIS_Score'] >= threshold]
    
    if not flagged.empty:
        st.error(f"ALERT: {len(flagged)} users have exceeded the intensity threshold!")
        st.dataframe(flagged.style.background_gradient(subset=['FIS_Score'], cmap='Reds'))
    else:
        st.success("Monitoring active: No users currently meet flagging criteria.")

with tab3:
    st.subheader("Recent Reddit Activity")
    st.table(mock_data[['Timestamp', 'Username', 'Sentiment', 'Content']])