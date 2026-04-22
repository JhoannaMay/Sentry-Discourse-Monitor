import requests
import pandas as pd

def fetch_recent_posts(subreddit_name, limit=25):
    # Standardize the name (remove r/ if the user included it)
    clean_name = subreddit_name.replace("r/", "").strip()
    
    url = f"https://www.reddit.com/r/{clean_name}/new.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 SentryThesis/3.0"}

    # 🛡️ THE INTELLIGENCE SHIELD: Strict filtering for your thesis
    inc_keywords = [
        'inc', 'iglesia ni cristo', 'manalo', 'evm', 'fym', 
        'central temple', 'philippine arena', 'lingap', 
        'doktrina', 'pagsamba', 'kulto', 'brainwash', 'scam', 'handog',
        'ministros', 'minister', 'kadiwa', 'kawan', 'binhi', 's ugo',
        'tagapamahala', 'tagapamahalang pangkalahatan', 'tagapangasiwa',
        'manalo','iglesia','cristo','inc-related','inc discourse'
    ]

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        posts = []

        for post in data['data']['children']:
            p = post['data']
            content = f"{p.get('title','')} {p.get('selftext','')}"
            content_lower = content.lower()

            # 🧠 THE "STRICT SHIELD" CHECK
            # We use Regex to ensure we only find WHOLE words (prevents 'income'/'incomplete')
            is_relevant = False
            for key in strict_keywords:
                # \b checks for word boundaries (start/end of a word)
                if re.search(r'\b' + re.escape(key) + r'\b', content_lower):
                    is_relevant = True
                    break
            
            # Special case for 'inc' - only allow if it's uppercase or specific
            if not is_relevant and "INC" in content: # Check for uppercase 'INC' specifically
                 is_relevant = True

            if is_relevant:
                posts.append({
                    'Username': p.get('author', 'anonymous'),
                    'Content': content,
                    'Timestamp': pd.to_datetime(p.get('created_utc', 0), unit='s'),
                    'Subreddit': clean_name,
                    'Upvotes': p.get('score', 0),
                    'Comment_Count': p.get('num_comments', 0)
                })
                
        return posts    
    except Exception as e:
        print(f"Error fetching from r/{clean_name}: {e}")
        return []