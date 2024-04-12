from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.home, name='home2'),
    path('directions/', views.route_view, name='route_view'),
    path('obstacles/', views.obstacles_view, name='obstacles'),
]