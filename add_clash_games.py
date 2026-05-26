import os
import django
import urllib.request
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

def add_games():
    url = 'https://clash-royale.io/'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(html, 'html.parser')
        
        cards = []
        for a in soup.find_all('a', href=True):
            img = a.find('img')
            if img and a['href'] != '/' and not a['href'].startswith('/category') and not a['href'].startswith('http'):
                slug = a['href'].strip('/')
                title = img.get('alt', slug.replace('-', ' ').title())
                thumb = img.get('src', '')
                cards.append({
                    'title': title,
                    'slug': slug,
                    'thumbnail': thumb
                })
        
        print(f"Parsed {len(cards)} games from homepage.")
        added = 0
        updated = 0
        
        for c in cards:
            slug = c['slug']
            title = c['title']
            thumb = c['thumbnail']
            
            # Format absolute thumbnail URL
            if thumb.startswith('/'):
                thumbnail_url = f"https://clash-royale.io{thumb}"
            else:
                thumbnail_url = thumb
                
            iframe_url = f"https://clash-royale.io/play/{slug}/"
            
            # Check if game exists by iframe_url
            game = Game.objects.filter(iframe_url=iframe_url).first()
            if not game:
                # Also check if it exists by title
                game = Game.objects.filter(title=title).first()
                
            if not game:
                Game.objects.create(
                    title=title,
                    description=f"Play {title} for free online on TechWorld!",
                    thumbnail_url=thumbnail_url,
                    iframe_url=iframe_url
                )
                added += 1
                print(f"Created: {title}")
            else:
                # Update existing game's iframe and thumbnail to use the working clash-royale.io links!
                game.thumbnail_url = thumbnail_url
                game.iframe_url = iframe_url
                game.save()
                updated += 1
                print(f"Updated to Clash-Royale format: {title}")
                
        print(f"Successfully added {added} new games and updated {updated} existing games!")
        
    except Exception as e:
        print("Error scraping/saving games:", e)

if __name__ == '__main__':
    add_games()
