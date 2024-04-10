import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import re
from shapely.ops import unary_union, polygonize


excel_data_bridge = pd.read_excel("C:\GAK\_ING_studium\ING_3_sem\DP_navigation_app\data\SSUC_mosty_podjazdy_lonlat.xlsx", sheet_name="mosty")
coordinates_bridge = []
for record in excel_data_bridge.iterrows():
    coordinates_bridge.append((record[1]['lon'], record[1]['lat']))
# coordinates_bridge = (excel_data_bridge["lat"],excel_data_bridge["lon"])


#Import excel data to database
# engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav")  
# excel_data_bridge.to_sql("bridge_obstacles", engine, if_exists='replace')

# print(coordinates_bridge)

#Import coordinates as points to database
def write2db(input,table,index):
    connection = psycopg2.connect(user="postgres",
                                    password="postgres",
                                    host="localhost",
                                    port="5432",
                                    database="DP_nav")
    try:
        connection.autocommit = True
        cursor = connection.cursor()

        query = f"""
                UPDATE {table} 
                SET geom = (ST_GeomFromText('POINT(%s %s)'))
                WHERE index = %s;
                """
        cursor.execute(query, (input[0], input[1], index))
       
        count = cursor.rowcount
        print(count, "Record inserted successfully into table")

    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into table", error)
        
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

for i in range(len(coordinates_bridge)):
    write2db(coordinates_bridge[i], 'bridge_obstacles',i)








