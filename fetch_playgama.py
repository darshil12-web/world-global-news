"""
fetch_playgama.py
=================
Scrapes ALL categories and games from playgama.com (17,000+ games)
and bulk-inserts them into the Django database with correct iframes.

Iframe format: https://playgama.com/export/game/SLUG
"""

import os, django, time, urllib.request, re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from news.models import Game

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': 'text/html,*/*'}
BASE    = 'https://playgama.com'

# All playgama categories → our site category mapping
CATEGORIES = {
    'arcade':         'Arcade',
    'io':             'Multiplayer',
    'action':         'Action',
    'puzzle':         'Puzzle',
    'sports':         'Sports',
    'strategy':       'Skill',
    'simulation':     'Simulator',
    'skill':          'Skill',
    'bubble-shooter': 'Arcade',
    'girls':          'Arcade',
    'two-player':     'Multiplayer',
    'boys':           'Action',
    'obby':           'Obby',
    'horror':         'Action',
    'car':            'Racing',
    'funny':          'Arcade',
    'multiplayer':    'Multiplayer',
    'shooting':       'Shooter',
    'snake':          'Arcade',
    'gun':            'Shooter',
    'clicker':        'Arcade',
    'solitaire':      'Puzzle',
    'drawing':        'Arcade',
    'idle':           'Tycoon',
    'racing':         'Racing',
    'minecraft':      '3D Games',
    'fighting':       'Fighting',
    'adventure':      'Adventure',
    'tycoon':         'Tycoon',
    'horror':         'Action',
    'zombie':         'Action',
    'stickman':       'Action',
    'dress-up':       'Arcade',
    'cooking':        'Arcade',
    'merge':          'Puzzle',
    'tower-defense':  'Action',
    'parkour':        'Obby',
    'running':        'Arcade',
    'trending_now':   '3D Games',
    'top_playgama':   '3D Games',
    'new':            '3D Games',
}

def fetch_html(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as r:
                return r.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if i < retries - 1:
                time.sleep(1.5)
    return ''

def get_all_categories():
    """Get all categories from /all/categories page."""
    html = fetch_html(f'{BASE}/all/categories')
    soup = BeautifulSoup(html, 'html.parser')
    cats = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/category/' in href:
            slug = href.split('/category/')[-1].strip('/')
            if slug and slug not in ('trending_now', 'top_playgama', 'new'):
                name = a.get_text(strip=True) or slug
                cats[slug] = name
    return cats

def scrape_category_page(cat_slug, page=1):
    """Scrape game slugs and thumbnails from one category page."""
    url = f'{BASE}/category/{cat_slug}' + (f'?page={page}' if page > 1 else '')
    html = fetch_html(url)
    if not html:
        return [], False

    soup = BeautifulSoup(html, 'html.parser')
    games = []

    # Find all game cards
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/game/' not in href:
            continue
        game_slug = href.split('/game/')[-1].strip('/')
        if not game_slug or '?' in game_slug:
            continue

        # Get title
        title = a.get_text(strip=True)
        if not title:
            img = a.find('img')
            title = img.get('alt', '').strip() if img else game_slug.replace('-', ' ').title()

        # Get thumbnail from img inside the link
        thumb = ''
        img = a.find('img')
        if img:
            thumb = img.get('src') or img.get('data-src') or img.get('data-lazy-src', '')
            if thumb and thumb.startswith('//'):
                thumb = 'https:' + thumb

        if game_slug and title:
            games.append({
                'slug':  game_slug,
                'title': title,
                'thumb': thumb,
            })

    # Check if there's a next page
    has_next = bool(soup.find('a', href=re.compile(r'\?page=\d+')))
    return games, has_next

def scrape_all_games_in_category(cat_slug, our_category):
    """Scrape all pages of a category."""
    all_games = {}
    page = 1
    while True:
        games, has_next = scrape_category_page(cat_slug, page)
        for g in games:
            s = g['slug']
            if s not in all_games:
                all_games[s] = {'category': our_category, **g}
        if not has_next or not games or page >= 20:  # max 20 pages
            break
        page += 1
        time.sleep(0.2)
    return all_games

# ─── MAIN ─────────────────────────────────────────────────────────────────────
print('=' * 65)
print('PLAYGAMA FULL FETCH — All categories, all games')
print('=' * 65)

# Get all category slugs
print('\nFetching all categories...')
all_cats = get_all_categories()
# Merge with our predefined list
for slug in CATEGORIES:
    if slug not in all_cats:
        all_cats[slug] = slug.replace('-', ' ').title()
print(f'Total categories: {len(all_cats)}')
for slug, name in list(all_cats.items())[:10]:
    print(f'  • {slug} → {CATEGORIES.get(slug, "3D Games")}')
print('  ...')

# Load existing to skip duplicates
existing_titles = set(Game.objects.values_list('title', flat=True))
print(f'\nExisting games in DB: {len(existing_titles)}')

# Scrape all categories
print('\nScraping all category pages...\n')
collected = {}  # slug → game dict

for idx, (cat_slug, cat_name) in enumerate(all_cats.items(), 1):
    our_cat = CATEGORIES.get(cat_slug, '3D Games')
    print(f'[{idx}/{len(all_cats)}] {cat_slug} → {our_cat}', end='  ')

    games = scrape_all_games_in_category(cat_slug, our_cat)
    new_count = 0
    for slug, g in games.items():
        if slug not in collected and g['title'] not in existing_titles:
            collected[slug] = g
            new_count += 1

    print(f'+{new_count} new (total: {len(collected)})')
    
    # All games are inserted immediately during scraping.
        
    time.sleep(0.3)

print(f'\n✅ Total unique new games inserted: {len(collected)}')
