import os
import django
import urllib.request
import json
import time
from django.utils.text import slugify
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

def fetch_gamepix_games(target=10000):
    games_per_page = 100
    pages = target // games_per_page
    total_inserted = 0
    
    print(f"Starting GamePix scrape. Target: {target} games.")
    
    for page in range(1, pages + 1):
        url = f"https://games.gamepix.com/games?limit={games_per_page}&page={page}"
        print(f"Fetching page {page}...")
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if 'data' not in data or not data['data']:
                print("No more data received.")
                break
                
            to_create = []
            for item in data['data']:
                title = item.get('title', 'Unknown')
                desc = item.get('description', f'Play {title} free online!')
                
                iframe_url = item.get('url')
                thumbnail_url = item.get('thumbnailUrl', '')
                cat = item.get('category', 'Action')
                
                slug = slugify(title) + '-' + str(uuid.uuid4())[:8]
                
                if title and iframe_url and thumbnail_url:
                    to_create.append(Game(
                        title=title,
                        slug=slug,
                        description=desc,
                        thumbnail_url=thumbnail_url,
                        iframe_url=iframe_url,
                        category=cat,
                    ))
            
            if to_create:
                Game.objects.bulk_create(to_create, ignore_conflicts=True)
                total_inserted += len(to_create)
                print(f"Inserted {len(to_create)} games from page {page}. Total: {total_inserted}")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            
    print(f"✅ GamePix scraping complete! Added {total_inserted} high-quality games.")

if __name__ == '__main__':
    fetch_gamepix_games(10000)
