import pandas as pd
import tqdm.auto as tqdm

import json

from utils import *

df = load_data()

angles = np.linspace(0, np.pi/2, 100)

result = dict(
    type="FeatureCollection",
    features=[
        dict(
            type="Feature",
            geometry=dict(
                type="LineString",
                coordinates=np.array(
                    [
                        median_point(for_state(df, state), theta=a)
                        for a in tqdm.tqdm(angles, desc=state)
                    ]
                ).tolist(),
            ),
            properties=dict(name="CA"),
        )
        for state in tqdm.tqdm(set(df.STUSAB))
    ],
)

with open("median-centroid-line.geojson", "w") as f:
    json.dump(result, f)
