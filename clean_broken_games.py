import os
import django
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

games = list(Game.objects.all())
broken_games_ids = []

# Headers to act like a real browser to avoid instant Cloudflare bans
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def check_game(game):
    try:
        # Don't follow redirects so we can catch the 302
        response = requests.head(game.iframe_url, headers=headers, allow_redirects=False, timeout=5)
        if response.status_code in [301, 302, 404]:
            return game.id
    except:
        pass
    return None

print(f"Starting scan of {len(games)} games for broken/redirecting URLs...")
count = 0

# Limit workers to 10 to avoid triggering rate limits on clash-royale.io
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check_game, game): game for game in games}
    for future in as_completed(futures):
        count += 1
        result = future.result()
        if result:
            broken_games_ids.append(result)
            
        if count % 500 == 0:
            print(f"Checked {count}/{len(games)}... Found {len(broken_games_ids)} broken games so far.")

if broken_games_ids:
    print(f"\nScan complete! Found {len(broken_games_ids)} broken games. Deleting them from the database...")
    deleted_count, _ = Game.objects.filter(id__in=broken_games_ids).delete()
    print(f"Successfully deleted {deleted_count} games!")
else:
    print("\nScan complete! No broken games found.")
