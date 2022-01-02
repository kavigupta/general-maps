import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import tqdm.auto as tqdm

import wquantiles

import json
df = pd.read_csv("/home/kavi/temp/blocks_pop_centroid.csv")
df = df[df.POP100 > 0]
def mean_point(frame):
    lat = (frame.INTPTLAT * frame.POP100).mean() / frame.POP100.mean()
    lon = (frame.INTPTLON * frame.POP100).mean() / frame.POP100.mean()
    return lon, lat

def median_point(frame):
    lat = wquantiles.median(frame.INTPTLAT, frame.POP100)
    lon = wquantiles.median(frame.INTPTLON, frame.POP100)
    return lon, lat
result = dict(
    type="FeatureCollection",
    features=[
        dict(
            type="Feature",
            geometry=dict(type="Point", coordinates=list(median_point(df[df.STUSAB == state]))),
            properties=dict(name=state)
        )
        for state in tqdm.tqdm(set(df.STUSAB))
    ],
)

with open("median-centroids.geojson", "w") as f:
    json.dump(result, f)
