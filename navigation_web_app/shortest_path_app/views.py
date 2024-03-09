from django.shortcuts import render
import folium
from . import shortest_path_obstacles as spo
from .forms import CoordinatesForm 



def map_view(request):
    m = folium.Map(location=[48.14225666993606, 17.119759122997106], zoom_start=10)
    folium.Marker(location=[48.14225666993606, 17.119759122997106], popup='Bratislava').add_to(m)
    m = m._repr_html_()

    return render(request,'map.html', {'map': m})


def transform_xy(request):
    if request.method == 'POST':
        form = CoordinateForm_xy(request.POST)
        if form.is_valid():
            x = int(form.cleaned_data['x_coordinate'])
            y = int(form.cleaned_data['y_coordinate'])

            result = ts.transform_coordinates_2D(x, y)
            Coordinate.objects.create(x_coordinate=x, y_coordinate=y, z_coordinate=None, result_x=result[0], result_y=result[1], result_z=None)
            return redirect('result')
    else:
        form = CoordinateForm_xy()
    return render(request, 'transform_xy.html', {'form': form})



