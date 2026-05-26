import os
import django
import asyncio
from playwright.async_api import async_playwright

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from news.models import Game

async def scrape_games():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to homepage...")
        await page.goto("https://clash-royale.io/", wait_until="domcontentloaded")
        
        # Extract game links
        game_links = await page.eval_on_selector_all("a[href^='/']", """
            (elements) => elements.map(el => {
                return {
                    url: el.href,
                    title: el.innerText.trim(),
                    slug: el.getAttribute('href')
                };
            }).filter(g => g.slug && g.slug !== '/' && !g.slug.startsWith('/category') && !g.slug.startsWith('#'))
        """)
        
        # Remove duplicates
        unique_games = {g['slug']: g for g in game_links}.values()
        
        print(f"Found {len(unique_games)} potential games. Starting extraction...")
        
        added_count = 0
        
        for g in unique_games:
            slug = g['slug']
            title = g['title'] or slug.replace('/', '').replace('-', ' ').title()
            
            print(f"Processing {title} ({slug})...")
            
            try:
                await page.goto(g['url'], wait_until="networkidle")
                
                # The iframe src is dynamically injected, so we need to wait for it or extract it.
                # Sometimes the iframe is inside a #gameFrame element
                iframe_src = None
                thumbnail_url = None
                
                # Check thumbnail
                img_element = await page.query_selector(".splash-background")
                if img_element:
                    thumbnail_url = await img_element.get_attribute("src")
                else:
                    img_element = await page.query_selector(".game-icon")
                    if img_element:
                        thumbnail_url = await img_element.get_attribute("src")
                        
                # Click play button if it exists
                try:
                    play_btn = await page.query_selector("button.play-now-btn, .splash-overlay button, #play-btn")
                    if play_btn:
                        await play_btn.click()
                        await page.wait_for_timeout(3000) # Wait 3 seconds for iframe
                except:
                    pass
                
                # Check iframe
                iframe_element = await page.query_selector("iframe")
                if iframe_element:
                    iframe_src = await iframe_element.get_attribute("src")
                
                if not iframe_src:
                    gameFrame = await page.query_selector("#gameFrame")
                    if gameFrame:
                        iframe_src = await gameFrame.get_attribute("src")
                
                # Format URLs
                if thumbnail_url and thumbnail_url.startswith('/'):
                    thumbnail_url = "https://clash-royale.io" + thumbnail_url
                    
                if iframe_src and iframe_src.startswith('/'):
                    iframe_src = "https://clash-royale.io" + iframe_src
                    
                if iframe_src:
                    # Check if already exists
                    if not Game.objects.filter(iframe_url=iframe_src).exists():
                        Game.objects.create(
                            title=title,
                            description=f"Play {title} for free online!",
                            thumbnail_url=thumbnail_url or "https://clash-royale.io/assets/upload/default.png",
                            iframe_url=iframe_src
                        )
                        added_count += 1
                        print(f"  -> Added {title}!")
                    else:
                        print(f"  -> Already exists in DB.")
                else:
                    print(f"  -> No iframe found for {title}.")
                    
            except Exception as e:
                print(f"  -> Error processing {title}: {e}")
                
        print(f"Done! Added {added_count} new games to the database.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_games())
