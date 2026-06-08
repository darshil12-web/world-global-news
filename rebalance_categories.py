import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

categories = [
    'Obby', 'Tycoon', 'Simulator', 'Roleplay', 'Shooter', 
    'Fighting', '3D Games', 'Adventure', 'Multiplayer', 
    'Puzzle', 'Skill', 'Sports'
]

games = list(Game.objects.all())
count = 0

for g in games:
    if g.category in ['Action', 'Arcade', 'Racing']:
        if random.random() < 0.7:
            g.category = random.choice(categories)
            count += 1

if games:
    batch_size = 1000
    for i in range(0, len(games), batch_size):
        Game.objects.bulk_update(games[i:i+batch_size], ['category'])

print(f"Re-categorized {count} games across the portal.")
