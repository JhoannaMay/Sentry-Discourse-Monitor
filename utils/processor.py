import pandas as pd

def calculate_fis(df):
    """
    Sentry Logic: FIS = (Negative Volume) * (Frequency Factor)
    This represents the 'User Flagging' component of the thesis.
    """
    if df.empty:
        return pd.DataFrame()

    # Group data by User
    user_groups = df.groupby('Username')
    
    stats = []
    for name, group in user_groups:
        total = len(group)
        negatives = len(group[group['Sentiment'] == 'Negative'])
        
        # Frequency: How consistent is their negativity?
        neg_ratio = negatives / total if total > 0 else 0
        
        # FIS Calculation: Penalizes high volume and high ratio
        # Formula: (Negative Count ^ 1.5) * Ratio
        fis_score = (negatives ** 1.5) * neg_ratio
        
        stats.append({
            'Username': name,
            'Total Posts': total,
            'Negative Posts': negatives,
            'FIS_Score': round(fis_score, 2)
        })
        
    return pd.DataFrame(stats).sort_values(by='FIS_Score', ascending=False)

def save_flagged_user(username, fis_score):
    """
    Saves a flagged user to a local CSV database.
    This fulfills the 'User Flagging System' part of the thesis.
    """
    try:
        # Load existing database or create new one
        try:
            db = pd.read_csv('flagged_database.csv')
        except FileNotFoundError:
            db = pd.DataFrame(columns=['Date_Flagged', 'Username', 'FIS_Score', 'Status'])
        
        # Check if user is already flagged
        if username not in db['Username'].values:
            new_entry = {
                'Date_Flagged': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
                'Username': username,
                'FIS_Score': fis_score,
                'Status': 'Under Review'
            }
            db = pd.concat([db, pd.DataFrame([new_entry])], ignore_index=True)
            db.to_csv('flagged_database.csv', index=False)
            return True
        return False
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False