from django.core.management.base import BaseCommand
from news.views import fetch_gnews_api

class Command(BaseCommand):
    help = 'Fetches the latest news from the GNews API and appends it to the existing news data.'

    def handle(self, *args, **options):
        self.stdout.write('Starting news fetch...')
        try:
            fetch_gnews_api()
            self.stdout.write(self.style.SUCCESS('Successfully updated news database.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch news: {e}'))
