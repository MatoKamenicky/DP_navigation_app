import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import re
from shapely.ops import unary_union, polygonize



#Import excel data + extract coordinates from links
def extract_coordinates(link):
    pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)'

    match = re.search(pattern, link)

    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        return longitude, latitude
    else:
        print("Coordinates not found")
        return None
        

excel_data_bridge = pd.read_excel("C:\GAK\_ING_studium\ING_3_sem\Diplomovka\data\SSÚC_mosty_podjazdy.xlsx", sheet_name="mosty")
excel_data_underpass = pd.read_excel("C:\GAK\_ING_studium\ING_3_sem\Diplomovka\data\SSÚC_mosty_podjazdy.xlsx", sheet_name="podjazdy")


coordinates_bridge = []
for i in range(len(excel_data_bridge['streetview'])):
    coordinates_bridge.append(extract_coordinates(excel_data_bridge['streetview'][i]))

coordinates_underpass = []
for i in range(len(excel_data_underpass['Streetview'])):
    coordinates_underpass.append(extract_coordinates(excel_data_underpass['Streetview'][i]))

excel_data_bridge.drop('streetview', axis=1, inplace=True)
excel_data_underpass.drop('Streetview', axis=1, inplace=True)


#Import excel data to database
engine = create_engine("postgresql://postgres:postgres@localhost:5432/DP_nav")  
excel_data_bridge.to_sql("bridge_obstacles", engine, if_exists='replace')
excel_data_underpass.to_sql("underpass_obstacles", engine, if_exists='replace')


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

for i in range(len(coordinates_underpass)):
    write2db(coordinates_underpass[i], 'underpass_obstacles',i)



