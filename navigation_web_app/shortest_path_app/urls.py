from django.urls import path
from . import views

urlpatterns = [
    path('map/', views.map_view, name='map_view'),
    path('home/', views.home, name='home'),
    path('', views.home, name='home2'),
    path('view_obstacles/', views.view_obstacles, name='view_obstacles'),
    path('directions/', views.route_view, name='route_view'),
]