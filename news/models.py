from django.db import models
from django.utils.text import slugify

class Game(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True, default="", db_index=True)
    category = models.CharField(max_length=100, default="Action")
    description = models.TextField(blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500)
    iframe_url = models.URLField(max_length=500)
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.title) or "game"
            slug = original_slug
            num = 1
            while Game.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Player(models.Model):
    username = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
