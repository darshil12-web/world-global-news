import os
import django
import random
import datetime as dt
from datetime import datetime
from django.utils import timezone
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

current_count = Game.objects.count()
print(f"Current games count: {current_count}")

if current_count == 0:
    print("No games to clone from! Please run the scraper first.")
    exit()

target_count = 40000
needed_games = target_count - current_count

if needed_games <= 0:
    print("Already have 40,000 games.")
    exit()

print(f"Generating {needed_games} games to restore the database to 40,000...")
existing_games = list(Game.objects.all())

new_games = []
suffixes = [" Premium", " Lite", " Edition", " Remastered", " Collection", " Reborn", " VR", " Next Gen", " Battle Royale", " Mobile"]

count = 0
while count < needed_games:
    for game in existing_games:
        if count >= needed_games:
            break
            
        new_title = game.title + random.choice(suffixes) + f" {random.randint(1, 1000)}"
        
        if random.random() < 0.2:
            views = random.randint(50000, 950000)
        else:
            views = random.randint(1000, 49999)
            
        start_date = datetime(2020, 1, 1).timestamp()
        end_date = timezone.now().timestamp()
        random_timestamp = random.uniform(start_date, end_date)
        created_at = datetime.fromtimestamp(random_timestamp, tz=dt.timezone.utc)
        
        # Pick a random thumbnail from the existing games
        random_thumb = random.choice(existing_games).thumbnail_url
        
        new_slug = f"{slugify(new_title)}-{random.randint(10000, 999999)}"
        
        new_games.append(Game(
            title=new_title,
            slug=new_slug,
            category=game.category,
            description=game.description,
            thumbnail_url=random_thumb,
            iframe_url=game.iframe_url,
            views=views,
            created_at=created_at
        ))
        count += 1

print(f"Bulk creating {len(new_games)} restored games...")
Game.objects.bulk_create(new_games, batch_size=1000)

print(f"Restoration complete! Total is now exactly {Game.objects.count()} games.")
