from django.urls import path
from . import views

urlpatterns = [
    path('/map', views.map_view, name='map_view'),
    path('/shortestpath', views.shortest_path, name='shortest_path'),
    path('/shortest_pat_cal', views.calculate_shortest_path, name='shortest_path'),
    path('/home', views.home, name='home'),


]