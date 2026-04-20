import pandas as pd

def calculate_fis(df):
    if df.empty:
        return pd.DataFrame()

    user_stats = []
    for username, group in df.groupby('Username'):
        total = len(group)
        negatives = len(group[group['Sentiment'] == 'Negative'])

        neg_ratio = negatives / total if total > 0 else 0
        fis_score = (negatives ** 2) * neg_ratio

        user_stats.append({
            'Username': username,
            'Total_Posts': total,
            'Negative_Posts': negatives,
            'FIS_Score': round(fis_score, 2)
        })

    return pd.DataFrame(user_stats).sort_values(by='FIS_Score', ascending=False)