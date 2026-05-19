import os
import json
import urllib.request

# URL to fetch the feed data
API_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=mundaylab.bsky.social&limit=50"

def fetch_feed():
    try:
        req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                posts = []
                
                for item in data.get('feed', []):
                    post_data = item.get('post', {})
                    record = post_data.get('record', {})
                    
                    # Ignore replies
                    if record.get('reply'):
                        continue
                        
                    # Keep raw text and raw facets for the JavaScript link builder
                    text = record.get('text', '')
                    facets = record.get('facets', [])
                    
                    # Resolve Image (Standard vs External links)
                    image_url = None
                    embed = post_data.get('embed', {})
                    if embed:
                        if 'images' in embed and len(embed['images']) > 0:
                            image_url = embed['images'][0].get('thumb')
                        elif 'external' in embed and isinstance(embed['external'], dict):
                            image_url = embed['external'].get('thumb')
                    
                    created_at = record.get('createdAt', '')
                    
                    posts.append({
                        "text": text,
                        "facets": facets,
                        "image": image_url,
                        "createdAt": created_at,
                        "uri": post_data.get('uri', ''),
                        "fullUrl": f"https://bsky.app/profile/{post_data.get('author', {}).get('handle')}/post/{post_data.get('uri', '').split('/')[-1]}" if post_data.get('uri') else ""
                    })
                
                with open("news.json", "w", encoding="utf-8") as f:
                    json.dump(posts, f, ensure_ascii=False, indent=2)
                print("Successfully updated news.json!")
                
    except Exception as e:
        print(f"Error executing feed update script: {e}")

if __name__ == "__main__":
    fetch_feed()
