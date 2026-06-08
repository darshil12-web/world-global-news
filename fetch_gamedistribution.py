import os
import django
import urllib.request
import json
import time
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

def fetch_gd_games(target_amount=40000):
    page = 1
    total_inserted = 0
    games_per_page = 100
    
    print(f"Starting GameDistribution scrape. Target: {target_amount} games.")
    
    while total_inserted < target_amount:
        url = f"https://catalog.api.gamedistribution.com/api/v2.0/rss/All/?format=json&amount={games_per_page}&page={page}"
        print(f"Fetching page {page}...")
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if not data:
                print("No more data received. Stopping.")
                break
                
            to_create = []
            for game_data in data:
                title = game_data.get('Title', 'Unknown Game')
                desc = game_data.get('Description', f'Play {title} for free online!')
                iframe_url = game_data.get('Url')
                
                # Try to get the best thumbnail (prefer 512x512)
                assets = game_data.get('Asset', [])
                thumbnail_url = ""
                if assets:
                    # Try to find a square thumb
                    squares = [a for a in assets if '512x512' in a]
                    thumbnail_url = squares[0] if squares else assets[0]
                    
                categories = game_data.get('Category', [])
                tags = [t.lower() for t in game_data.get('Tag', [])]
                cat_lower = categories[0].lower() if categories else ''
                
                # Portal categories: Obby, Tycoon, Simulator, Roleplay, Shooter, Fighting, 
                # 3D Games, Action, Adventure, Arcade, Multiplayer, Puzzle, Racing, Skill, Sports
                
                import random
                
                cat = 'Action'
                if 'puzzle' in cat_lower or 'cards' in cat_lower or 'logic' in cat_lower:
                    cat = 'Puzzle'
                elif 'racing' in cat_lower or 'car' in tags or 'driving' in cat_lower:
                    cat = 'Racing'
                elif 'sports' in cat_lower or 'football' in tags or 'basketball' in tags:
                    cat = 'Sports'
                elif '.io' in cat_lower or 'multiplayer' in tags:
                    cat = 'Multiplayer'
                elif 'shooting' in cat_lower or 'guns' in tags or 'sniper' in tags:
                    cat = 'Shooter'
                elif 'fighting' in cat_lower or 'combat' in tags:
                    cat = 'Fighting'
                elif 'adventure' in cat_lower or 'rpg' in tags:
                    cat = 'Adventure'
                elif 'simulation' in cat_lower or 'management' in tags:
                    # Randomly split between Tycoon, Simulator, Roleplay
                    cat = random.choice(['Tycoon', 'Simulator', 'Roleplay'])
                elif 'agility' in cat_lower or 'parkour' in tags:
                    cat = 'Obby'
                elif 'casual' in cat_lower or 'cooking' in cat_lower:
                    cat = 'Arcade'
                elif 'skill' in cat_lower:
                    cat = 'Skill'
                elif '3d' in tags:
                    cat = '3D Games'
                else:
                    # Fallback randomizer to ensure all categories get SOME games
                    if random.random() < 0.2:
                        cat = random.choice(["Obby", "Tycoon", "Simulator", "Roleplay"])
                    else:
                        cat = random.choice(["Action", "Arcade", "Skill", "Adventure"])
                    
                # Create base slug
                import uuid
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
                print(f"Inserted {len(to_create)} games from page {page}. Total so far: {total_inserted}/{target_amount}")
            else:
                print("No valid games found on this page.")
                
            page += 1
            time.sleep(0.5) # Be gentle to their API
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            time.sleep(2)
            page += 1 # Skip broken pages
            
    print(f"✅ GameDistribution scraping complete! Successfully inserted {total_inserted} games.")

if __name__ == '__main__':
    fetch_gd_games(40000)
