import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import urllib.request
import re
from news.models import Game

def check_game(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
        match = re.search(r'this\._getDomainData\s*=\s*function\(\)\{\s*return\s*(\[.*?\]);', html)
        if match:
            domains = match.group(1)
            if domains != '[]':
                return True, domains
        return False, None
    except Exception as e:
        return False, str(e)

games = Game.objects.filter(iframe_url__icontains='html5.gamedistribution.com')[:10]
for g in games:
    is_locked, info = check_game(g.iframe_url)
    print(f"{g.title}: Locked? {is_locked} ({info})")

