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
from shapely.geometry import LineString
import json
ox.config(use_cache=True, log_console=True)



def connect_to_postgres(host, dbname, user, password):
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    return conn

def get_obstacles(type,conn,everything=False):
    if everything == True:
        cursor = conn.cursor()
        cursor.execute(f"""SELECT * FROM {type}""")
        obstacles  = cursor.fetchall()
        cursor.close()

        return obstacles
    
    elif everything == False:
        conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
        cursor = conn.cursor()
        cursor.execute(f"""SELECT index, ST_AsText(geom),nearest_edge_u,nearest_edge_v,nazov_objektu FROM {type}""")
        obstacles  = cursor.fetchall()
        cursor.close()

        return obstacles 

#New way to save road network to DB - using geodataframe
def road_network_to_db_gdf(place_name,table):
    graph  = ox.graph_from_place(place_name, network_type="drive", simplify=True)

    engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav") 

    node_gdf, edge_gdf, weight = mm.nx_to_gdf(graph, spatial_weights=True)
    print(weight)
    node_gdf.to_postgis(table + "_nodes", engine, if_exists='replace', index=True, index_label='id', schema='public', dtype=None)
    edge_gdf.to_postgis(table + "_edges", engine, if_exists='replace', index=True, index_label='id', schema='public', dtype=None)


#road_network_to_db_gdf("Bratislava, Slovakia","road_network_BA_gdf")

#function to import road network from postgres to python using geodataframe
def graph_from_db_gdf(table):
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav") 

    nodes_table = table + "_nodes"
    edges_table = table + "_edges"
    sql_nodes = f"""SELECT node_id, lon, lat, ST_AsBinary(geometry)
                    FROM {nodes_table}"""
    
    sql_edges = f"""SELECT node_start, node_end, ST_AsBinary(geometry)
                    FROM {edges_table}"""
    
    #nodes_gdf = gpd.GeoDataFrame.from_postgis(sql_nodes, engine, geom_col='geometry')
    edges_gdf = gpd.GeoDataFrame.from_postgis(sql_edges, engine, geom_col='geometry')

    graph = mm.gdf_to_nx(edges_gdf, approach='primal')

    return graph
    
#function to import road network from postgres to python using as text for geometry
def graph_from_db_new(table, conn):
    cur = conn.cursor()

    graph = nx.MultiDiGraph()

    #add nodes to the graph
    nodes_table = table + "_nodes" 
    cur.execute(sql.SQL(f"""
        SELECT node_id, lon, lat, ST_AsText(geometry)
        FROM {nodes_table}
    """))

    for row in cur.fetchall():
        node_id, lon, lat, geometry = row
        node_geometry = loads(geometry)
        if node_geometry is not None:
            lon, lat = node_geometry.x, node_geometry.y
            graph.add_node(node_id, x=lon, y=lat, geometry=node_geometry)

    #add edges to the graph
    edges_table = table + "_edges" 
    cur.execute(sql.SQL(f"""
        SELECT source, target, ST_AsText(geometry)
        FROM {edges_table}
    """))

    for row in cur.fetchall():
        source, target, geometry = row
        edge_geometry = loads(geometry)
        if edge_geometry is not None:
            graph.add_edge(source, target, geometry=edge_geometry)

    cur.close()

    graph.graph["crs"] = "EPSG:4326"

    return graph


#---------------------------------OLD WAY---------------------------------#
    
#function to save road network to DB using postgis and geometry data type
def road_network_to_db(place_name,table):
    graph  = ox.graph_from_place(place_name, network_type="drive", simplify=True)
    
    #save to DB
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    cur = conn.cursor()

    edges_table = table + "_edges" 
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {edges_table} (
            id SERIAL PRIMARY KEY,
            source BIGINT ,
            target BIGINT ,
            geometry GEOMETRY(LineString, 4326)
        )
    """)

    nodes_table = table + "_nodes" 
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {nodes_table} (
            id SERIAL PRIMARY KEY,
            node_id BIGINT,
            lon DOUBLE PRECISION,
            lat DOUBLE PRECISION,
            geometry GEOMETRY(Point, 4326)
        )
    """)

    # Insert edges into the database
    for u, v, data in graph.edges(data=True):
        if 'geometry' in data:
            geometry = data['geometry']
            cur.execute(sql.SQL("""
                INSERT INTO road_network_BA_edges (source, target, geometry)
                VALUES (%s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326))
            """), (u, v, geometry.wkt))

    # Insert nodes into the database
    for node, data in graph.nodes(data=True):
        cur.execute(sql.SQL("""
            INSERT INTO road_network_BA_nodes (node_id, lon, lat, geometry)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """), (node, data['x'], data['y'], data['x'], data['y']))



    conn.commit()
    cur.close()
    conn.close()

def graph_from_db(table, conn, include_nodes=False):
    cur = conn.cursor()

    graph = nx.MultiDiGraph()

    # if include_nodes is True, add nodes to the graph
    if include_nodes:
        nodes_table = table + "_nodes" 
        cur.execute(sql.SQL(f"""
            SELECT node_id, lon, lat, ST_AsBinary(geometry)
            FROM {nodes_table}
        """))

        for row in cur.fetchall():
            node_id, lon, lat, geometry_wkb = row
            if geometry_wkb:
                geometry = wkb.loads(geometry_wkb, hex=True)
                graph.add_node(node_id, lon=lon, lat=lat, geometry=geometry)

    # add edges to the graph
    edges_table = table + "_edges" 
    cur.execute(sql.SQL(f"""
        SELECT source, target, ST_AsBinary(geometry)
        FROM {edges_table}
    """))

    for row in cur.fetchall():
        source, target, geometry_wkb = row
        if geometry_wkb:
            geometry = wkb.loads(geometry_wkb, hex=True)
            graph.add_edge(source, target, geometry=geometry)

    cur.close()

    graph.graph["crs"] = "EPSG:4326"

    return graph

#---------------------------------OLD WAY---------------------------------#


def update_nearest_edge(conn, point_id, u, v):
    cur = conn.cursor()
    cur.execute("UPDATE bridge_obstacles SET nearest_edge_u = %s, nearest_edge_v = %s WHERE index = %s", (u, v, point_id))
    conn.commit()
    cur.close()

def obstacles_nearest_edge():
    #get graph from DB to variable graph
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

    graph = graph_from_db_new("road_network_ba",conn)

    bridge_obstacles = get_obstacles('bridge_obstacles',conn)

    for record in bridge_obstacles:
        point_id, point_text, u, v,name = record
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
#obstacles_nearest_edge()


#function for export shortest path to geopackage - for qgis visualisation
def export_gpkg(graph, shortest_path):
    nodes_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=False)

    shortest_path_nodes_gdf = nodes_gdf.loc[shortest_path]

    nodes_gdf.to_file('graph_data.gpkg', layer='nodes', driver='GPKG')
    shortest_path_nodes_gdf.to_file('shortest_path.gpkg', layer='shortest_path', driver='GPKG')



#function to find the shortest path with obstacles, using graph from postgres DB - for now only plot the graph
def shortest_path(start,end):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    #graph = graph_from_db_new("road_network_ba",conn)
    #graph_obstacles = graph_from_db_new("road_network_ba",conn)
    bridge_obstacles = get_obstacles('bridge_obstacles',conn,)
    obstacles_edge = []

    graph_obstacles  = ox.graph_from_place("Bratislava, Slovakia", network_type="drive", simplify=True)

    
   
    for record in bridge_obstacles:
        edge_record = (record[2],record[3])
        if edge_record[0] is not None and edge_record[1] is not None:
            obstacles_edge.append(edge_record)
    
    graph_obstacles.remove_edges_from(obstacles_edge) 
    
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    ox.plot_graph(graph, ax=ax1, node_color='w', edge_color='r', edge_linewidth=1, node_size=0, show=False)
    ax1.set_title('Graph')

    ox.plot_graph(graph_obstacles, ax=ax2, node_color='w', edge_color='r', edge_linewidth=1, node_size=0, show=False)
    ax2.set_title('Graph obstacles')

    plt.show()
    """
    
    #nearest node to the points of origin and destination
    node_Xo = ox.distance.nearest_nodes(graph_obstacles, start[1], start[0])
    node_Xd = ox.distance.nearest_nodes(graph_obstacles, end[1], end[0])
    
    nodes = [node_Xo, node_Xd]

    #Shortest path calculation
    shortest_path = nx.shortest_path(graph_obstacles, nodes[0], nodes[1], weight='length',method='dijkstra')


    nodes_coords = [(graph_obstacles.nodes[node]['y'], graph_obstacles.nodes[node]['x']) for node in shortest_path]

    shortest_path_line = LineString(nodes_coords)

    geojson_geometry = json.dumps(shortest_path_line.__geo_interface__)
    """
    #Plot shortest path
    fig, ax = ox.plot_graph_route(graph_obstacles, shortest_path, route_color='r', route_linewidth=4, node_size=0)
    plt.show()
    """
    
    # route_map = ox.plot_route_folium(graph_obstacles, shortest_path, tiles = 'openstreetmap', fit_bounds = True )
    return geojson_geometry

"""
Xo = 48.14225666993606, 17.119759122997106
Xd = 48.147988762031815, 17.144489719694707

shortest_path(Xo,Xd)
"""


