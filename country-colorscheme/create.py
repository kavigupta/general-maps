import re
from collections import defaultdict

from shapely import geometry
import numpy as np
from svgpathtools import svg2paths
import pycountry
import pandas as pd

import gspread

from permacache import permacache, stable_hash


def get_color(c, side):
    if c == "":
        return None
    return {
        "black": "#000000",
        "red": "#cc0000",
        "pink": "#ff8888",
        "blue": "#0000cc",
        "light blue": "#4444ff",
        "green": "#00cc00",
        "orange": "#ff8800",
        "purple": "#8800cc",
        "magenta": "#ff00ff",
        "brown": "#884400",
        "cyan": "#00cccc",
        "yellow": "#dddd00",
        "light yellow": "#ffff88",
        "no left/right": "#888888",
        "one party": "#888888",
    }[c]


def load_db():
    gc = gspread.service_account()
    sh = gc.open("Country Colorschemes")
    data = sh.sheet1.get_all_values()
    data = pd.DataFrame(data[1:], columns=data[0])
    data.Country = data.Country.map(lambda x: x.split("[")[0].split("(")[0].strip())
    data = data.set_index("Country")
    return data


def get_rectangles(countries, data):
    colors = []
    adjustments = {
        "India": (0, 50),
        "China": (5, 8),
        "Malaysia": (-90, 0),
    }
    used = set()
    insert = []
    for original_name in countries:
        db_name = normalize_svg_name(original_name)
        if db_name is None:
            continue
        x, y = centroid(countries[original_name])
        if np.isnan(x):
            continue

        used.add(db_name)
        dx, dy = adjustments.get(db_name, (0, 0))
        row = data.loc[db_name]

        r = float(row.Size) * 10
        left, right = get_color(row.Left, "left"), get_color(row.Right, "right")
        insert += [
            rectangle(
                f"{db_name}_left", r / 2, r, x + dx - r / 2, y + dy - r / 2, left
            ),
            rectangle(f"{db_name}_left", r / 2, r, x + dx, y + dy - r / 2, right),
        ]
        colors.append((left, right, int(row.Population)))
    return [x for x in insert if x is not None], colors


def load_countries(map_path):
    backmap_to_groups = get_backmap(map_path)
    by_country = defaultdict(list)
    paths, attributes = svg2paths(map_path)
    for path, attr in zip(paths, attributes):
        if "id" not in attr or attr["id"] not in backmap_to_groups:
            continue
        by_country[backmap_to_groups[attr["id"]]].append(path)
    return by_country


def get_backmap(map_path):
    backmap_to_groups = {}
    with open(map_path) as f:
        svg = f.read()
    svg = svg.split("\n")
    append_to_prev = False
    overall = []
    for line in svg:
        if append_to_prev:
            overall[-1] += " " + line.lstrip()
        else:
            overall.append(line)
        if line.strip().endswith("<path") or line.strip().endswith("<g"):
            append_to_prev = True
        else:
            append_to_prev = False
    svg = overall
    current_groups = []
    for line in svg:
        group = re.search('<g id="([^"]+)"', line)
        if group is not None:
            current_groups.append(group.group(1))
            continue
        if "</g>" in line:
            current_groups.pop()
            continue
        path = re.search('<(path|circle) id="([^"]+)"', line)
        if path is not None and path.group(1) == "path":
            val = path.group(2)
            if not current_groups:
                backmap_to_groups[val] = val
            elif "tw" in current_groups + [val]:
                backmap_to_groups[val] = "tw"
            elif "hk" in current_groups + [val]:
                backmap_to_groups[val] = "hk"
            elif "xk" in current_groups + [val]:
                backmap_to_groups[val] = "xk"
            else:
                backmap_to_groups[val] = current_groups[0]
    return backmap_to_groups


def rectangle(ident, w, h, x, y, color):
    # y += 182.26204
    if color is None:
        return None
    return f'<rect id="{ident}" width="{w}" height="{h}" x="{x}" y="{y}" style="fill:{color}"/>'


def poly(path):
    ts = np.linspace(0, 1, 1000)
    coords = np.array([path.point(t) for t in ts])
    return geometry.Polygon(np.array([np.real(coords), np.imag(coords)]).T)


def best(paths):
    subpaths = [poly(x) for path in paths for x in path.continuous_subpaths()]
    if not subpaths:
        return np.nan, np.nan
    return max(subpaths, key=lambda x: x.area)


@permacache(
    "country-colorscheme/create/centroid",
    key_function=dict(paths=lambda x: stable_hash(str(x))),
)
def centroid(paths):
    [z] = best(paths).centroid.coords
    return z


def normalize_svg_name(name):
    if name in {"ocean"}:
        return None

    country = pycountry.countries.get(alpha_2=name.upper())
    if country is None:
        name = {"xk": "Kosovo"}[name]
    else:
        name = getattr(country, "common_name", country.name)
    name = name.split("(")[0].strip()
    name = {
        "Côte d'Ivoire": "Ivory Coast",
        "Congo, The Democratic Republic of the": "DR Congo",
        "Czechia": "Czech Republic",
        "Syrian Arab Republic": "Syria",
        "Russian Federation": "Russia",
        "Iran, Islamic Republic of": "Iran",
        "Korea, Republic of": "South Korea",
        "Palestine, State of": "Palestine",
        "Lao People's Democratic Republic": "Laos",
        "Korea, Democratic People's Republic of": "North Korea",
        "French Southern Territories": None,
        "Antarctica": None,
        "Timor-Leste": "East Timor",
        "South Georgia and the South Sandwich Islands": None,
        "Brunei Darussalam": "Brunei",
        "Cabo Verde": "Cape Verde",
        "Sao Tome and Principe": "São Tomé and Príncipe",
        "Virgin Islands, U.S.": "U.S. Virgin Islands",
        "Micronesia, Federated States of": "Micronesia",
        "British Indian Ocean Territory": None,
        "Virgin Islands, British": None,
        "Pitcairn": None,
        "Holy See": "Vatican City",
    }.get(name, name)
    return name
