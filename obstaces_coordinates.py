import osmnx as ox
import networkx as nx
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import re
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union, polygonize
from shapely.geometry import Polygon, LineString
import contextily as ctx


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

