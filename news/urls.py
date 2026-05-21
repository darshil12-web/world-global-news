from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('category/<str:category>/', views.category_news, name='category_news'),
    path('article/<slug:slug>/', views.news_detail, name='news_detail'),
    path('about-us/', views.about, name='about'),
    path('contact-us/', views.contact, name='contact'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('privacy-policy/', views.privacy, name='privacy'),
    path('terms-of-service/', views.terms, name='terms'),
    path('cookie-policy/', views.cookie, name='cookie'),
    
    # API endpoints
    path('api/comments/<slug:slug>/', views.api_get_comments, name='api_get_comments'),
    path('api/comments/<slug:slug>/post/', views.api_post_comment, name='api_post_comment'),
]
