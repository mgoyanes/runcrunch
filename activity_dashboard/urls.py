from django.urls import path, include
from . import views

urlpatterns = [
        path('', views.activity_dashboard, name='activity_dashboard'),
        path('<int:activity_id>', views.activity_detail, name='activity_detail'),
        path('<int:activity_id>/<str:key>', views.shareable, name='shareable'),
        path('heatmap', views.heatmap, name='heatmap'),
        path('trends', views.trends, name='trends'),
        path('error', views.error, name='error'),
        path('privacy', views.privacy, name='privacy'),
        #path('<int:activity_id>/edit', views.edit, name='edit')
        ]