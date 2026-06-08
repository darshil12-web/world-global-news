import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

games = list(Game.objects.filter(iframe_url__icontains='widgets.playgama.com/?gameSlug='))
count = 0
for g in games:
    match = re.search(r'gameSlug=([^&]+)', g.iframe_url)
    if match:
        g.iframe_url = f'https://playgama.com/export/game/{match.group(1)}'
        count += 1

if games:
    # Use bulk_update in batches
    batch_size = 1000
    for i in range(0, len(games), batch_size):
        Game.objects.bulk_update(games[i:i+batch_size], ['iframe_url'])

print(f"Updated {count} URLs successfully.")
