from django.shortcuts import render, redirect
import folium
from . import shortest_path_obstacles as spo
from .forms import CarDimensionsForm 
from shapely.wkt import loads
import geojson
from django.http import JsonResponse
import json


def car_dimensions(request):
    if request.method == 'POST':
        form = CarDimensionsForm(request.POST)
        if form.is_valid():
            height = form.cleaned_data['height']
            width = form.cleaned_data['width']
            weight = form.cleaned_data['weight']
    else:
        form = CarDimensionsForm()
    return render(request, 'home.html', {'form': form})


def home(request):
    # Forms for car dimensions
    if request.method == 'POST':
        form = CarDimensionsForm(request.POST)
        if form.is_valid():
            height = form.cleaned_data['height']
            width = form.cleaned_data['width']
            weight = form.cleaned_data['weight']

            # request.session['weight'] = weight
            # return redirect('route_view') 
    else:
        form = CarDimensionsForm()
    
    # Get obstacles from the database and create a GeoJSON object
    conn = spo.connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    obstacles = spo.get_obstacles('bridge_obstacles',conn)
    features = []

    for record in obstacles:
        point_id, point_text, u, v,name,max_weight = record
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

    context = {'form': form, 'geojson_data': geojson_data}
    return render(request, 'home.html', context)


def route_view(request):
    # car_weight = request.session.get('weight')
    # if car_weight is None:
    #     return JsonResponse({'error': 'Weight not found in session'}, status=400)
    

    if request.method == 'POST':
        body = json.loads(request.body)
        
        start_lat = body['start_lat']
        start_lng = body['start_lon']
        end_lat = body['end_lat']
        end_lng = body['end_lon']

        start_point = (start_lat, start_lng)
        end_point = (end_lat, end_lng)

        car_weight = request.POST.get('weight', 0)
        route = spo.shortest_path(start_point, end_point, car_weight)

        print(route)

        return JsonResponse(route,safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def custom_404(request, exception):
    return render(request, 'C:\GAK\_ING_studium\ING_3_sem\DP_navigation_app\navigation_web_app\shortest_path_app\templates\404.html', status=404)



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
