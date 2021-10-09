import numpy as np
import pandas as pd
import subprocess

import gspread

import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker")

from mapmaker.mapper import map_county_margins
from mapmaker.data import data_by_year
from mapmaker.colors import STANDARD_PROFILE
from mapmaker.stitch_map import remove_backgrounds


d2020 = data_by_year()[2020]

gc = gspread.service_account()
sh = gc.open("Actually Good National Divorce Map")
result = sh.sheet1.get_all_values()
result = pd.DataFrame(result[1:], columns=result[0])

classification = np.zeros(d2020.shape[0], dtype=np.int)
classification[result.Country == "United States of Canada"] = 1
classification[result.Country == "Jesusland"] = -1

margins = np.array([d2020.past_pres_partisanship, d2020.dem_margin])
total_votes = np.array([d2020.total_votes])

dem_votes = (margins + 1) / 2 * total_votes
gop_votes = total_votes - dem_votes

def statistics(classification):
    mc_gop = gop_votes[:, classification == 1].sum(1) / total_votes[
        :, classification == 1
    ].sum(1)
    jl_gop = gop_votes[:, classification == -1].sum(1) / total_votes[
        :, classification == -1
    ].sum(1)
    mcr = [f"{mc_gop[i]:.2%} R, {1 - mc_gop[i]:.2%} D" for i in range(2)]
    jlr = [f"{jl_gop[i]:.2%} R, {1 - jl_gop[i]:.2%} D" for i in range(2)]
    return mc_gop, jl_gop, mcr, jlr


mc_gop, jl_gop, mcr, jlr = statistics(classification)
mc_gop_i, jl_gop_i, _, _ = statistics(np.where(d2020.dem_margin > 0, 1, -1))

est_pop = d2020.CVAP / (d2020.CVAP.sum() / 329.5e6)

substitutions = dict(
    IR=f"{mc_gop_i[-1]:.0%}",
    ID=f"{1 - jl_gop_i[-1]:.0%}",
    MCP=f"{est_pop[classification == 1].sum()/1e6:.0f} million",
    JLP=f"{est_pop[classification == -1].sum()/1e6:.0f} million",
    MC16=mcr[0],
    MC20=mcr[1],
    JL16=jlr[0],
    JL20=jlr[1]
)

def create_map(margin, path):
    map_county_margins(
        d2020,
        dem_margin=margin,
        profile=STANDARD_PROFILE,
    ).write_image(path)

    remove_backgrounds(path)
    
create_map(classification * 0.25, "outputs/divorce.svg")
create_map(
    np.where(classification == 1, d2020.dem_margin, np.nan),
    "outputs/united-states-canada.svg",
)
create_map(
    np.where(classification == -1, d2020.dem_margin, np.nan), "outputs/jesusland.svg"
)

with open("template.svg") as f:
    result = f.read()
for k, v in substitutions.items():
    result = result.replace("$" + k, v)

with open("out.svg", "w") as f:
    f.write(result)
    
subprocess.check_call(['inkscape', '--export-type=png', 'out.svg', '-w', '4096'])
subprocess.check_call(['rm', 'out.svg'])