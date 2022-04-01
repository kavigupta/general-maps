from functools import partial
import itertools
import os
import subprocess

import tqdm


import numpy as np
import pandas as pd
import geopandas as gpd

import geopy.distance
import pyproj
from pyproj.crs import ProjectedCRS
from pyproj.crs.coordinate_operation import AzumuthalEquidistantConversion
from shapely.ops import transform
from shapely.geometry import Point


cities = {
    "New York": (40.71, -74),
    "Los Angeles": (34.1, -118.2),
    "Chicago": (41.8781, -87.6298),
    "Seattle": (47.61, -122.33),
    "Denver": (39.74, -104.99),
    "Miami": (25.7, -80.19),
    "Boston": (42.36, -71.06),
    "Minneapolis": (44.98, -93.27),
    "San Francisco": (37.77, -122.42),
    "McAllen": (26.2034, -98.2300),
}


def get_distances():
    csv = pd.read_csv("/home/kavi/temp/census_downloaded/usa.csv")
    distances = {city: distance((lon, lat), csv) for city, (lat, lon) in cities.items()}
    return csv, distances


def construct(pop):
    names = list(cities)
    csv, distances = get_distances()
    distance_ordering = {city: np.argsort(distances[city]) for city in cities}
    distances = {city: distances[city][distance_ordering[city]] for city in cities}
    pops = {city: np.cumsum(csv.POP100[distance_ordering[city]]) for city in cities}
    indices = {city: np.searchsorted(pops[city], pop) for city in cities}
    radiuses = {city: distances[city].iloc[indices[city]] for city in cities}
    circles = {
        city: geodesic_point_buffer(*reversed(cities[city]), radiuses[city])
        for city in cities
    }
    usa = gpd.read_file("shapefiles/cb_2018_us_nation_5m.shp").iloc[0].geometry
    intersections = {city: usa.intersection(circles[city]) for city in cities}
    intersections_frame = gpd.GeoDataFrame(
        pd.DataFrame({"name": names}),
        geometry=[intersections[x] for x in names],
    )
    intersections_frame = intersections_frame.set_crs("epsg:4326")
    frame = intersections_frame
    sub = list(ordered_subsets(frame)[-1])
    frame = frame[frame.name.apply(lambda x: x in sub)]
    return frame


def distance(pt, csv):
    # https://stackoverflow.com/a/19412565/1549476
    # approximate radius of earth in km
    R = 6373.0

    lon1, lat1 = np.radians(pt)

    lon2, lat2 = np.radians(csv.INTPTLON), np.radians(csv.INTPTLAT)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return c * R


def geodesic_point_buffer(lon, lat, km):
    # https://gis.stackexchange.com/a/384813
    proj_crs = ProjectedCRS(conversion=AzumuthalEquidistantConversion(lat, lon))
    proj_wgs84 = pyproj.Proj("EPSG:4326")
    Trans = pyproj.Transformer.from_proj(proj_crs, proj_wgs84, always_xy=True).transform

    return transform(Trans, Point(0, 0).buffer(km * 1000))


def powerset(iterable):
    s = list(iterable)
    return [
        set(x)
        for x in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def ordered_subsets(frame):
    self_joined = gpd.sjoin(frame, frame)
    graph_edges = [
        set(x)
        for x in zip(self_joined["name_left"], self_joined["name_right"])
        if x[0] != x[1]
    ]
    cities_order = list(cities)
    valid_sets = powerset(frame["name"])
    valid_sets = [x for x in valid_sets if all(len(x & g) != 2 for g in graph_edges)]
    return sorted(
        valid_sets, key=lambda x: (len(x), sorted([-cities_order.index(c) for c in x]))
    )


def export_countries(folder, countries):
    folder = f"/home/kavi/temp/out/{folder}"
    try:
        os.makedirs(folder)
    except FileExistsError:
        pass
    for name in tqdm.tqdm(countries):
        frame = construct(countries[name])
        frame.to_file("temp/temp.shp")
        subprocess.check_call(
            ["/usr/bin/python3", "export.py", "Main", name, f"{folder}/{name}.png"]
        )
