import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import urllib.request
import re
from news.models import Game

def get_game_src(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
    match = re.search(r'var gameSrc = "(.*?)".*?;', html)
    if match:
        return match.group(1)
    return "Not Found"

games = Game.objects.filter(iframe_url__icontains='html5.gamedistribution.com')[:3]
for g in games:
    print(g.title, get_game_src(g.iframe_url))

