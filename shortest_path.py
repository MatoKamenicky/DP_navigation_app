import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from shapely.ops import unary_union, polygonize
import contextily as ctx
import psycopg2
from shapely.wkt import loads

def connect_to_postgres(host, dbname, user, password):
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    return conn

def get_bridge_obstacles(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT ST_AsText(geom) FROM bridge_obstacles")
    bridge_obstacles  = cursor.fetchall()
    cursor.close()
    return bridge_obstacles 


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

#Xo = 48.15778031493731, 17.12004649807463
#Xd = 48.177666652910766, 17.04614727569561

Xo = 48.139948579614924, 17.099163757685766
Xd = 48.1314118173731, 17.112115551449396

def find_shortest_path(Xo,Xd,graph_proj):
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

    #Apply obstacles to the graph - using high weight for the edges with obstacles
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

    bridge_obstacles = get_bridge_obstacles(conn)

    closed_points = []
    for record in bridge_obstacles:
        point_text = record[0]
        point_geometry = loads(point_text)
        if point_geometry is not None:
            lon, lat = point_geometry.x, point_geometry.y
            closed_points.append((lat, lon))
        else:
            print("Error: Unable to parse geometry from text:", point_text)

    for lat, lon in closed_points:
        nearest_edge = ox.distance.nearest_edges(graph_proj, lon, lat)

        #print(nearest_edge)

        if isinstance(nearest_edge, int):
            print("Error: No nearest edges found for point:", (lat, lon))
            continue
        u, v, _ = nearest_edge
        graph_proj.add_edge(u, v, length=99999999) 


    #Shortest path calculation
    shortest_path = nx.shortest_path(graph_proj, nodes[0], nodes[1], weight='length')

    #Plot shortest path
    fig, ax = ox.plot_graph_route(graph_proj, shortest_path, route_color='r', route_linewidth=4, node_size=0)
    plt.show()

    conn.close()
    """
    ctx.add_basemap(ax, crs=graph_proj.graph['crs'], source=ctx.providers.OpenStreetMap.Mapnik)
    plt.savefig('my_route_plot.png')
    """

find_shortest_path(Xo,Xd,graph_proj)

#Export shortest path to GeoPackage
def export_gpkg(graph, shortest_path):
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    shortest_path_nodes_gdf = nodes_gdf.loc[shortest_path]

    nodes_gdf.to_file('graph_data.gpkg', layer='nodes', driver='GPKG')
    shortest_path_nodes_gdf.to_file('shortest_path.gpkg', layer='shortest_path', driver='GPKG')