import re
from collections import defaultdict
import subprocess

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
        if left is None or right is None:
            assert left is None and right is None
            continue
        insert += [
            rectangle(
                f"{db_name}_left", r / 2, r, x + dx - r / 2, y + dy - r / 2, left
            ),
            rectangle(f"{db_name}_left", r / 2, r, x + dx, y + dy - r / 2, right),
        ]
        colors.append(((left, right), int(row.Population)))
    return [x for x in insert if x is not None], colors


def load_countries(map_path):
    backmap_to_groups = get_backmap(map_path)
    by_country = defaultdict(list)
    paths, attributes = svg2paths(map_path)
    rec = None
    for path, attr in zip(paths, attributes):
        if attr["id"] == "mostcommoncolors":
            rec = path
        if "id" not in attr or attr["id"] not in backmap_to_groups:
            continue
        by_country[backmap_to_groups[attr["id"]]].append(path)
    assert rec is not None
    return by_country, rec


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
    ident = f'id="{ident}" ' if ident is not None else ""
    return (
        f'<rect {ident}width="{w}" height="{h}" x="{x}" y="{y}" style="fill:{color}"/>'
    )


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
    if name in {"ignore"}:
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


def sorted_colors(colors, key):
    pop_each = defaultdict(int)
    for color, pop in colors:
        if color == ("#888888",) * 2:
            continue
        pop_each[key(color)] += pop
    colors, pops = zip(*sorted(pop_each.items(), key=lambda x: -x[1]))
    pops = np.array(pops)
    pops = pops / pops.sum()
    return colors, pops


def color_rectangles(rec, xps, xpe, cs, ps):
    xmin, xmax, ymin, ymax = rec.bbox()
    xs, xe = xmin + (xmax - xmin) * xps, xmin + (xmax - xmin) * xpe
    ys, ye = ymin, ymax
    extra_rectangles = []
    for c, p, n in zip(cs, ps, np.cumsum([0, *ps])):
        w, h = xe - xs, (ye - ys) * p
        x, y = xs, ys + (ye - ys) * n
        extra_rectangles += [rectangle(None, w, h, x, y, c)]
    return extra_rectangles


def all_color_rectangles(rec, colors):
    overall = []
    # left
    cs, ps = sorted_colors(colors, key=lambda x: x[0])
    overall += color_rectangles(rec, 0, 0.2, cs, ps)

    cs, ps = sorted_colors(colors, key=lambda x: x)

    cls, crs = zip(*cs)
    overall += color_rectangles(rec, 0.3, 0.5, cls, ps)
    overall += color_rectangles(rec, 0.5, 0.7, crs, ps)

    # right
    cs, ps = sorted_colors(colors, key=lambda x: x[1])
    overall += color_rectangles(rec, 0.8, 1, cs, ps)
    return overall


def create_map(map_path, out_path):
    data = load_db()
    countries, rec = load_countries(map_path)

    rectangles, colors = get_rectangles(countries, data)

    with open(map_path) as f:
        svg = f.read().replace("fill:#123456", "fill:#123456;fill-opacity:0")
    *svg, close = svg.strip().split("\n")
    assert close == "</svg>"
    svg = svg + rectangles + all_color_rectangles(colors) + [close]
    with open(out_path, "w") as f:
        f.write("\n".join(svg))

    subprocess.check_call(
        ["inkscape", "--export-type=png", "--export-area-drawing", "out.svg"]
    )
