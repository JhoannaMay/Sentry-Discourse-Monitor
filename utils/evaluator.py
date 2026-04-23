import pandas as pd
import os

def log_audit(username, content, ai_sentiment, human_sentiment, notes=""):
    """
    Logs manual verification of AI results for Thesis Phase 6.
    """
    file = 'evaluation_log.csv'
    is_correct = 1 if ai_sentiment == human_sentiment else 0
    
    new_entry = pd.DataFrame([{
        'Timestamp': pd.Timestamp.now(),
        'Username': username,
        'Content': content[:100], 
        'AI_Label': ai_sentiment,
        'Human_Label': human_sentiment,
        'Is_Correct': is_correct,
        'Notes': notes
    }])
    
    if not os.path.isfile(file):
        new_entry.to_csv(file, index=False)
    else:
        new_entry.to_csv(file, mode='a', header=False, index=False)