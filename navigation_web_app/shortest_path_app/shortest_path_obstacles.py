import osmnx as ox
import networkx as nx
import psycopg2
from sqlalchemy import create_engine
from shapely.wkt import loads
import geopandas as gpd
from shapely import geometry, ops
import json
import taxicab as tc
from . import distance as dist
import re
import matplotlib.pyplot as plt

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


# Function for creatinggraph and save it to the database
def to_db(place_name):
    bbox = 48.31,48.00,16.95,17.29
    graph = ox.graph_from_bbox(bbox=bbox, network_type="drive", simplify=False, truncate_by_edge=True)
    # graph  = ox.graph_from_place(place_name, network_type="drive", simplify=False, truncate_by_edge=True)
    # graph = ox.speed.add_edge_speeds(graph)
    # graph = ox.speed.add_edge_travel_times(graph)
    
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav") 

    gdf_nodes, gdf_edges = ox.graph_to_gdfs(
        graph,
        nodes=True, edges=True,
        node_geometry=True,
        fill_edge_geometry=True)
    gdf_nodes.set_geometry("geometry")
    gdf_edges.set_geometry("geometry")

    gdf_edges = gdf_edges.reset_index() 

    gdf_nodes.to_postgis("ba_nodes_bbox", engine, if_exists='replace', index=True, index_label='osmid', schema='public')
    gdf_edges.to_postgis("ba_edges_bbox", engine, if_exists='replace', schema='public')

# to_db("Bratislava, Slovakia")

# Function for loading graph from the database
def from_db():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav") 
    nodes = gpd.read_postgis("SELECT * FROM ba_nodes_bbox;", engine, geom_col='geometry')
    edges = gpd.read_postgis("SELECT * FROM ba_edges_bbox;", engine, geom_col='geometry')

    graph = nx.MultiDiGraph()

    for index, row in edges.iterrows(): 
        graph.add_edge(row['u'], row['v'], key=row['key'], osmid=row['osmid'], lanes=row['lanes'], ref=row['ref'], name=row['name'], highway=row['highway'], maxspeed=row['maxspeed'], oneway=row['oneway'], reversed=row['reversed'], length=row['length'], junction=row['junction'], bridge=row['bridge'], geometry=row['geometry'])

    for index, row in nodes.iterrows():
        graph.add_node(row['osmid'], y=row['y'], x=row['x'], street_count=row['street_count'], highway=row['highway'], geometry=row['geometry'])

    node_attrs = {node: {'y': data['y'], 'x': data['x'], 'street_count': data['street_count'], 'highway': data['highway'], 'geometry': data['geometry']} for node, data in graph.nodes(data=True)}
    nx.set_node_attributes(graph, node_attrs)

    edge_attrs = {(u, v, k): {'osmid': d['osmid'], 'oneway': d['oneway'], 'length': d['length'], 'maxspeed': d['maxspeed'], 'lanes': d['lanes'], 'highway': d['highway'], 'name': d['name'], 'ref': d['ref'], 'bridge': d['bridge'], 'junction': d['junction'], 'geometry': d['geometry']} for u, v, k, d in graph.edges(keys=True, data=True)}
    nx.set_edge_attributes(graph, edge_attrs)


    graph.graph['crs'] = edges.crs
    ox.distance.add_edge_lengths(graph)

    return graph

# from_db()


def update_nearest_edge(conn, point_id, u, v):
    cur = conn.cursor()
    cur.execute("UPDATE bridge_obstacles SET nearest_edge_u = %s, nearest_edge_v = %s WHERE index = %s", (u, v, point_id))
    conn.commit()
    cur.close()

# Function for finding nearest edge of the graph to the obstacles
def obstacles_nearest_edge():
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    graph = from_db()

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


# Function for export shortest path to geopackage - for qgis visualisation
def export_gpkg(graph, shortest_path):
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    shortest_path_nodes_gdf = nodes_gdf.loc[shortest_path]

    nodes_gdf.to_file('graph_data.gpkg', layer='nodes', driver='GPKG')
    shortest_path_nodes_gdf.to_file('shortest_path.gpkg', layer='shortest_path', driver='GPKG')

# Function for extracting the first number from the string - max weight of the bridge
def extract_first_number(text):
    pattern = r'\d+(\.\d+)?'
    
    match = re.search(pattern, text)
    number = 0

    if match and (float(match.group()) < 1000):
        if match.group() is not None:
            return float(match.group())
    else:
        pass


# Function to find the shortest path with obstacles, using graph from postgres DB - for now only plot the graph
def shortest_path(start,end, car_weight, type):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    bridge_obstacles = get_obstacles('bridge_obstacles',conn)
    obstacles_edge = []

    graph_obstacles  = from_db()  

    # Remove edges with obstacles for specific car weight
    for record in bridge_obstacles:
        max_weight = extract_first_number(record[5])
        if max_weight is not None:
            if max_weight < car_weight:
                if record[2] is not None and record[3] is not None:
                    obstacles_edge.append((int(record[2]), int(record[3])))
  
    graph_obstacles.remove_edges_from(obstacles_edge) 

    # Save difference of the graph and graph_obstacles geopackage
    # dif = nx.difference(graph, graph_obstacles)
    # ox.save_graph_geopackage(dif, filepath='graph_dif_last_last_chance.gpkg', directed=True)

    # Version 1 - using OSMNX library - can use also travel time, not so accurate nearest node
    # Add speeds and travel times to the graph
    graph_obstacles = ox.speed.add_edge_speeds(graph_obstacles)
    graph_obstacles = ox.speed.add_edge_travel_times(graph_obstacles)
   
    #nearest node to the points of origin and destination
    # orig = ox.distance.nearest_nodes(graph_obstacles, start[1], start[0])
    # dest = ox.distance.nearest_nodes(graph_obstacles, end[1], end[0])
    
    # nodes = [orig, dest]
    
    # #Shortest path calculation
    # shortest_path = nx.shortest_path(graph_obstacles, nodes[0], nodes[1], weight='travel_time',method='dijkstra')
    # shortest_path_coords = [(graph_obstacles.nodes[node]['x'], graph_obstacles.nodes[node]['y']) for node in shortest_path]
    # shortest_path_line = geometry.LineString(shortest_path_coords)

    # Version 2 - using taxicab library - cant use travel time, more accurate nearest node
    # route = tc.distance.shortest_path(graph_obstacles, start, end)

    if type == 'length':
        route = dist.shortest_path(graph_obstacles, start, end, type='length')
    elif type == 'time':
        route = dist.shortest_path(graph_obstacles, start, end, type='time')
    else:
        route = dist.shortest_path(graph_obstacles, start, end, type='length')

    nodes_coords = [(graph_obstacles.nodes[node]['x'], graph_obstacles.nodes[node]['y']) for node in route[1]]

    multi_line = geometry.MultiLineString([geometry.LineString(nodes_coords), route[2], route[3]])
    shortest_path_line = ops.linemerge(multi_line)

    geojson_geometry = json.dumps(shortest_path_line.__geo_interface__)

    route_length = int(sum(ox.routing.route_to_gdf(graph_obstacles, route[1], weight="length")["length"]))
    route_time = int(sum(ox.routing.route_to_gdf(graph_obstacles, route[1], weight="travel_time")["travel_time"]))


    
    return geojson_geometry, route_length, route_time

# shortest_path((48.1451, 17.1077),(48.1451, 17.1077), 50.0)