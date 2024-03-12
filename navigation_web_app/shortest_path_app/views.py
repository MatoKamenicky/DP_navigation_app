from django.http import HttpResponse
from django.shortcuts import render
from flask import redirect
import folium
from . import shortest_path_obstacles as spo
from .forms import CoordinatesForm 
from .models import Coordinates
import json
from shapely.geometry import LineString, Point
from shapely.wkt import loads




def map_view(request):
    m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=10)
    folium.Marker(location=[48.14225666993606, 17.119759122997106], popup='Bratislava').add_to(m)
    m = m._repr_html_()
    return render(request,'map.html', {'map': m})



def shortest_path(request):
    if request.method == 'POST':
        form = CoordinatesForm(request.POST)
        if form.is_valid():
            start_lat = int(form.cleaned_data['start_lat'])
            start_lon = int(form.cleaned_data['start_lon'])
            end_lat = int(form.cleaned_data['end_lat'])
            end_lon = int(form.cleaned_data['end_lon'])
        
            start_point = (start_lat, start_lon)
            end_point = (end_lat, end_lon)

            route = spo.shortest_path(start_point, end_point)
            Coordinates.objects.create(start_lat=start_lat, start_lon=start_lon, end_lat=end_lat, end_lon=end_lon)
            return redirect('result')
    else:
        form = CoordinatesForm()
    return render(request, 'transform_xy.html', {'form': form})

"""
def result(request,start_point,end_point):
    figure = folium.Figure()
    route=spo.shortest_path(start_point,end_point)
    m = folium.Map(location=[(route['start_point'][0]),
                                 (route['start_point'][1])], 
                       zoom_start=10)
    m.add_to(figure)
    folium.PolyLine(route['route'],weight=8,color='blue',opacity=0.6).add_to(m)
    folium.Marker(location=route['start_point'],icon=folium.Icon(icon='play', color='green')).add_to(m)
    folium.Marker(location=route['end_point'],icon=folium.Icon(icon='stop', color='red')).add_to(m)
    figure.render()
    context={'map':figure}
    return render(request,'showroute.html',context)
"""
def result(request):
    shortest_path = request.session.get('shortest_path')  
    if shortest_path:
        map_center = shortest_path[0]
        my_map = folium.Map(location=map_center, zoom_start=10)

        folium.PolyLine(locations=shortest_path, color='blue').add_to(my_map)

        map_html = my_map._repr_html_()

        return render(request, 'result.html', {'map_html': map_html})
    else:
        return HttpResponse("Shortest path not found.")

"""
def coor_form(request):
    form = CoordinatesForm(request.POST or None)
    shortest_path = None
    if request.method == 'POST' and form.is_valid():
        start_lat = int(form.cleaned_data['start_lat'])
        start_lon = int(form.cleaned_data['start_lon'])
        end_lat = int(form.cleaned_data['end_lat'])
        end_lon = int(form.cleaned_data['end_lon'])

        start_point = (start_lat, start_lon)
        end_point = (end_lat, end_lon)
        shortest_path = spo.shortest_path(start_point, end_point)

        request.session['shortest_path'] = json.dumps(shortest_path)

        return redirect('result')
    else:
        form = CoordinatesForm()
    return render(request, 'coor_form.html', {'form': form, 'shortest_path': shortest_path})
"""

def home(request):
    form = CoordinatesForm(request.POST or None)
    route = None
    if request.method == 'POST' and form.is_valid():
        start_lat = int(form.cleaned_data['start_lat'])
        start_lon = int(form.cleaned_data['start_lon'])
        end_lat = int(form.cleaned_data['end_lat'])
        end_lon = int(form.cleaned_data['end_lon'])

        start_point = (start_lat, start_lon)
        end_point = (end_lat, end_lon)

        route = spo.shortest_path(start_point, end_point)
        route_line = LineString(list(route.geometry.values))

        request.session['shortest_path'] = json.dumps(route)

        figure = folium.Figure()
        m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=10)
        
        folium.Marker(start_point, popup='Start Point').add_to(m)
        folium.Marker(end_point, popup='End Point').add_to(m)

        #raster layers
        folium.raster_layers.TileLayer('Open Street Map').add_to(m)
        folium.raster_layers.TileLayer('Stamen Terrain').add_to(m)
        folium.raster_layers.TileLayer('Stamen Watercolor').add(m)
        folium.raster_layers.TileLayer('CartoDB Positron').add(m)
        folium.raster_layers.TileLayer('CartoDB Dark_Matter').add(m)

        folium.LayerControl().add_to(m)

        m.add_to(figure)
        figure.render()
        context={'map':figure}
        #map_html = m.get_root().render()

        return render(request, 'home_new.html', {'form': form, 'shortest_path': route}, context)
    else:
        form = CoordinatesForm()
        return render(request, 'home_new.html', {'form': form})


def view_obstacles(request):
    conn = spo.connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

    obstacles_info = spo.get_obstacles('bridge_obstacles',conn,everything=True)
    obstacles = spo.get_obstacles('bridge_obstacles',conn)
    figure = folium.Figure()
    m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=12)

    for record in obstacles:
        point_id, point_text, u, v,name = record
        point_geometry = loads(point_text)
        if point_geometry is not None:
            lon, lat = point_geometry.x, point_geometry.y
            folium.Marker(location=[lat, lon], popup=name).add_to(m)

    m.add_to(figure)
    figure.render()
    context={'map':figure}

    return render(request, 'view_obstacles.html', context)

def route_view(request):
    figure = folium.Figure()
    m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=12)

    start_point = (48.16703839996931, 17.078660578675134)
    end_point = (48.15520311675808, 17.137080529772206)
    route = spo.shortest_path(start_point, end_point)

    
    #folium.PolyLine(locations=route,weight=8,color='blue',opacity=0.6).add_to(m)


    folium.Marker(location=start_point, popup='Start point').add_to(m)
    folium.Marker(location=end_point, popup='End point').add_to(m)

    """
    #raster layers
    folium.raster_layers.TileLayer('Open Street Map',attr='attribution').add_to(m)
    folium.raster_layers.TileLayer('Stamen Terrain',attr='attribution').add_to(m)
    folium.raster_layers.TileLayer('Stamen Watercolor',attr='attribution').add(m)
    folium.raster_layers.TileLayer('CartoDB Positron',attr='attribution').add(m)
    folium.raster_layers.TileLayer('CartoDB Dark_Matter',attr='attribution').add(m)

    folium.LayerControl().add_to(m)
    """
    route.add_to(figure)
    m.add_to(figure)
    figure.render()
    context={'map':figure}

    return render(request, 'shortest_path.html', context)


def custom_404(request, exception):
    return render(request, 'C:\GAK\_ING_studium\ING_3_sem\DP_navigation_app\navigation_web_app\shortest_path_app\templates\404.html', status=404)







