from django.urls import path
from . import views

urlpatterns = [
    path('map/', views.map_view, name='map_view'),
    path('shortestpath/', views.shortest_path, name='shortest_path'),
    path('home/', views.home, name='home'),
    path('view_obstacles/', views.view_obstacles, name='view_obstacles'),
    path('directions/', views.route_view, name='route_view'),
]