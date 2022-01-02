import pandas as pd

import tqdm.auto as tqdm


import json

from utils import *

df = load_data()

result = dict(
    type="FeatureCollection",
    features=[
        dict(
            type="Feature",
            geometry=dict(type="Point", coordinates=list(median_point(for_state(df, state)))),
            properties=dict(name=state)
        )
        for state in tqdm.tqdm(set(df.STUSAB))
    ],
)

with open("median-centroids.geojson", "w") as f:
    json.dump(result, f)
