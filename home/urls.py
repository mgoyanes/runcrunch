from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('account', views.account, name='home'),
    path('register', views.register, name='register'),
    path('delete', views.delete, name='delete'),
    path('connect-to-strava', views.connect_to_strava, name='connect-to-strava'),
    path('privacy', views.privacy, name='privacy'),

    path('', include('django.contrib.auth.urls'))
]
