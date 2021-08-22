import electiondata as e
from electiondata.examples.canonical_2018_general import Canonical2018General
import pandas as pd
import numpy as np

import re
import os

r2010 = pd.read_html(
    "https://en.wikipedia.org/wiki/2010_United_States_Senate_election_in_California"
)
[r2010] = [x for x in r2010 if "Alameda" in str(x)]
r2010["state"] = "CA"
e.usa_county_to_fips(
    alaska_handler=e.alaska.AT_LARGE, state_column="state"
).apply_to_df(r2010, "County", "FIPS")
r2010 = r2010.set_index("FIPS")

margin_2010 = r2010.Boxer.apply(lambda x: float(x[:-1])) - r2010.Fiorina.apply(
    lambda x: float(x[:-1])
)
swing = 100 - margin_2010
overall_swing = ((r2010["Votes"] + r2010["Votes.2"]) * swing).sum() / (
    r2010["Votes"] + r2010["Votes.2"]
).sum()


def map(sw, path, subname):
    with open("Blank_California_Map.svg") as f:
        svg = f.read()
    svg = svg.replace('"\n', '"')
    svg = svg.replace("$subname", subname)
    s = sw
    svg = svg.replace("$SWING", f"D+{overall_swing/100:.0%}")
    #     svg = svg.replace("$No", f"{s/2 + .5:.2%}")
    result = []
    for line in svg.split("\n"):
        mat = re.search(r'id="_x3([01])_([0-9][0-9]).*".*fill="#CCCCCC"', line)
        if not mat:
            result.append(line)
            continue
        row = sw.loc["06" + "".join(mat.groups())]
        margin = row / 200
        abs_margin = abs(margin)
        amount_other = int(0xFF * (1 - abs_margin))
        rgb = (amount_other, amount_other, 255)
        if margin < 0:
            rgb = rgb[::-1]
        color = "%02X%02X%02X" % rgb
        result.append(line.replace("CCCCCC", color))
    with open(path, "w") as f:
        f.write("\n".join(result))
    os.system('inkscape --export-type="png" ' + path)


map(swing, "2016_swing.svg", "2016 actual")

print("Overall swing", 100 - overall_swing)
