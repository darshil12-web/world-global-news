from news.models import Game

def sidebar_games_processor(request):
    try:
        # Fetch a pool of 60 random games
        games_pool = list(Game.objects.all().order_by('?')[:60].values('id', 'title', 'thumbnail_url', 'slug'))
    except Exception:
        games_pool = []
    return {
        'sidebar_games_pool': games_pool
    }
