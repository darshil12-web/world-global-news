import json
import os
import time
import threading
import urllib.request
import urllib.error
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from .models import Game, Player


def scrape_clash_games():
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
                'description': f"Play {title} for free online on Poki Clone!",
                'category': 'Action' # Default category
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
                    iframe_url=g['iframe_url'],
                    category=g['category']
                )
            else:
                game.thumbnail_url = g['thumbnail_url']
                game.iframe_url = g['iframe_url']
                game.save()
                
    except Exception as e:
        print("Error in background clash-royale.io sitemap scrape:", e)

def trigger_background_scrape():
    lock_path = os.path.join(settings.BASE_DIR, 'data', 'clash_scrape_lock.txt')
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    if not os.path.exists(lock_path) or (time.time() - os.path.getmtime(lock_path) > 86400):
        with open(lock_path, 'w') as f:
            f.write(str(time.time()))
        thread = threading.Thread(target=scrape_clash_games)
        thread.start()

def get_paginated_games(request, queryset, items_per_page=48):
    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return page_obj

def get_categories():
    return ["Obby", "Tycoon", "Simulator", "Roleplay", "Shooter", "Fighting", "3D Games", "Action", "Adventure", "Arcade", "Multiplayer", "Puzzle", "Racing", "Skill", "Sports"]

def decorate_games(games_list):
    for game in games_list:
        # Deterministic rating percentage (between 87% and 99%)
        game.rating_pct = 87 + (game.id % 13)
        # Deterministic active player count based on views and id
        players = int(game.views * 0.15) + (game.id % 90) + 12
        if players >= 1000000:
            game.active_players = f"{players/1000000:.1f}M"
        elif players >= 1000:
            game.active_players = f"{players/1000:.1f}K"
        else:
            game.active_players = str(players)
        
        # Determine clean creator name based on category
        studios = {
            'Action': 'Action Forge',
            'Adventure': 'Quest Masters',
            'Arcade': 'Retro Neon',
            'Multiplayer': 'Nexus Arena',
            'Puzzle': 'Logic Labs',
            'Racing': 'Apex Velocity',
            'Skill': 'Dexterity Devs',
            'Sports': 'Stadium Elite',
            'Obby': 'Roblox Obstacles',
            'Tycoon': 'Roblox Builders',
            'Simulator': 'Roblox Simulators',
            'Roleplay': 'Roblox RP Group',
            'Shooter': 'Roblox Tactical',
            'Fighting': 'Roblox Combat'
        }
        game.creator = studios.get(game.category, 'Roblox Studio')
    return games_list

def index(request):
    trigger_background_scrape()
    
    query = request.GET.get('q', '').strip()
    order = request.GET.get('order', '-views')
    valid_orders = ['-created_at', 'created_at', '-views', 'views', 'title', '-title']
    if order not in valid_orders:
        order = '-views'
        
    if query:
        games_list = Game.objects.filter(title__icontains=query).order_by(order)
    else:
        # Default Poki-style home page is an infinite grid of popular games
        games_list = Game.objects.all().order_by(order)
        
    total_count = games_list.count()
    page_obj = get_paginated_games(request, games_list, 60)
    decorate_games(page_obj.object_list)
    
    is_home_request = not bool(query)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        from django.template.loader import render_to_string
        html = render_to_string('news/game_cards_partial.html', {'games': page_obj, 'is_ajax': True})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None
        })
        
    context = {
        'games': page_obj,
        'has_next': page_obj.has_next(),
        'total_count': total_count,
        'categories': get_categories(),
        'current_order': order,
        'is_home': not bool(query),
        'query': query,
    }
    return render(request, 'news/index.html', context)

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'suggestions': []})
    
    games = Game.objects.filter(title__icontains=query).order_by('-views')[:6]
    suggestions = []
    from django.urls import reverse
    for g in games:
        suggestions.append({
            'title': g.title,
            'url': reverse('play_game', args=[g.slug]),
            'thumbnail': g.thumbnail_url
        })
    return JsonResponse({'suggestions': suggestions})

def category_games(request, category):
    trigger_background_scrape()
    
    order = request.GET.get('order', '-views')
    valid_orders = ['-created_at', 'created_at', '-views', 'views', 'title', '-title']
    if order not in valid_orders:
        order = '-views'
        
    if category.lower() == '3d games':
        from django.db.models import Q
        games_list = Game.objects.filter(
            Q(category__icontains='3D Games') | 
            Q(category__icontains='Obby') | 
            Q(category__icontains='Tycoon') | 
            Q(category__icontains='Simulator') | 
            Q(category__icontains='Roleplay') | 
            Q(category__icontains='Shooter') | 
            Q(category__icontains='Fighting')
        ).order_by(order)
    else:
        games_list = Game.objects.filter(category__icontains=category).order_by(order)
    total_count = games_list.count()
    
    if total_count == 0:
        return render(request, '404.html', status=404)
        
    page_obj = get_paginated_games(request, games_list, 60)
    decorate_games(page_obj.object_list)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
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
        'categories': get_categories(),
        'current_category': category,
        'current_order': order,
        'is_home': False,
    }
    return render(request, 'news/index.html', context)

def play_game(request, slug):
    try:
        game = Game.objects.get(slug=slug)
    except Game.DoesNotExist:
        return render(request, '404.html', status=404)
    
    game.views += 1
    game.save(update_fields=['views'])
    
    decorate_games([game])
    
    related_games = Game.objects.exclude(id=game.id).order_by('?')[:36]
    decorate_games(list(related_games))
    
    context = {
        'game': game,
        'related_games': related_games,
        'categories': get_categories(),
    }
    
    response = render(request, 'news/play.html', context)
    
    # Update continue playing cookie
    continue_slugs = request.COOKIES.get('continue_playing', '')
    slug_list = [s.strip() for s in continue_slugs.split(',') if s.strip()]
    if game.slug in slug_list:
        slug_list.remove(game.slug)
    slug_list.insert(0, game.slug)
    slug_list = slug_list[:12]
    
    response.set_cookie('continue_playing', ','.join(slug_list), max_age=30*24*60*60, path='/')
    return response

# Custom Roblox Clone Sub-pages
def profile(request):
    categories = get_categories()
    return render(request, 'news/profile.html', {'categories': categories})

def avatar(request):
    categories = get_categories()
    return render(request, 'news/avatar.html', {'categories': categories})

def catalog(request):
    categories = get_categories()
    catalog_items = [
        # Hats
        {'id': 'bacon_hair', 'name': 'Bacon Hair', 'type': 'hat', 'price': 0, 'img': 'bacon_hair'},
        {'id': 'red_cap', 'name': 'Roblox Red Cap', 'type': 'hat', 'price': 15, 'img': 'red_cap'},
        {'id': 'wizard_hat', 'name': 'Wizard Hat', 'type': 'hat', 'price': 75, 'img': 'wizard_hat'},
        {'id': 'crown', 'name': 'Royal Crown', 'type': 'hat', 'price': 250, 'img': 'crown'},
        {'id': 'valkyrie', 'name': 'Valkyrie Helm', 'type': 'hat', 'price': 500, 'img': 'valkyrie'},
        # Shirts
        {'id': 'roblox_hoodie', 'name': 'Blue Hoodie', 'type': 'shirt', 'price': 0, 'img': 'roblox_hoodie'},
        {'id': 'tuxedo', 'name': 'Elegant Tuxedo', 'type': 'shirt', 'price': 50, 'img': 'tuxedo'},
        {'id': 'gold_tee', 'name': 'Gold Chain Tee', 'type': 'shirt', 'price': 100, 'img': 'gold_tee'},
        {'id': 'ninja_suit', 'name': 'Ninja Gi', 'type': 'shirt', 'price': 150, 'img': 'ninja_suit'},
        # Faces
        {'id': 'smile_face', 'name': 'Default Smile', 'type': 'face', 'price': 0, 'img': 'smile_face'},
        {'id': 'chill_face', 'name': 'Chill Face', 'type': 'face', 'price': 30, 'img': 'chill_face'},
        {'id': 'winner_face', 'name': 'Winner Smile', 'type': 'face', 'price': 120, 'img': 'winner_face'},
        {'id': 'beast_face', 'name': 'Beast Mode', 'type': 'face', 'price': 400, 'img': 'beast_face'},
    ]
    return render(request, 'news/catalog.html', {'categories': categories, 'items': catalog_items})


def robux_page(request):
    categories = get_categories()
    return render(request, 'news/robux.html', {'categories': categories})


# Legal / Static pages
def about(request):
    categories = get_categories()
    return render(request, 'news/about.html', {'categories': categories})

def contact(request):
    categories = get_categories()
    return render(request, 'news/contact.html', {'categories': categories})

def disclaimer(request):
    categories = get_categories()
    return render(request, 'news/disclaimer.html', {'categories': categories})

def privacy(request):
    categories = get_categories()
    return render(request, 'news/privacy.html', {'categories': categories})

def terms(request):
    categories = get_categories()
    return render(request, 'news/terms.html', {'categories': categories})

def cookie(request):
    categories = get_categories()
    return render(request, 'news/cookie.html', {'categories': categories})

def dmca(request):
    categories = get_categories()
    return render(request, 'news/dmca.html', {'categories': categories})

def editorial_policy(request):
    categories = get_categories()
    return render(request, 'news/editorial_policy.html', {'categories': categories})

@csrf_exempt
def set_username(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            requested_name = data.get('username', '').strip()
            if not requested_name:
                return JsonResponse({'error': 'Username cannot be empty'}, status=400)
            
            base_name = requested_name
            final_name = base_name
            num = 1
            while Player.objects.filter(username__iexact=final_name).exists():
                final_name = f"{base_name}{num}"
                num += 1
            
            Player.objects.create(username=final_name)
            request.session['username'] = final_name
            
            return JsonResponse({'success': True, 'username': final_name, 'message': 'Username claimed successfully!'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)
