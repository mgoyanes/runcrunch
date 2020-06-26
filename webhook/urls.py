from django.urls import path, include
from . import views

urlpatterns = [
        path('', views.event, name='webhook_event')
        ]