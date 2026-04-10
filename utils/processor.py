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