import json
import os
import urllib.request
from bs4 import BeautifulSoup
from django.utils.text import slugify
from datetime import datetime

import django
import sys

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.conf import settings

def scrape_techcult():
    base_url = "https://techcult.com/"
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
    
    # Dynamically fetch all categories from techcult
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
        print("Scraping:", link)
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
            
    json_path = os.path.join(settings.BASE_DIR, 'data', 'news.json')
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, indent=4)
    print(f"Successfully scraped and saved {len(news_items)} articles from Techcult.")

if __name__ == '__main__':
    scrape_techcult()
