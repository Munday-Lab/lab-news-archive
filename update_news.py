import os
import re
import json
import urllib.request
from datetime import datetime

# URL to fetch the feed data
API_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=mundaylab.bsky.social&limit=50"

def clean_text(text):
    if not text:
        return ""
    
    # 1. Remove trailing stacked handles/tags at the literal end of the post
    text = re.sub(r'(\s*(?:[#@]\S+\s*)+)$', '', text)
    
    # 2. Process remaining mid-sentence handles (@) and hashtags (#)
    # This matches the word and groups any trailing punctuation to protect it
    def format_match(match):
        word = match.group(1)
        punctuation = match.group(2) or ""
        
        # Split normal CamelCase (e.g., JohnDoe -> John Doe)
        word = re.sub(r'([a-z])([A-Z])', r'\1 \2', word)
        # Split acronyms leading into mixed case (e.g., IOPPublishing -> IOP Publishing)
        word = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', word)
        # Split letters and numbers (e.g., Lab2026 -> Lab 2026)
        word = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', word)
        word = re.sub(r'([0-9])([a-zA-Z])', r'\1 \2', word)
        
        return word + punctuation

    text = re.sub(r'[#@](\w+)(\b|[.,!?:\s]|$)', format_match, text)
    
    # 3. Clean up any resulting double spaces
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text

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
                    
                    # Ignore replies to keep the feed clean
                    if record.get('reply'):
                        continue
                        
                    text = record.get('text', '')
                    cleaned_text = clean_text(text)
                    
                    # --- REQ 2: Resolve Image (Standard vs. External link thumbnails) ---
                    image_url = None
                    embed = post_data.get('embed', {})
                    
                    if embed:
                        # Case A: Standard uploaded image
                        if 'images' in embed and len(embed['images']) > 0:
                            image_url = embed['images'][0].get('thumb')
                        # Case B: External link card preview thumbnail (e.g., UC Davis story)
                        elif 'external' in embed and isinstance(embed['external'], dict):
                            image_url = embed['external'].get('thumb')
                    
                    # Grab created timestamp
                    created_at = record.get('createdAt', '')
                    
                    posts.append({
                        "text": cleaned_text,
                        "image": image_url,
                        "createdAt": created_at,
                        "uri": post_data.get('uri', ''),
                        "fullUrl": f"https://bsky.app/profile/{post_data.get('author', {}).get('handle')}/post/{post_data.get('uri', '').split('/')[-1]}" if post_data.get('uri') else ""
                    })
                
                # Save the processed items into news.json
                with open("news.json", "w", encoding="utf-8") as f:
                    json.dump(posts, f, ensure_ascii=False, indent=2)
                print("Successfully updated news.json with link-card pictures and parsed text rules!")
                
    except Exception as e:
        print(f"Error executing feed update script: {e}")

if __name__ == "__main__":
    fetch_feed()
