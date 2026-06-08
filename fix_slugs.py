import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game
import time

def fix_empty_slugs():
    empty_games = list(Game.objects.filter(slug=''))
    if not empty_games:
        print("No empty slugs found.")
        return 0
    
    print(f"Found {len(empty_games)} games with empty slugs.")
    
    # We need unique slugs
    existing_slugs = set(Game.objects.exclude(slug='').values_list('slug', flat=True))
    
    for game in empty_games:
        base_slug = slugify(game.title) or "game"
        slug = base_slug
        num = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{num}"
            num += 1
        game.slug = slug
        existing_slugs.add(slug)
        
    # Bulk update
    batch_size = 1000
    for i in range(0, len(empty_games), batch_size):
        Game.objects.bulk_update(empty_games[i:i+batch_size], ['slug'])
        print(f"Updated {min(i+batch_size, len(empty_games))}/{len(empty_games)} slugs...")
        
    print("Done fixing slugs!")
    return len(empty_games)

if __name__ == '__main__':
    fix_empty_slugs()
