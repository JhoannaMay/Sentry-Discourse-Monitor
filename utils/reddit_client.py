import requests
import pandas as pd

def fetch_recent_posts(subreddit_name, limit=25):
    url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 SentryThesis/3.0"}

    inc_keywords = [
        'inc', 'iglesia ni cristo', 'iglesia', 'i.n.c',
        'manalo', 'evm', 'kulto', 'doktrina'
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