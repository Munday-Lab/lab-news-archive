import os
import json
import urllib.request

# URL to fetch the feed data
API_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=mundaylab.bsky.social&limit=50"

def fetch_feed():
    try:
        # 1. Load existing historical entries if the file exists
        existing_posts = []
        if os.path.exists("news.json"):
            try:
                with open("news.json", "r", encoding="utf-8") as f:
                    existing_posts = json.load(f)
                    if not isinstance(existing_posts, list):
                        existing_posts = []
            except Exception as e:
                print(f"Could not read existing news.json history, starting fresh: {e}")

        # Create a set of existing URIs so we don't insert duplicate posts
        existing_uris = {post.get('uri') for post in existing_posts if post.get('uri')}

        # 2. Fetch the latest live data from Bluesky
        req = urllib.request.Request(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                new_posts = []
                
                for item in data.get('feed', []):
                    post_data = item.get('post', {})
                    uri = post_data.get('uri', '')
                    
                    # If we already have this post in our history, or it's a reply, skip it
                    if not uri or uri in existing_uris:
                        continue
                        
                    record = post_data.get('record', {})
                    if record.get('reply'):
                        continue
                        
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
                    
                    new_posts.append({
                        "text": text,
                        "facets": facets,
                        "image": image_url,
                        "createdAt": created_at,
                        "uri": uri,
                        "fullUrl": f"https://bsky.app/profile/{post_data.get('author', {}).get('handle')}/post/{uri.split('/')[-1]}"
                    })
                
                # 3. Combine them: New items go directly to the top, followed by old history
                combined_posts = new_posts + existing_posts
                
                # 4. Save everything back down safely
                with open("news.json", "w", encoding="utf-8") as f:
                    json.dump(combined_posts, f, ensure_ascii=False, indent=2)
                    
                print(f"Successfully processed feed! Added {len(new_posts)} new posts. Total entries: {len(combined_posts)}")
                
    except Exception as e:
        print(f"Error executing feed update script: {e}")

if __name__ == "__main__":
    fetch_feed()
