import pandas as pd
import geopandas as gpd

vals = pd.read_csv("/home/kavi/temp/census_downloaded/usa.csv")
vals = vals[vals.POP100 > 0]
geo = gpd.points_from_xy(vals.INTPTLON, vals.INTPTLAT, crs="EPSG:4326")
frame = gpd.GeoDataFrame(vals[["POP100"]], geometry=geo)
frame.to_file("/home/kavi/temp/census_downloaded/usa.shp")
