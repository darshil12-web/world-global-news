from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('category/<str:category>/', views.category_games, name='category_games'),
    path('play/<slug:slug>/', views.play_game, name='play_game'),
    
    # Custom Roblox Replica Pages
    path('profile/', views.profile, name='profile'),
    path('avatar/', views.avatar, name='avatar'),
    path('catalog/', views.catalog, name='catalog'),
    path('robux/', views.robux_page, name='robux_page'),
    
    # Legal / Static pages
    path('about-us/', views.about, name='about'),
    path('contact-us/', views.contact, name='contact'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('privacy-policy/', views.privacy, name='privacy'),
    path('terms-of-service/', views.terms, name='terms'),
    path('cookie-policy/', views.cookie, name='cookie'),
    path('dmca/', views.dmca, name='dmca'),
    path('editorial-policy/', views.editorial_policy, name='editorial_policy'),
    path('set-username/', views.set_username, name='set_username'),
]
