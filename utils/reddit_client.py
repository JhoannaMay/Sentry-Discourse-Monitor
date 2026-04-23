import requests
import pandas as pd
import re
import time
import pytz

def fetch_recent_posts(subreddit_name, limit=10):
    """
    Hybrid Logic: Trusts r/exiglesianicristo, filters others.
    Uses cache-busting to find posts from hours ago.
    """
    clean_name = subreddit_name.replace("r/", "").strip()

    url = f"https://www.reddit.com/r/{clean_name}/new.json?limit={limit}&_={int(time.time())}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 SentryThesis/3.0"}

    strict_keywords = [
        'inc', 'iglesia ni cristo', 'manalo', 'evm', 'fym', 
        'central temple', 'philippine arena', 'lingap', 
        'pagsamba', 'kulto', 'brainwash', 'scam', 'handog',
        'ministros', 'kadiwa', 'kawan', 'binhi', 'sugo'
    ]

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []

        data = response.json()
        posts = []

        for post in data['data']['children']:
            p = post['data']
            content = f"{p.get('title', '')} {p.get('selftext', '')}"
            content_lower = content.lower()

            raw_utc = p.get('created_utc', 0)
            utc_time = pd.to_datetime(raw_utc, unit='s')
            local_tz = pytz.timezone('Asia/Manila')
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
            
            is_relevant = False
            # TRUSTED RULE: Skip filter for dedicated sub
            if clean_name.lower() in ['exiglesianicristo', 'inc_secrets']:
                is_relevant = True
            else:
                # STRICT RULE: Apply filter for general subs
                for key in strict_keywords:
                    if re.search(r'\b' + re.escape(key) + r'\b', content_lower):
                        is_relevant = True
                        break
                if not is_relevant and "INC" in content:
                    is_relevant = True

            if is_relevant:
                posts.append({
                    'ID': p.get('id'),
                    'Username': p.get('author', 'anonymous'),
                    'Content': content.strip(),
                    'Timestamp': pd.to_datetime(p.get('created_utc', 0), unit='s'),
                    'Subreddit': clean_name
                })
        return posts    
    except Exception:
        return []