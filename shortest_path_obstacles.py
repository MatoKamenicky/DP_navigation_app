import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import psycopg2
from psycopg2 import sql
from shapely.wkt import loads

def connect_to_postgres(host, dbname, user, password):
    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    return conn

def get_obstacles(type,conn):
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    cursor = conn.cursor()
    cursor.execute(f"""SELECT index, ST_AsText(geom) FROM {type}""")
    obstacles  = cursor.fetchall()
    cursor.close()
    return obstacles 

def road_network_to_db(place_name,table):
    graph  = ox.graph_from_place(place_name, network_type="drive", simplify=True)
    
    #save to DB
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')
    cur = conn.cursor()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            source BIGINT ,
            target BIGINT ,
            geometry GEOMETRY(LineString, 4326)
        )
    """)

    for u, v, data in graph.edges(data=True):
        if 'geometry' in data:
            geometry = data['geometry']
            cur.execute(sql.SQL("""
                INSERT INTO road_network_BA (source, target, geometry)
                VALUES (%s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326))
            """), (u, v, geometry.wkt))

    conn.commit()
    cur.close()
    conn.close()


#road_network_to_db("Bratislava, Slovakia", "road_network_BA")

def graph_from_db(table,conn):
    cur = conn.cursor()

    cur.execute(sql.SQL(f"""
        SELECT source, target, ST_AsText(geometry) 
        FROM {table}
    """))   
    
    graph = nx.MultiDiGraph()

    for row in cur.fetchall():
        source, target, geometry_text = row
        geometry = loads(geometry_text)
        graph.add_edge(source, target, geometry=geometry) 

    cur.close()
    graph.graph["crs"] = "EPSG:4326"

    return graph

def update_nearest_edge(conn, point_id, u, v):
    cur = conn.cursor()
    cur.execute("UPDATE bridge_obstacles SET nearest_edge_u = %s, nearest_edge_v = %s WHERE index = %s", (u, v, point_id))
    conn.commit()
    cur.close()

def obstacles_nearest_edge():
    #get graph from DB to variable graph
    conn = connect_to_postgres(host='localhost', dbname='DP_nav', user='postgres', password='postgres')

    graph = graph_from_db("road_network_BA",conn)

    bridge_obstacles = get_obstacles('bridge_obstacles',conn)

    for record in bridge_obstacles:
        #point_id = record[0]
        #point_text = record[1]
        point_id, point_text = record
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
obstacles_nearest_edge()

  
