from django.shortcuts import render, redirect
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
    if request.method == 'POST':
        form = CarDimensionsForm(request.POST)
        if form.is_valid():
            # height = form.cleaned_data['height']
            # width = form.cleaned_data['width']
            weight = form.cleaned_data['weight']
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

def obstacles_view(request):
    if request.method == 'POST':
        json_data = json.loads(request.body)
        weight = float(json_data.get('car_weight'))
        conn = spo.connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
        obstacles = spo.get_obstacles('bridge_obstacles',conn)
        features = []

        for record in obstacles:
            point_id, point_text, u, v,name, max_weight = record
            point_geometry = loads(point_text)
            max_weight_bridge = spo.extract_first_number(max_weight)    
            if max_weight_bridge is not None:
                if (point_geometry is not None) and (weight > max_weight_bridge):
                    lon, lat = point_geometry.x, point_geometry.y
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "max_weight": max_weight_bridge
                        }
                    }
                    features.append(feature)

        feature_collection = {
        "type": "FeatureCollection",
        "features": features
        }
        geojson_data = geojson.loads(geojson.dumps(feature_collection))
        print(geojson_data)
        return JsonResponse(geojson_data,safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def route_view(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        
        start_lat = body['start_lat']
        start_lng = body['start_lon']
        end_lat = body['end_lat']
        end_lng = body['end_lon']
        car_weight = float(body['car_weight'])

        start_point = (start_lat, start_lng)
        end_point = (end_lat, end_lng)

        route = spo.shortest_path(start_point, end_point, car_weight)
        return JsonResponse(route,safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def custom_404(request, exception):
    return render(request, 'C:\GAK\_ING_studium\ING_3_sem\DP_navigation_app\navigation_web_app\shortest_path_app\templates\404.html', status=404)

