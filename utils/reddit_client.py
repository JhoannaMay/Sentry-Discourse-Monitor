import requests
import pandas as pd

def fetch_recent_posts(subreddit_name, limit=25):
    url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 SentryThesis/3.0"}

    inc_keywords = [
    # Official Names & Abbreviations
    'inc', 'iglesia ni cristo', 'church of christ', 'i.n.c', 
    
    # Leadership (Past & Present)
    'manalo', 'evm', 'fym', 'egm', 'angelo manalo',
    
    # Places & Events
    'central temple', 'pabahay', 'philippine arena', 'lingap', 'sta cena', 'bnh',
    
    # Doctrines & Terms
    'doktrina', 'leksyon', 'akay', 'handog', 'tanging handog', 'pagsamba', 'worship service',
    
    # Community & Slang (Common in r/exiglesianicristo)
    'kulto', 'owes', 'handog', 'lokal', 'distrito', 'scan', 'pananalapi', 'pauwi'
]   

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        posts = []
        for post in data['data']['children']:
            p = post['data']
            content = f"{p.get('title','')} {p.get('selftext','')}"

            posts.append({
                'Username': p.get('author', 'anonymous'),
                'Content': content,
                'Timestamp': pd.to_datetime(p.get('created_utc', 0), unit='s')
            })

        return posts

    except Exception as e:
        print(e)
        return []