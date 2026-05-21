import json
import os
from django.conf import settings
from django.shortcuts import render, Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime

def get_news_data():
    json_path = os.path.join(settings.BASE_DIR, 'data', 'news.json')
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def index(request):
    news_items = get_news_data()
    
    # Optional: Sort by date descending (assuming iso format dates)
    news_items = sorted(news_items, key=lambda x: x.get('date', ''), reverse=True)
    
    context = {
        'news_items': news_items,
    }
    return render(request, 'news/index.html', context)

def news_detail(request, slug):
    news_items = get_news_data()
    article = next((item for item in news_items if item.get('slug') == slug), None)
    
    if article is None:
        raise Http404("Article not found")
        
    context = {
        'article': article,
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
