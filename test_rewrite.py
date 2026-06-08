import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import urllib.request
from news.models import Game

def check_raw(md5):
    url = f"https://html5.gamedistribution.com/rvvASMiM/{md5}/index.html"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=5)
        return res.getcode() == 200
    except:
        return False

games = Game.objects.filter(iframe_url__startswith='https://html5.gamedistribution.com/')[:20]
for g in games:
    url = g.iframe_url
    if 'rvvASMiM' not in url:
        md5 = url.split('/')[-2]
        if len(md5) == 32:
            print(f"{g.title}: {check_raw(md5)}")
