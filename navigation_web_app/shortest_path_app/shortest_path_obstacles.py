import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from shapely.wkt import loads
from shapely import wkb
import geopandas as gpd
import momepy as mm
from shapely import geometry, ops
import json
import taxicab as tc
import re
from osmnx import convert
import pandas as pd 

ox.settings.use_cache = False
ox.settings.log_console = False


def connect_to_postgres(host, dbname, user, password):
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    return conn

def get_obstacles(type, conn, everything=False):
    if everything == True:
        cursor = conn.cursor()
        cursor.execute(f"""SELECT * FROM {type}""")
        obstacles  = cursor.fetchall()
        cursor.close()

        return obstacles
    
    elif everything == False:
        conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
        cursor = conn.cursor()
        cursor.execute(f"""SELECT index, ST_AsText(geom),nearest_edge_u,nearest_edge_v,meno,predpisana_vypocitana_normalna
        FROM {type}""")
        obstacles  = cursor.fetchall()
        cursor.close()

        return obstacles

#-------------------------------------------------------------------------#

def to_db(place_name):
    graph  = ox.graph_from_place(place_name, network_type="drive", simplify=False, truncate_by_edge=True)
    graph = ox.speed.add_edge_speeds(graph)
    graph = ox.speed.add_edge_travel_times(graph)
    
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav") 

    gdf_nodes, gdf_edges = ox.graph_to_gdfs(
        graph,
        nodes=True, edges=True,
        node_geometry=True,
        fill_edge_geometry=True)
    gdf_nodes.set_geometry("geometry")
    gdf_edges.set_geometry("geometry")

    gdf_edges = gdf_edges.reset_index() 

    gdf_nodes.to_postgis("ba_nodes", engine, if_exists='replace', index=True, index_label='osmid', schema='public')
    gdf_edges.to_postgis("ba_edges", engine, if_exists='replace', schema='public')

# to_db("Bratislava, Slovakia")

def from_db():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav") 
    nodes = gpd.read_postgis("SELECT * FROM ba_nodes;", engine, geom_col='geometry')
    edges = gpd.read_postgis("SELECT * FROM ba_edges;", engine, geom_col='geometry')

    G = nx.MultiDiGraph()

    for index, row in edges.iterrows():
        G.add_edge(row['u'], row['v'], key=row['key'], osmid=row['osmid'], oneway=row['oneway'], lanes=row['lanes'], highway=row['highway'], name=row['name'], ref=row['ref'], bridge=row['bridge'], width=row['width'], junction=row['junction'], tunnel=row['tunnel'], geometry=row['geometry'])

    for index, row in nodes.iterrows():
        G.add_node(row['osmid'], y=row['y'], x=row['x'], street_count=row['street_count'], ref=row['ref'], highway=row['highway'], geometry=row['geometry'])

    node_attrs = {node: {'y': data['y'], 'x': data['x'], 'street_count': data['street_count'], 'ref': data['ref'], 'highway': data['highway'], 'geometry': data['geometry']} for node, data in G.nodes(data=True)}
    nx.set_node_attributes(G, node_attrs)

    edge_attrs = {(u, v, k): {'osmid': d['osmid'], 'oneway': d['oneway'], 'lanes': d['lanes'], 'highway': d['highway'], 'name': d['name'], 'ref': d['ref'], 'bridge': d['bridge'], 'width': d['width'], 'junction': d['junction'], 'tunnel': d['tunnel'], 'geometry': d['geometry']} for u, v, k, d in G.edges(keys=True, data=True)}
    nx.set_edge_attributes(G, edge_attrs)

    G.graph['crs'] = edges.crs
    ox.distance.add_edge_lengths(G)
    
    return G

# from_db_gpt()

#-------------------------------------------------------------------------#


def update_nearest_edge(conn, point_id, u, v):
    cur = conn.cursor()
    cur.execute("UPDATE bridge_obstacles SET nearest_edge_u = %s, nearest_edge_v = %s WHERE index = %s", (u, v, point_id))
    conn.commit()
    cur.close()

def obstacles_nearest_edge():
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    graph  = ox.graph_from_place("Bratislava, Slovakia", network_type="drive", simplify=False, truncate_by_edge=True)

    bridge_obstacles = get_obstacles('bridge_obstacles',conn,everything=False)

    for record in bridge_obstacles:
        point_id, point_text, u, v,name,max_weight = record
        point_geometry = loads(point_text)
        if point_geometry is not None:
            lon, lat = point_geometry.x, point_geometry.y
            # Find nearest edge to the obstacle
            nearest_edge = ox.distance.nearest_edges(graph, lon, lat)
            if nearest_edge:
                u, v, _ = nearest_edge
                # Update the database with the nearest edge information
                update_nearest_edge(conn, point_id, u, v)
            else:
                print("Error: No nearest edges found for point:", (lat, lon))
        else:
            print("Error: Unable to parse geometry from text:", point_text)

    conn.close()
# obstacles_nearest_edge()


#function for export shortest path to geopackage - for qgis visualisation
def export_gpkg(graph, shortest_path):
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    shortest_path_nodes_gdf = nodes_gdf.loc[shortest_path]

    nodes_gdf.to_file('graph_data.gpkg', layer='nodes', driver='GPKG')
    shortest_path_nodes_gdf.to_file('shortest_path.gpkg', layer='shortest_path', driver='GPKG')

#function for extracting the first number from the string - max weight of the bridge
def extract_first_number(text):
    pattern = r'\d+(\.\d+)?'
    
    match = re.search(pattern, text)
    number = 0

    if match and (float(match.group()) < 1000):
        if match.group() is not None:
            return float(match.group())
    else:
        pass


#function to find the shortest path with obstacles, using graph from postgres DB - for now only plot the graph
def shortest_path(start,end,car_weight):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    #graph = graph_from_db_new("road_network_ba",conn)
    #graph_obstacles = graph_from_db_new("road_network_ba",conn)
    bridge_obstacles = get_obstacles('bridge_obstacles',conn)
    obstacles_edge = []

    graph_obstacles  = ox.graph_from_place("Bratislava, Slovakia", network_type="drive", simplify=False, truncate_by_edge=True, retain_all=True)
    #graph_obstacles_d = ox.get_digraph(graph_obstacles)
    graph  = ox.graph_from_place("Bratislava, Slovakia", network_type="drive", simplify=False, truncate_by_edge=True, retain_all=True)
    # print(graph)
    # print("-------------------")
    # print(graph_obstacles.edges)



    # graph_obstacles_proj = ox.project_graph(graph_obstacles)
    # graph_obstacles = ox.consolidate_intersections(graph_obstacles_proj, rebuild_graph=True, tolerance=15, dead_ends=False)

    # Remove edges with obstacles for specific car weight
    for record in bridge_obstacles:
        max_weight = extract_first_number(record[5])
        if max_weight is not None:
            if max_weight < car_weight:
                if record[2] is not None and record[3] is not None:
                    obstacles_edge.append((int(record[2]), int(record[3])))
    
    # print("Prekazky - hrany: ", obstacles_edge)
    # print(len(obstacles_edge))
    graph_obstacles.remove_edges_from(obstacles_edge) 
    # print("Prekazky: ",graph_obstacles.number_of_edges())
    # print("Normalny: ",graph.number_of_edges())

    # print(f"Graph obstacles length: {len(graph_obstacles.edges)}")
    # print(f"Graph length: {len(graph.edges)}")
    dif = nx.difference(graph, graph_obstacles)
    # print(f"Dif length: {len(dif.edges)}")

    ox.save_graph_geopackage(dif, filepath='hanicka_graph_dif_new.gpkg', directed=True)

    
    # fig, ax = ox.plot_graph(dif)

    # Add speeds and travel times to the graph
    # graph_obstacles = ox.speed.add_edge_speed(graph_obstacles)
    # graph_obstacles = ox.speed.add_edge_travel_times(graph_obstacles)

    
    
    # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # ox.plot_graph(graph, ax=ax1, node_color='w', edge_color='r', edge_linewidth=1, node_size=0, show=False)
    # ax1.set_title('Graph')

    # ox.plot_graph(graph_obstacles, ax=ax2, node_color='w', edge_color='r', edge_linewidth=1, node_size=0, show=False)
    # ax2.set_title('Graph obstacles')

    # plt.show()
   
    
    #nearest node to the points of origin and destination
    # orig = ox.distance.nearest_nodes(graph_obstacles, start[1], start[0])
    # dest = ox.distance.nearest_nodes(graph_obstacles, end[1], end[0])
    
    # nodes = [orig, dest]

    #Shortest path calculation
    #shortest_path = nx.shortest_path(graph_obstacles, nodes[0], nodes[1], weight='length',method='dijkstra')

    # route = tc.distance.shortest_path(graph_obstacles, start, end)

    # nodes_coords = [(graph_obstacles.nodes[node]['x'], graph_obstacles.nodes[node]['y']) for node in route[1]]

    # multi_line = geometry.MultiLineString([geometry.LineString(nodes_coords), route[2], route[3]])
    # shortest_path_line = ops.linemerge(multi_line)

    # geojson_geometry = json.dumps(shortest_path_line.__geo_interface__)
    
    # # route_map = ox.plot_route_folium(graph_obstacles, shortest_path, tiles = 'openstreetmap', fit_bounds = True )
    # return geojson_geometry

# shortest_path((48.1451, 17.1077),(48.1451, 17.1077), 50.0)

def sp_obstacles(start,end):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    bridge_obstacles = get_obstacles('bridge_obstacles',conn,everything=False)

    graph_obstacles  = ox.graph_from_place("Bratislava, Slovakia", network_type="drive", simplify=True, truncate_by_edge=True)

    bridge_coordinates = []
    for record in bridge_obstacles:
        point_id, point_text, u, v,name,max_weight = record
        point_geometry = loads(point_text)
        if point_geometry is not None:
            (lon, lat) = point_geometry.x, point_geometry.y
            bridge_coordinates.append((lat, lon))

    bridge_nodes = []
    for lat, lon in bridge_coordinates:
        point = geometry.Point(lon, lat)
        nearest_node = ox.distance.nearest_nodes(graph_obstacles, point.x, point.y)
        bridge_nodes.append(nearest_node)

    bridge_nodes_copy = bridge_nodes.copy()
    for node in bridge_nodes_copy:
        if node in graph_obstacles.nodes():
            for neighbor in graph_obstacles.neighbors(node):
                graph_obstacles.remove_edge(node, neighbor)


    route = tc.distance.shortest_path(graph_obstacles, start, end)

    nodes_coords = [(graph_obstacles.nodes[node]['x'], graph_obstacles.nodes[node]['y']) for node in route[1]]

    multi_line = geometry.MultiLineString([geometry.LineString(nodes_coords), route[2], route[3]])
    shortest_path_line = ops.linemerge(multi_line)

    geojson_geometry = json.dumps(shortest_path_line.__geo_interface__)
    
    return geojson_geometry

# Function for calculae shortest path without obstacles - working fine
def sp(start,end):
    # conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    #graph = graph_from_db_new("road_network_ba",conn)

    # graph  = ox.graph_from_place("Bratislava, Slovakia", network_type="drive", simplify=True, truncate_by_edge=True)
    graph = from_db()

    # Version 1 - using OSMNX library - can use also travel time, not so accurate nearest node
    # Add speeds and travel times to the graph
    # graph_obstacles = ox.speed.add_edge_speed(graph_obstacles)
    # graph_obstacles = ox.speed.add_edge_travel_times(graph_obstacles)
 
    #nearest node to the points of origin and destination
    # orig = ox.distance.nearest_nodes(graph_obstacles, start[1], start[0])
    # dest = ox.distance.nearest_nodes(graph_obstacles, end[1], end[0])
    
    # nodes = [orig, dest]

    #Shortest path calculation
    #shortest_path = nx.shortest_path(graph_obstacles, nodes[0], nodes[1], weight='length',method='dijkstra')


    # Version 2 - using taxicab library - cant use travel time, more accurate nearest node
    route = tc.distance.shortest_path(graph, start, end)

    nodes_coords = [(graph.nodes[node]['x'], graph.nodes[node]['y']) for node in route[1]]

    multi_line = geometry.MultiLineString([geometry.LineString(nodes_coords), route[2], route[3]])
    shortest_path_line = ops.linemerge(multi_line)

    geojson_geometry = json.dumps(shortest_path_line.__geo_interface__)
    
    return geojson_geometry