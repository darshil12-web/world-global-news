from django.db import models

class Game(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    thumbnail_url = models.URLField(max_length=500)
    iframe_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
