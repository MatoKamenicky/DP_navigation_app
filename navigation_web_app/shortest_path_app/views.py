from django.shortcuts import render
import folium
from . import shortest_path_obstacles as spo
from .forms import CoordinatesForm 
from .models import Coordinates
from shapely.wkt import loads
from folium import plugins
import geojson




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
    figure = folium.Figure()
    m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=10)

    #view obstacles
    fg = folium.FeatureGroup(name="Obstacles", show=False).add_to(m)
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

    """
    m.add_to(figure)
    figure.render()
    context={'map':figure}
    """
    context = {'geojson_data': geojson_data}
    return render(request, 'home.html', context)


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







