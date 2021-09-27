import numpy as np
import matplotlib.pyplot as plt

from data import get_data
from density_prediction import Data, color


import electiondata as e
import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker")

import mapmaker.data

from mapmaker.stitch_map import generate_map
from mapmaker.data import data_by_year

data = get_data()

datas = [
    Data.of(data, "Standard Density", "Standard Density Metric"),
    Data.of(data, "Mean within 4km", "Alternate Density Metric [4km]"),
    Data.of(data, "Mean within 1km", "Alternate Density Metric [1km]"),
    Data.of(data, "Mean within 250m", "Alternate Density Metric [250m]"),
]
fig, axs = plt.subplots(2, 2, figsize=(10, 10), dpi=200)
for data, ax in zip(datas, axs.flatten()):
    data.plot(ax)
plt.savefig("metric.png", facecolor="white", bbox_inches="tight")
data_2020 = data_by_year()[2020]
for data in datas:
    title = data.title
    title = title.replace("Standard", "Std.")
    title = title.replace("Alternate", "Alt.")
    title = title.replace("Density", "Dens.")
    title = title.replace(" Metric", "")
    generate_map(
        data_2020,
        title=f"Prediction by {title}",
        out_path=f"{title} prediction.svg",
        dem_margin=data.map_prediction(data_2020.FIPS),
        turnout=data_2020.turnout,
        map_type="president",
        year=2020,
    )
    generate_map(
        data_2020,
        title=f"Residual by {title}",
        out_path=f"{title} residual.svg",
        dem_margin=data_2020.dem_margin - data.map_prediction(data_2020.FIPS),
        turnout=data_2020.turnout,
        map_type="president",
        year=2020,
    )
