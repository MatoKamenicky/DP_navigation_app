import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from shapely.ops import unary_union, polygonize
import contextily as ctx

#Import OSM data
place_name = "Bratislava, Slovakia"
graph  = ox.graph_from_place(place_name, network_type="drive", simplify=True)
graph_proj = ox.project_graph(graph, to_crs='EPSG:4326')

#Import OSM data to database
"""
engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgis_skuska")  
gdf_nodes.to_postgis("osm_nodes", engine)
gdf_edges.to_postgis("osm_edges", engine)
"""

#Nearest node to the points of origin and destination
Xo = 48.15778031493731, 17.12004649807463
Xd = 48.177666652910766, 17.04614727569561

def find_shortest_path(Xo,Xd):
    #Version with good results of origin and destination nodes
    node_Xo = ox.distance.nearest_nodes(graph_proj, Xo[1], Xo[0])
    node_Xd = ox.distance.nearest_nodes(graph_proj, Xd[1], Xd[0])
    nodes = [node_Xo, node_Xd]

    #Index of the nodes - maybe not necessary - results ??
    """
    node = ox.nearest_nodes(graph_proj, Xo, Xd)
    Xo_node = [i for i, x in enumerate(list(graph_proj)) if x == node[0]]
    Xd_node = [i for i, x in enumerate(list(graph_proj)) if x == node[1]]
    origin = list(graph_proj)[Xo_node[0]]
    destination = list(graph_proj)[Xd_node[0]]
    """
    #Shortest path calculation
    shortest_path = nx.shortest_path(graph_proj, nodes[0], nodes[1], weight='length')

    #Plot shortest path
    fig, ax = ox.plot_graph_route(graph_proj, shortest_path, route_color='r', route_linewidth=4, node_size=0)
    ctx.add_basemap(ax, crs=graph_proj.graph['crs'], source=ctx.providers.OpenStreetMap.Mapnik)
    plt.savefig('my_route_plot.png')

find_shortest_path(Xo,Xd)

#Export shortest path to GeoPackage
def export_gpkg(graph, shortest_path):
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    shortest_path_nodes_gdf = nodes_gdf.loc[shortest_path]

    nodes_gdf.to_file('graph_data.gpkg', layer='nodes', driver='GPKG')
    shortest_path_nodes_gdf.to_file('shortest_path.gpkg', layer='shortest_path', driver='GPKG')