import os
import django
import urllib.request
import json
import ssl
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

def fetch_clash_games():
    print("--------------------------------------------------")
    print("Scraping and Syncing games from clash-royale.io...")
    print("--------------------------------------------------")
    
    def clean_title(title):
        if not title:
            return "Unknown Game"
        suffixes = [
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
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            
            title_meta = soup.find('meta', attrs={'name': 'twitter:title'}) or soup.find('meta', property='og:title')
            title = title_meta.get('content') if title_meta else (soup.title.string if soup.title else '')
            title = clean_title(title)
            
            image_meta = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', property='og:image')
            image = image_meta.get('content') if image_meta else ''
            if image and image.startswith('/'):
                image = f"https://clash-royale.io{image}"
                
            slug = url.rstrip('/').split('/')[-1]
            if slug == 'search' or not slug:
                return None
                
            iframe_url = f"https://clash-royale.io/play/{slug}/"
            
            return {
                'title': title,
                'thumbnail_url': image or f"https://clash-royale.io/assets/upload/{slug}.png",
                'iframe_url': iframe_url,
                'description': f"Play {title} for free online on TechWorld!"
            }
        except Exception as e:
            return None

    sitemap_url = 'https://clash-royale.io/sitemap.xml'
    req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode('utf-8')
        urls = re.findall(r'<loc>(https?://clash-royale.io/[^<]+)</loc>', xml)
        game_urls = [u for u in urls if u != 'https://clash-royale.io/' and '/category/' not in u]
        print(f"Found {len(game_urls)} game URLs on clash-royale.io.")
        
        print("Scraping game details concurrently...")
        with ThreadPoolExecutor(max_workers=15) as executor:
            results = list(executor.map(fetch_game_details, game_urls))
            
        games_data = [r for r in results if r]
        print(f"Scraped {len(games_data)} games successfully.")
        
        added = 0
        updated = 0
        
        for g in games_data:
            if 'search' in g['iframe_url']:
                continue
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
                
        print(f"Clash-Royale Sync Done: Added {added} new, updated {updated} existing.")
        
    except Exception as e:
        print("Error scraping clash-royale.io:", e)

def fetch_ant_games():
    print("--------------------------------------------------")
    print("Scraping and Syncing games from ant.games...")
    print("--------------------------------------------------")
    
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
            
            title_meta = soup.find('meta', attrs={'name': 'twitter:title'}) or soup.find('meta', property='og:title')
            title = title_meta.get('content') if title_meta else (soup.title.string if soup.title else '')
            title = clean_title(title)
            
            image_meta = soup.find('meta', attrs={'name': 'twitter:image'}) or soup.find('meta', property='og:image')
            image = image_meta.get('content') if image_meta else ''
            if image:
                if image.startswith('/'):
                    image = f"https://ant.games{image}"
                image = image.replace('/150x150/', '/220x220/').replace('/120x120/', '/220x220/').replace('/100x100/', '/220x220/')
                
            slug = url.rstrip('/').split('/')[-1]
            
            # Extract direct frame_link from scripts
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

    sitemap_url = 'https://ant.games/sitemaps/games.xml'
    req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode('utf-8')
        urls = re.findall(r'<loc>(https?://ant.games/[^<]+)</loc>', xml)
        game_urls = [u for u in urls if u != 'https://ant.games/' and '/category/' not in u]
        print(f"Found {len(game_urls)} game URLs on ant.games.")
        
        print("Scraping AntGames details concurrently...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(fetch_game_details, game_urls))
            
        games_data = [r for r in results if r]
        print(f"Scraped {len(games_data)} AntGames successfully.")
        
        added = 0
        updated = 0
        
        for g in games_data:
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
                
        print(f"AntGames Sync Done: Added {added} new, updated {updated} existing.")
        
    except Exception as e:
        print("Error scraping ant.games:", e)

def fetch_more_games():
    print("--------------------------------------------------")
    print("Fetching and saving GameDistribution games...")
    print("--------------------------------------------------")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    existing_urls = set(Game.objects.values_list('iframe_url', flat=True))
    print(f"Existing games in DB: {len(existing_urls)}")

    total_added = 0

    for page in range(51, 151):
        url = f'https://catalog.api.gamedistribution.com/api/v2.0/rss/All/?collection=all&amount=100&page={page}&format=json'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, context=ctx, timeout=15)
            data = json.loads(response.read().decode('utf-8'))

            if not data:
                print(f"  No data on page {page}, stopping.")
                break

            batch = []
            for item in data:
                iframe_url = item.get('Url', '')
                if iframe_url and iframe_url not in existing_urls:
                    batch.append(Game(
                        title=item.get('Title', 'Unknown Game'),
                        description=item.get('Description', ''),
                        thumbnail_url=item.get('Asset', [''])[0],
                        iframe_url=iframe_url,
                    ))
                    existing_urls.add(iframe_url)

            if batch:
                Game.objects.bulk_create(batch)
                total_added += len(batch)

            print(f"  Page {page}/150 — saved {len(batch)} games | Total added: {total_added}")

        except Exception as e:
            print(f"  Error on page {page}: {e}")
            continue

    print(f"\nGameDistribution Sync Done! Added {total_added} new games.")
    print(f"Total games in DB: {Game.objects.count()}")

if __name__ == '__main__':
    fetch_clash_games()
    fetch_ant_games()
    fetch_more_games()
