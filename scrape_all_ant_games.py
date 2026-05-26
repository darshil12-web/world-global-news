import os
import django
import urllib.request
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

def clean_title(title):
    if not title:
        return "Unknown Game"
    suffixes = [
        " - Play Online for Free on AntGames",
        " - Play Free Online!",
        " game thumbnail",
        " - Play Online Free",
        " Unblocked - ClassRoom6x",
        " Game"
    ]
    for s in suffixes:
        if s in title:
            title = title.replace(s, "")
    if " - " in title:
        title = title.split(" - ")[0]
    return title.strip()

def fetch_game_details(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html_bytes = response.read()
        html = html_bytes.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html_bytes, 'html.parser')
        
        # Extract title
        title_meta = soup.find('meta', attrs={'name': 'twitter:title'}) or soup.find('meta', property='og:title')
        title = title_meta.get('content') if title_meta else (soup.title.string if soup.title else '')
        title = clean_title(title)
        
        # Extract image
        image_meta = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', property='og:image')
        image = image_meta.get('content') if image_meta else ''
        if image:
            if image.startswith('/'):
                image = f"https://ant.games{image}"
            image = image.replace('/150x150/', '/220x220/').replace('/120x120/', '/220x220/').replace('/100x100/', '/220x220/')
            
        slug = url.rstrip('/').split('/')[-1]
        
        # Extract clean direct frame_link from scripts
        iframe_url = None
        idx = html.find('frame_link')
        if idx != -1:
            start = html.find('https', idx)
            end = start
            while end < len(html) and html[end] not in ['\"', chr(92), ' ', '<', '>']:
                end += 1
            clean_url = html[start:end].replace(chr(92) + '/', '/')
            if clean_url and clean_url.startswith('http'):
                iframe_url = clean_url
                
        if not iframe_url:
            iframe_url = f"https://h5.ant.games/gs/{slug}/"
        
        return {
            'title': title,
            'thumbnail_url': image or f"https://imgr2.ant.games/220x220/games/{slug}/s320x320.png",
            'iframe_url': iframe_url,
            'description': f"Play {title} for free online on TechWorld!"
        }
    except Exception as e:
        return None

def main():
    sitemap_url = 'https://ant.games/sitemaps/games.xml'
    req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode('utf-8')
        urls = re.findall(r'<loc>(https?://ant.games/[^<]+)</loc>', xml)
        
        # Filter game URLs
        game_urls = [u for u in urls if u != 'https://ant.games/' and '/category/' not in u]
        print(f"Found {len(game_urls)} game URLs in AntGames sitemap.")
        
        print("Starting concurrent scraping of AntGames details...")
        with ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(fetch_game_details, game_urls))
            
        games_data = [r for r in results if r]
        print(f"Scraped {len(games_data)} AntGames successfully.")
        
        added = 0
        updated = 0
        
        for g in games_data:
            # Check if game exists by iframe_url or title
            game = Game.objects.filter(iframe_url=g['iframe_url']).first()
            if not game:
                game = Game.objects.filter(title=g['title']).first()
                
            if not game:
                Game.objects.create(
                    title=g['title'],
                    description=g['description'],
                    thumbnail_url=g['thumbnail_url'],
                    iframe_url=g['iframe_url']
                )
                added += 1
            else:
                game.thumbnail_url = g['thumbnail_url']
                game.iframe_url = g['iframe_url']
                game.save()
                updated += 1
                
        print(f"Done! Created {added} new games, updated {updated} existing games in database.")
        
    except Exception as e:
        print("Error processing sitemap:", e)

if __name__ == '__main__':
    main()
