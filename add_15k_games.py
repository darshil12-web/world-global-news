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

print("Fetching existing games to duplicate...")
existing_games = list(Game.objects.all()[:15000])

new_games = []
suffixes = [" Deluxe", " HD", " Online", " 2", " Multiplayer", " Pro", " 3D", " Ultra", " Evolution", " Infinity"]

for i, game in enumerate(existing_games):
    # Create a clone
    new_title = game.title + random.choice(suffixes)
    
    # Generate random stats for the clone
    if random.random() < 0.2:
        views = random.randint(50000, 950000)
    else:
        views = random.randint(1000, 49999)
        
    start_date = datetime(2020, 1, 1).timestamp()
    end_date = timezone.now().timestamp()
    random_timestamp = random.uniform(start_date, end_date)
    created_at = datetime.fromtimestamp(random_timestamp, tz=dt.timezone.utc)
    
    new_slug = f"{game.slug}-{random.randint(1000, 999999)}"
    
    new_game = Game(
        title=new_title,
        slug=new_slug,
        category=game.category,
        description=game.description,
        thumbnail_url=game.thumbnail_url,
        iframe_url=game.iframe_url,
        views=views,
        created_at=created_at
    )
    new_games.append(new_game)

print(f"Bulk creating {len(new_games)} new games...")
Game.objects.bulk_create(new_games, batch_size=1000)

print(f"Successfully added 15,000 new games! Total is now {Game.objects.count()}.")
