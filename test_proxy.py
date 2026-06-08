import urllib.request
import re

url = "https://html5.gamedistribution.com/a084e6ab82f9420bbe89bbe5c1b150fc/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Remove the sitelock array
html_fixed = re.sub(r'this\._getDomainData\s*=\s*function\(\)\{\s*return\s*\[.*?\];\s*\}', r'this._getDomainData = function(){ return []; }', html)

with open('proxy_test.html', 'w') as f:
    f.write(html_fixed)
print("Saved proxy_test.html")
