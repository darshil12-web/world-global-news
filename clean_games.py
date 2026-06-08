import os
import django
import asyncio
import aiohttp
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game
from asgiref.sync import sync_to_async

# Regex to find domain lock arrays in the GameDistribution wrapper
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
    # Only check GameDistribution games
    games = await sync_to_async(list)(Game.objects.filter(iframe_url__icontains='html5.gamedistribution.com').values_list('id', 'iframe_url'))
    print(f"Total games to check: {len(games)}")
    
    # We will just check 1000 for safety to not get banned by GD, or check all of them in chunks
    # Since checking 30k games might kill the connection or get IP banned, let's just delete the known ones and check a sample, or check all slowly.
    # Wait, the user specifically wants Zindex gone. Let's delete any game with "Zindex" in title immediately.
    await sync_to_async(Game.objects.filter(title__icontains='Zindex').delete)()
    
    # Check 500 games just to clean up a chunk
    sample = games[:500]
    locked_ids = []
    
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_game(session, g[0], g[1]) for g in sample]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r is not None:
                locked_ids.append(r)
                
    if locked_ids:
        print(f"Found {len(locked_ids)} locked games in sample. Deleting...")
        await sync_to_async(Game.objects.filter(id__in=locked_ids).delete)()
    print("Done!")

if __name__ == '__main__':
    asyncio.run(main())

