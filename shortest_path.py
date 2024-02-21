import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from shapely.ops import unary_union, polygonize
import psycopg2
from shapely.wkt import loads

def connect_to_postgres(host, dbname, user, password):
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    return conn

def save_graph_to_db(graph,table):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')    
    ox.save_graph_to_postgis(graph, conn, table)
    conn.close()

def get_obstacles(type,conn):
    cursor = conn.cursor()
    cursor.execute(f"""SELECT ST_AsText(geom) FROM {type}""")
    bridge_obstacles  = cursor.fetchall()
    cursor.close()
    return bridge_obstacles 

def write2db(input,table):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

    column_name = "id_edge"
    column_type = "INT"

    cur = conn.cursor()
    alter_query = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type};"
    cur.execute(alter_query)
    conn.commit()

    cur.close()
    conn.close()



#Import OSM data
def import_graph_to_DB(place_name,table):
    place_name = "Bratislava, Slovakia"
    graph  = ox.graph_from_place(place_name, network_type="drive", simplify=True)
    save_graph_to_db(graph, table)
    return graph

graph = import_graph_to_DB("Bratislava, Slovakia","BA_roads_network")
graph_proj = ox.project_graph(graph, to_crs='EPSG:4326')


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

    #Apply obstacles to the graph - using high weight for the edges with obstacles
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

    bridge_obstacles = get_obstacles(bridge_obstacles,conn)

    closed_points = []
    for record in bridge_obstacles:
        point_text = record[0]
        point_geometry = loads(point_text)
        if point_geometry is not None:
            lon, lat = point_geometry.x, point_geometry.y
            closed_points.append((lat, lon))
        else:
            print("Error: Unable to parse geometry from text:", point_text)

    closed_roads = []
    for lat, lon in closed_points:
        nearest_edge = ox.distance.nearest_edges(graph_proj, lon, lat)

        if isinstance(nearest_edge, int):
            print("Error: No nearest edges found for point:", (lat, lon))
            continue
        u, v, _ = nearest_edge
        graph_proj.add_edge(u, v, length=99999999)
        closed_roads.append((u,v))

    """
    #Shortest path calculation
    shortest_path = nx.shortest_path(graph_proj, nodes[0], nodes[1], weight='length')

    #Plot shortest path
    fig, ax = ox.plot_graph_route(graph_proj, shortest_path, route_color='r', route_linewidth=4, node_size=0)
    plt.show()
    """
    conn.close()

    return closed_roads

#find_shortest_path(Xo,Xd,graph_proj)

#closed_roads = find_shortest_path(Xo,Xd,graph_proj)


#Plot the road network with roads with obstacles highlighted  
def plot_closed_roads(graph, closed_edges):
    print(closed_edges)
    edge_colors = []
    for u, v in graph.edges():
        if (u, v) in closed_edges:
            edge_colors.append('red')
        else:
            edge_colors.append('grey')    
    # Plot the road network with closed roads highlighted
    fig, ax = ox.plot_graph(graph, node_size=0, edge_color=edge_colors, edge_linewidth=0.5)
    
    plt.show()

#Find and plot the closed roads
#plot_closed_roads(graph_proj, closed_roads)

#Export shortest path to GeoPackage
def export_gpkg(graph, shortest_path):
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    shortest_path_nodes_gdf = nodes_gdf.loc[shortest_path]

    nodes_gdf.to_file('graph_data.gpkg', layer='nodes', driver='GPKG')
    shortest_path_nodes_gdf.to_file('shortest_path.gpkg', layer='shortest_path', driver='GPKG')