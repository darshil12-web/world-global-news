import json
import os
from django.conf import settings
from django.shortcuts import render, Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from .models import Game
from django.core.paginator import Paginator

def get_news_data():
    json_path = os.path.join(settings.BASE_DIR, 'data', 'news.json')
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

import urllib.request
import urllib.error
import time
import threading
from django.utils.text import slugify
from newspaper import Article

from bs4 import BeautifulSoup

def scrape_techcult():
    json_path = os.path.join(settings.BASE_DIR, 'data', 'news.json')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    
    cat_mapping = {
        'android': 'Android', 
        'apple': 'iOS', 
        'windows': 'Windows', 
        'how-to': 'How-To', 
        'software': 'Apps', 
        'gaming': 'Gaming'
    }
    
    article_links = []
    
    base_url = "https://techcult.com/"
    
    all_cats = set()
    try:
        req = urllib.request.Request(base_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'lxml')
            for a in soup.find_all('a', href=True):
                if 'https://techcult.com/category/' in a['href']:
                    cat_name = a['href'].split('/category/')[1].strip('/')
                    if cat_name:
                        all_cats.add(cat_name)
    except Exception as e:
        all_cats = set(cat_mapping.keys())
        
    for tc_cat in all_cats:
        my_cat = cat_mapping.get(tc_cat, tc_cat.replace('-', ' ').title())
        try:
            req = urllib.request.Request(f"https://techcult.com/category/{tc_cat}/", headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                soup = BeautifulSoup(html, 'lxml')
                count = 0
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('https://techcult.com/') and len(href.split('/')) > 4 and 'category' not in href and 'tag' not in href and 'page' not in href and 'author' not in href and 'about' not in href and 'contact' not in href and 'policy' not in href and 'privacy' not in href and 'terms' not in href and 'disclaimer' not in href:
                        if href not in [link_info['url'] for link_info in article_links]:
                            article_links.append({'url': href, 'category': my_cat})
                            count += 1
                            if count >= 20:
                                break
        except Exception as e:
            print(f"Failed to fetch {tc_cat} page:", e)

    news_items = []
    
    for item in article_links:
        link = item['url']
        my_cat = item['category']
        try:
            req_art = urllib.request.Request(link, headers=headers)
            with urllib.request.urlopen(req_art) as response:
                art_html = response.read().decode('utf-8')
                art_soup = BeautifulSoup(art_html, 'lxml')
                
                title_tag = art_soup.find('h1')
                if not title_tag:
                    continue
                title = title_tag.text.strip()
                
                img_tag = art_soup.find('meta', property='og:image')
                image_url = img_tag['content'] if img_tag else ''
                
                desc_tag = art_soup.find('meta', property='og:description')
                summary = desc_tag['content'] if desc_tag else title
                
                content_div = art_soup.find('div', class_='entry-content')
                if content_div:
                    for script in content_div(["script", "style", "form"]):
                        script.decompose()
                    content_html = str(content_div)
                else:
                    content_html = "<p>Content could not be extracted.</p>"
                
                news_item = {
                    'slug': slugify(title) or 'article',
                    'title': title,
                    'subtitle': summary,
                    'category': my_cat,
                    'author': "Techcult",
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'image': image_url,
                    'summary': summary[:150] + "..." if len(summary) > 150 else summary,
                    'content': content_html,
                    'body': content_html,
                    'url': link
                }
                news_items.append(news_item)
        except Exception as e:
            print("Failed to scrape article", link, e)
            
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, indent=4)

def scrape_clash_games():
    import re
    from bs4 import BeautifulSoup
    from concurrent.futures import ThreadPoolExecutor
    from news.models import Game
    
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
            print(f"Error fetching {url} in background:", e)
            return None

    sitemap_url = 'https://clash-royale.io/sitemap.xml'
    req = urllib.request.Request(sitemap_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml = response.read().decode('utf-8')
        urls = re.findall(r'<loc>(https?://clash-royale.io/[^<]+)</loc>', xml)
        game_urls = [u for u in urls if u != 'https://clash-royale.io/' and '/category/' not in u]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(fetch_game_details, game_urls))
            
        games_data = [r for r in results if r]
        
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
            else:
                game.thumbnail_url = g['thumbnail_url']
                game.iframe_url = g['iframe_url']
                game.save()
                
    except Exception as e:
        print("Error in background clash-royale.io sitemap scrape:", e)

def index(request):
    json_path = os.path.join(settings.BASE_DIR, 'data', 'news.json')
    
    # Auto-fetch techcult data in background if cache is older than 2 hours (7200 seconds) or missing
    if not os.path.exists(json_path) or (time.time() - os.path.getmtime(json_path) > 7200):
        if os.path.exists(json_path):
            os.utime(json_path, None)
        thread = threading.Thread(target=scrape_techcult)
        thread.start()
        
    news_items = get_news_data()
    
    # Filter only the approved categories for display on the frontend
    allowed_categories = ['Android', 'iOS', 'Windows', 'How-To', 'Apps', 'Gaming']
    news_items = [item for item in news_items if item.get('category') in allowed_categories]
    
    news_items = sorted(news_items, key=lambda x: x.get('date', ''), reverse=True)
    
    featured_games = Game.objects.all().order_by('-id')[:48]
    
    context = {
        'news_items': news_items,
        'clash_games': featured_games,  # Reused variable name or we can rename in index.html too
    }
    return render(request, 'news/index.html', context)

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

def games(request):
    # Auto-scrape new clash-royale.io games in the background once every 24 hours (86400 seconds)
    lock_path = os.path.join(settings.BASE_DIR, 'data', 'clash_scrape_lock.txt')
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    if not os.path.exists(lock_path) or (time.time() - os.path.getmtime(lock_path) > 86400):
        # Update modified time immediately to prevent multiple threads
        with open(lock_path, 'w') as f:
            f.write(str(time.time()))
        thread = threading.Thread(target=scrape_clash_games)
        thread.start()

    games_list = Game.objects.all().order_by('-id')
    total_count = games_list.count()
    paginator = Paginator(games_list, 48)  # 48 games per page
    
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        from django.http import JsonResponse
        from django.template.loader import render_to_string
        html = render_to_string('news/game_cards_partial.html', {'games': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })
        
    context = {
        'games': page_obj,
        'has_next': page_obj.has_next(),
        'total_count': total_count,
    }
    return render(request, 'news/games.html', context)

def play_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    related_games = Game.objects.exclude(id=game_id).order_by('?')[:36]
    return render(request, 'news/play.html', {'game': game, 'related_games': related_games})

def news_detail(request, slug):
    news_items = get_news_data()
    article = next((item for item in news_items if item.get('slug') == slug), None)
    
    if article is None:
        raise Http404("Article not found")
        
    related_articles = [item for item in news_items if item.get('category') == article.get('category') and item.get('slug') != slug][:3]
        
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    return render(request, 'news/detail.html', context)

def category_news(request, category):
    news_items = get_news_data()
    # Filter by category (case-insensitive)
    category_items = [item for item in news_items if item.get('category', '').lower() == category.lower()]
    
    category_items = sorted(category_items, key=lambda x: x.get('date', ''), reverse=True)
    
    context = {
        'news_items': category_items,
        'current_category': category.title(),
    }
    return render(request, 'news/index.html', context)

def about(request):
    return render(request, 'news/about.html')

def contact(request):
    return render(request, 'news/contact.html')

def disclaimer(request):
    return render(request, 'news/disclaimer.html')

def privacy(request):
    return render(request, 'news/privacy.html')

def terms(request):
    return render(request, 'news/terms.html')

def cookie(request):
    return render(request, 'news/cookie.html')

def dmca(request):
    return render(request, 'news/dmca.html')

def editorial_policy(request):
    return render(request, 'news/editorial_policy.html')

def get_comments_data():
    json_path = os.path.join(settings.BASE_DIR, 'data', 'comments.json')
    if not os.path.exists(json_path):
        return {}
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_comments_data(data):
    json_path = os.path.join(settings.BASE_DIR, 'data', 'comments.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def api_get_comments(request, slug):
    data = get_comments_data()
    article_comments = data.get(slug, [])
    return JsonResponse({'comments': article_comments})

@csrf_exempt
def api_post_comment(request, slug):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            name = body.get('name', 'Anonymous')
            text = body.get('text', '')
            if not text:
                return JsonResponse({'error': 'No text'}, status=400)
            
            data = get_comments_data()
            if slug not in data:
                data[slug] = []
                
            exact_time = datetime.now().strftime("%I:%M %p, %b %d")
                
            new_comment = {
                'id': str(len(data[slug]) + 1),
                'name': name,
                'text': text,
                'time': exact_time,
                'likes': 0,
                'dislikes': 0
            }
            # Prepend so newest is first
            data[slug].insert(0, new_comment)
            save_comments_data(data)
            return JsonResponse({'comment': new_comment})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)
