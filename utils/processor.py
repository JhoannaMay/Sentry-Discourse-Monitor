import pandas as pd

def calculate_fis(df):
    if df.empty or 'Magnitude' not in df.columns:
        return pd.DataFrame()

    user_stats = []
    for username, group in df.groupby('Username'):
        total = len(group)
        neg_group = group[group['Sentiment'] == 'Negative']
        neg_count = len(neg_group)
        
        avg_magnitude = group['Magnitude'].mean()
        avg_intensity = neg_group['Magnitude'].mean() if neg_count > 0 else 0

        fis_score = neg_count * avg_intensity
 
        user_stats.append({
            'Username': username,
            'Posts': total,
            'Neg_Posts': neg_count,
            'Avg_Magnitude': round(avg_magnitude, 2),
            'Avg_Intensity': round(avg_intensity, 2),
            'FIS_Score': round(fis_score, 2)
        })

    return pd.DataFrame(user_stats).sort_values(by='FIS_Score', ascending=False)