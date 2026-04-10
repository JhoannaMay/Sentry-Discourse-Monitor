import requests
import pandas as pd

def fetch_recent_posts(subreddit_name, limit=25):
    url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 SentryThesis/1.0"}
    
    # Expanded keywords for deeper religious discourse detection
    inc_keywords = [
    'inc', 'iglesia ni cristo', 'iglesia', 'i.n.c', 'manalo', 
    'cool-to', 'kulto', 'evm', 'owe', 'sulong', 'tumiwalag', 'handog']

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        posts = []
        for post in data['data']['children']:
            p = post['data']
            content_raw = f"{p['title']} {p['selftext']}"
            content_lower = content_raw.lower()
            
            mentions_inc = any(key in content_lower for key in inc_keywords)
            
            posts.append({
                'Username': p['author'],
                'Content': content_raw,
                'Timestamp': pd.to_datetime(p['created_utc'], unit='s'),
                'Mentions_INC': "Yes" if mentions_inc else "No"
            })
        return posts
    except Exception as e:
        print(f"Fetch error: {e}")
        return []