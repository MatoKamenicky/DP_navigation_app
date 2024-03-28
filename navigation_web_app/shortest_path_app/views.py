from django.shortcuts import render
import folium
from . import shortest_path_obstacles as spo
from .forms import CoordinatesForm 
from .models import Coordinates
from shapely.wkt import loads
from folium import plugins
import geojson
from django.http import JsonResponse
import json




def map_view(request):
    m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=10)
    folium.Marker(location=[48.14225666993606, 17.119759122997106], popup='Bratislava').add_to(m)
    m = m._repr_html_()
    return render(request,'map.html', {'map': m})



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

"""
#raster layers
folium.TileLayer('Open Street Map').add_to(m)
folium.TileLayer('Stamen Terrain').add_to(m)
folium.TileLayer('Stamen Toner').add_to(m)
folium.TileLayer('Stamen Watercolor').add_to(m)
folium.TileLayer('CartoDB Positron').add_to(m)
folium.TileLayer('CartoDB Dark_Matter').add_to(m)
"""

def home(request):
    conn = spo.connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    obstacles = spo.get_obstacles('bridge_obstacles',conn)

    features = []
    
    for record in obstacles:
        point_id, point_text, u, v,name = record
        point_geometry = loads(point_text)
        if point_geometry is not None:
            lon, lat = point_geometry.x, point_geometry.y
            feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "name": name
            }
            }
            features.append(feature)

    feature_collection = {
    "type": "FeatureCollection",
    "features": features
    }
    geojson_data = geojson.loads(geojson.dumps(feature_collection))

    context = {'geojson_data': geojson_data}
    return render(request, 'home.html', context)


#This view is now not very useful, because it is possible to view the obstacles on the map in the layer control
def view_obstacles(request):
    conn = spo.connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

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
    
    if request.method == 'POST':
        
        start_lat = float(request.POST.get('number1'))
        start_lng = float(request.POST.get('number2'))
        end_lat = float(request.POST.get('number3'))
        end_lng = float(request.POST.get('number4'))

        start_point = (start_lat, start_lng)
        end_point = (end_lat, end_lng)

        route = spo.shortest_path(start_point, end_point)

        route_json = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": route
        }
        }

        return JsonResponse(route_json)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def custom_404(request, exception):
    return render(request, 'C:\GAK\_ING_studium\ING_3_sem\DP_navigation_app\navigation_web_app\shortest_path_app\templates\404.html', status=404)







