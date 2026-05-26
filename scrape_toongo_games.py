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
        " - Play on Toongo",
        " Game"
    ]
    for s in suffixes:
        if s in title:
            title = title.replace(s, "")
    return title.strip()

def fetch_toongo_details(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    slug = url.rstrip('/').split('/')[-1]
    
    # 1. Fetch game page to get meta details
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
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
        if not image:
            image = f"https://img.toongo.io/g/{slug}/badge.webp"
            
        # Extract description
        desc_meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', property='og:description')
        description = desc_meta.get('content') if desc_meta else f"Play {title} for free online on TechWorld!"
        
        # 2. Fetch play iframe template page to extract direct cdn.toongo.io URL
        iframe_url = None
        play_url = f"https://toongo.io/e/{slug}/index.html"
        play_req = urllib.request.Request(play_url, headers=headers)
        try:
            with urllib.request.urlopen(play_req, timeout=5) as p_res:
                p_html = p_res.read().decode('utf-8', errors='ignore')
            idx = p_html.find('\"src\":\"')
            if idx != -1:
                start = idx + 7
                end = p_html.find('\"', start)
                clean_url = p_html[start:end].replace('\\/', '/')
                if clean_url and clean_url.startswith('http'):
                    iframe_url = clean_url
        except Exception:
            pass
            
        if not iframe_url:
            # Fallback if iframe page can't be fetched
            iframe_url = f"https://cdn.toongo.io/{slug}/index.html"
            
        # Ensure qcek token is appended to allow framing on any domain
        if 'toongo.io' in iframe_url and '?qcek' not in iframe_url and '&qcek' not in iframe_url:
            if '?' in iframe_url:
                iframe_url += '&qcek'
            else:
                iframe_url += '?qcek'
            
        return {
            'title': title,
            'thumbnail_url': image,
            'iframe_url': iframe_url,
            'description': description
        }
    except Exception as e:
        return None

def main():
    print("--------------------------------------------------")
    print("Fetching game URLs from toongo.io sitemap...")
    print("--------------------------------------------------")
    sitemap_url = 'https://toongo.io/sitemap-games.xml'
    req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode('utf-8')
        game_urls = re.findall(r'<loc>(https?://toongo.io/game/[^<]+)</loc>', xml)
        print(f"Found {len(game_urls)} games in sitemap.")
        
        # Slice to process a highly stable set of top 250 premium games first
        # Processing 250 keeps it incredibly fast, fully working, and responsive.
        target_urls = game_urls[:250]
        print(f"Scraping detailed game assets for top {len(target_urls)} games concurrently...")
        
        with ThreadPoolExecutor(max_workers=35) as executor:
            results = list(executor.map(fetch_toongo_details, target_urls))
            
        games_data = [r for r in results if r]
        print(f"Scraped {len(games_data)} Toongo games successfully.")
        
        added = 0
        updated = 0
        
        for g in games_data:
            # Check if exists by iframe_url or title
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
                
        print(f"Toongo Sync Done: Added {added} new, updated {updated} existing games in database.")
        print("--------------------------------------------------")
        
    except Exception as e:
        print("Error processing toongo.io sitemap:", e)

if __name__ == '__main__':
    main()
