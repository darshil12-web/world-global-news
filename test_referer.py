import urllib.request
import re

url = "https://html5.gamedistribution.com/a084e6ab82f9420bbe89bbe5c1b150fc/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://localhost:8000/'})
html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
match = re.search(r'this\._getDomainData\s*=\s*function\(\)\{\s*return\s*(\[.*?\]);', html)
print(match.group(1) if match else "None")
