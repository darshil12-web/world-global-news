import os
import django
import asyncio
import aiohttp
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game
from asgiref.sync import sync_to_async

LOCK_REGEX = re.compile(r'this\._getDomainData\s*=\s*function\(\)\{\s*return\s*(\[.*?\]);')

async def check_game(session, game_id, url):
    try:
        async with session.get(url, timeout=5) as response:
            html = await response.text()
            match = LOCK_REGEX.search(html)
            if match:
                domains = match.group(1)
                if domains != '[]':
                    return game_id
    except:
        pass
    return None

async def main():
    games = await sync_to_async(list)(Game.objects.filter(iframe_url__icontains='html5.gamedistribution.com').values_list('id', 'iframe_url'))
    print(f"Total games to check: {len(games)}")
    
    locked_ids = []
    
    connector = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Process in chunks of 2000 to avoid memory issues
        chunk_size = 2000
        for i in range(0, len(games), chunk_size):
            chunk = games[i:i+chunk_size]
            tasks = [check_game(session, g[0], g[1]) for g in chunk]
            results = await asyncio.gather(*tasks)
            
            chunk_locked = [r for r in results if r is not None]
            locked_ids.extend(chunk_locked)
            print(f"Processed {i+len(chunk)}/{len(games)}... Found {len(locked_ids)} locked so far.")
            
    if locked_ids:
        print(f"Deleting {len(locked_ids)} locked games from database...")
        # Delete in batches
        for i in range(0, len(locked_ids), 1000):
            batch = locked_ids[i:i+1000]
            await sync_to_async(Game.objects.filter(id__in=batch).delete)()
    print("Cleanup Complete!")

if __name__ == '__main__':
    asyncio.run(main())

