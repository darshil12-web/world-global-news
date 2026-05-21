import json
import random
import os
from datetime import datetime, timedelta

# User provided list of reporters
reporters = [
    "Christiane Amanpour", "Clarissa Ward", "Lyse Doucet", "Richard Engel", "Jeremy Bowen", 
    "Anderson Cooper", "Yalda Hakim", "Ros Atkins", "Louis Theroux", "Max Foster",
    "Maria Ressa", "Glenn Greenwald", "Mehdi Hasan", "Fareed Zakaria", "Ezra Klein",
    "Eliot Higgins", "Anne Applebaum", "Ronan Farrow", "Maggie Haberman", "Jonathan Swan",
    "David Muir", "Kaitlan Collins", "Mary Bruce", "Jeff Mason", "Ashley Parker",
    "Arnab Goswami", "Rajat Sharma", "Rajdeep Sardesai", "Sudhir Chaudhary", "Anjana Om Kashyap",
    "Rahul Kanwal", "Rubika Liyaquat", "Navika Kumar", "Chitra Tripathi", "Amish Devgan",
    "Ravish Kumar", "Barkha Dutt", "Palki Sharma", "Saurabh Dwivedi", "Faye D'Souza",
    "Dhanya Rajendran", "Shekhar Gupta", "Siddharth Varadarajan", "Arfa Khanum Sherwani", "Suhasini Haidar",
    "Suhasini Raj", "P Sainath", "Aniruddha Ghosal", "Shereen Bhan", "Harsha Bhogle"
]

images = [
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1521295121783-8a321d551ad2?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1529107386315-e1c731f2ca75?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80"
]

new_articles_data = [
    ("Global AI Regulations Reshape Tech Industry in 2026", "Technology", "New comprehensive frameworks implemented in the EU and US are fundamentally altering how tech giants operate, marking the end of the 'wild west' era of AI development."),
    ("Middle East Trade Routes See Historic Recovery", "World", "Following years of disruption, maritime trade through crucial Middle Eastern corridors has reached unprecedented volumes, stabilizing global supply chains."),
    ("Luxury Wellness Lifestyle Trends Rise Across Europe", "Lifestyle", "The post-pandemic shift toward holistic health has culminated in a booming luxury wellness sector, with specialized retreats multiplying across the continent."),
    ("Electric Vehicle Markets Break New Records Worldwide", "Business", "May 2026 sales figures indicate that EVs now constitute over 40% of all new vehicle purchases globally, driven by radical improvements in battery technology."),
    ("Mars Colony Project Announces First Civilian Selection", "Technology", "The international coalition for space exploration has finally revealed the methodology for selecting the first civilian colonists destined for Mars."),
    ("Major Breakthrough in Desalination Technology", "Technology", "A new graphene-based filtration system promises to make seawater desalination 80% more energy-efficient, offering hope to drought-stricken regions."),
    ("Stock Markets Stabilize After Digital Currency Implementation", "Business", "Central Bank Digital Currencies (CBDCs) are now standard in over 15 major economies, leading to a surprising era of financial stability."),
    ("Historic Peace Accord Signed in Eastern Europe", "World", "Delegates from conflicting nations have signed a definitive peace treaty, bringing an end to the region's longest-running geopolitical standoff."),
    ("The Return of Supersonic Commercial Flights", "Technology", "Aviation regulators have officially approved the new generation of ultra-quiet supersonic passenger jets for trans-Atlantic routes starting this fall."),
    ("Global Summit Addresses Automation and Universal Basic Income", "News", "As AI displaces millions of administrative jobs, global leaders convene in Geneva to discuss standardizing Universal Basic Income models."),
    ("New FDA Approval Cures Rare Genetic Disorders", "News", "CRISPR-based therapies have reached maturity, with the FDA approving a one-time treatment that permanently corrects three distinct genetic anomalies."),
    ("India Surpasses $10 Trillion Economy Milestone", "Business", "A surge in advanced manufacturing and a dominating global IT service sector has pushed India's GDP past the historic $10 trillion mark."),
    ("The Resurgence of Print Media in the Digital Age", "Lifestyle", "In an unexpected cultural shift, Gen Alpha is driving a massive revival of physical magazines and print journalism, seeking respite from screen fatigue."),
    ("Breakthrough in Nuclear Fusion Sustains Reaction for 24 Hours", "Technology", "The ITER facility has successfully maintained a net-positive fusion reaction for an entire day, proving the commercial viability of unlimited clean energy."),
    ("Urban Farming Revolutionizes Mega-City Food Supplies", "Lifestyle", "Vertical farming skyscrapers in Tokyo and New York are now producing enough organic yields to significantly reduce reliance on rural agriculture."),
    ("Major Tech Firm Unveils Fully Autonomous Robot Workforce", "Business", "In a controversial move, a leading logistics conglomerate has deployed a warehouse entirely operated by humanoid robots, achieving zero error rates."),
    ("Antarctic Ice Shelf Shows Signs of Re-freezing", "World", "Climate scientists report a surprising and localized reversal in ice melt, attributed to the aggressive geoengineering aerosol programs launched in 2024."),
    ("The Rise of Neuro-Linked Virtual Reality", "Technology", "A new consumer headset that translates neural signals directly into VR movement has hit the market, blurring the lines between physical and digital spaces."),
    ("Global Housing Crisis Addressed by 3D-Printed Neighborhoods", "News", "Governments in developing nations are mass-deploying 3D concrete printers, successfully erecting sustainable housing for thousands in a matter of weeks."),
    ("Traditional Office Spaces Converted to Mixed-Use Habitats", "Business", "As the hybrid work model solidifies permanently, commercial real estate developers are transforming vacant skyscrapers into indoor parks and living spaces."),
    ("Breakthrough in Deep-Ocean Plastic Cleanup", "World", "An autonomous fleet of solar-powered drones has successfully removed over 2 million tons of microplastics from the Great Pacific Garbage Patch this year."),
    ("The Evolution of Digital Nomad Visas", "Lifestyle", "Over 60 countries have now established a unified digital nomad visa program, allowing seamless, borderless living for the global remote workforce."),
    ("Next-Generation Quantum Internet Enters Public Testing", "Technology", "The first unhackable quantum communication network is now being tested by selected financial institutions, promising absolute data security.")
]

def generate_html_content(summary, cat):
    img1 = random.choice(images)
    img2 = random.choice(images)
    
    return f"""<p>{summary}</p>
<p>The implications of this development are sending shockwaves across the globe. Experts have been anticipating this shift for several years, but the speed of implementation has caught many off guard. "This is a paradigm shift in how we understand the current landscape," noted a leading industry analyst.</p>
<figure class="article-inline-image">
    <img src="{img1}" alt="Context Image 1">
    <figcaption>Visual context highlighting the recent developments in {cat}.</figcaption>
</figure>
<p>Furthermore, international regulatory bodies are scrambling to establish updated guidelines to manage the rapid changes. Preliminary reports indicate that significant investments are already being diverted to capitalize on this new trajectory. Stakeholders from North America to Southeast Asia are re-evaluating their long-term strategies.</p>
<figure class="article-inline-image">
    <img src="{img2}" alt="Context Image 2">
    <figcaption>Analysts review the latest data and its global impact.</figcaption>
</figure>
<p>As the situation continues to evolve, all eyes will remain focused on the long-term sustainability of these measures. WorldGlobal will continue to provide real-time updates, on-the-ground reporting, and deep analytical coverage as more information becomes available over the coming weeks.</p>"""

json_path = 'data/news.json'
with open(json_path, 'r', encoding='utf-8') as f:
    existing_data = json.load(f)

# The existing data has 7 items, let's keep them and append 23 to get 30.
# Let's fix the existing data to also use one of the reporters if they don't already have one, and ensure 3 images.
for item in existing_data:
    if "figure" not in item["content"]:
        img1 = random.choice(images)
        img2 = random.choice(images)
        item["content"] = item["content"] + f"""
<figure class="article-inline-image">
    <img src="{img1}" alt="Context Image 1">
</figure>
<p>Global reactions are pouring in as the situation develops. Industry experts predict widespread long-term ramifications.</p>
<figure class="article-inline-image">
    <img src="{img2}" alt="Context Image 2">
</figure>
<p>Stay tuned to WorldGlobal for continuous, highly detailed updates on this developing story.</p>
"""
    if item["author"] not in reporters:
        item["author"] = random.choice(reporters)

current_id = max(item["id"] for item in existing_data) if existing_data else 0

for i, (title, cat, summary) in enumerate(new_articles_data):
    current_id += 1
    
    # 2026-05-21 and subtract some random hours
    pub_date = datetime(2026, 5, 21, 12, 0) - timedelta(hours=random.randint(1, 48), minutes=random.randint(1, 60))
    
    slug = title.lower().replace(" ", "-").replace(",", "").replace(".", "").replace("'", "")
    
    new_item = {
        "id": current_id,
        "title": title,
        "slug": slug,
        "summary": summary,
        "content": generate_html_content(summary, cat),
        "image": random.choice(images),
        "author": random.choice(reporters),
        "date": pub_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "category": cat
    }
    existing_data.append(new_item)

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(existing_data, f, indent=2)

print(f"Generated {len(existing_data)} total articles in news.json.")
