import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker")

import copy
import torch
import numpy as np

from mapmaker.stitch_map import *
from mapmaker.generate_image import *
from mapmaker.data import *

model = get_model(calibrated=False)
copied_model = copy.deepcopy(model)
with torch.no_grad():
    copied_model.adcm.dcm.partisanship_heads["(2012, True)"][-2] = 0.3
    copied_model.adcm.dcm.partisanship_heads["(2012, True)"] -= 0.14
p, t = copied_model.adcm.dcm.predict(
    2012, copied_model.features.features(2012), use_past_partisanship=True
)

for s in "West Virginia", "Kentucky":
    p[np.array(data_by_year()[2012].state == s)] += 0.2

generate_map(
    data_by_year()[2016],
    title="2016 if Bernie did everything right",
    out_path="out.svg",
    dem_margin=p,
    turnout=t,
    map_type="president",
    year=2016,
)
