from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('support', views.support, name='support'),
    path('upgrade', views.upgrade, name='upgrade'),
    path('upgrade/<int:success>', views.upgrade, name='upgrade'),
    path('subscribe', views.subscribe, name='subscribe'),
    path('subscribed/<str:email>/<str:subscription_id>', views.subscribed, name='subscribed'),
    path('success/<str:amount>/<str:customer_id>', views.success, name='success'),
    path('charge', views.charge, name='charge'),
    path('cancel', views.cancel, name='cancel'),
    path('cancelled/<str:expiration>', views.cancelled, name='cancelled')
]
