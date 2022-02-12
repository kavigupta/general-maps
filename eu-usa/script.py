import os
import re
import tempfile
import colorsys

import pandas as pd
import numpy as np

import apportionpy.apportionment
import svgpathtools
import gspread

def color(hue, sat):
    return "#" + ("%02x" * 3) % tuple(int(x * 255) for x in colorsys.hsv_to_rgb(hue, sat, 1))

def full_ramp(h2, h1):
    return [
        color(h1, 0.6),
        -7,
        color(h1, 0.45),
        -3,
        color(h1, 0.3),
        -1,
        color(h1, 0.15),
        0,
        color(h2, 0.15),
        1,
        color(h2, 0.3),
        3,
        color(h2, 0.45),
        7,
        color(h2, 0.6),
    ]

color_ramps = dict(
    G=full_ramp(2/3, 0),
    P=full_ramp(1/3, 2/3),
)

party_dict = dict(
    G={
        "Green": (100, 100),
        "Left": (100, 100),
        "Center Left": (100, 100),
        "Center": (65 - 35, 100),
        "Center Right": (25 - 75, 100),
        "Right": (0 - 100, 100),
    },
    P={
        "Green": (100, 75),
        "Left": (80 - 20, 100),
        "Center Left": (40 - 60, 100),
        "Center": (20 - 80, 50),
        "Center Right": (0 - 100, 10),
    },
)

parties = dict(
    G=lambda y: ["D", "R"], P=lambda y: ["Sanders", "Clinton" if y == "16" else "Biden"]
)


def read_data():
    gc = gspread.service_account()
    sh = gc.open("Euro 2020 presidential election")
    sh = sh.sheet1
    cols, *data = sh.get_all_values()
    df = pd.DataFrame(data, columns=cols).set_index("State")
    with tempfile.NamedTemporaryFile() as f:
        df.to_csv(f.name)
        return pd.read_csv(f.name).set_index("State").fillna(0)


def get_for_year(df, year, distro):
    party_names = ["Green", "Left", "Center Left", "Center", "Center Right", "Right"]
    result = np.array(df[[f"{year} {col}" for col in party_names]])
    partisa = np.array([distro.get(name, (0, 0))[0] for name in party_names])
    turnout = np.array([distro.get(name, (0, 0))[1] for name in party_names])
    result *= turnout
    result = result / result.sum(1)[:, None]
    result = result @ partisa
    return result


def produce_map(colors, index, out_path):
    colors = dict(zip(index, colors))
    paths, attrs, svg_attrs = svgpathtools.svg2paths2("basemap.svg")
    for path, attr in zip(paths, attrs):
        if not attr["id"] in colors:
            continue
        c = colors[attr["id"]]
        attr["style"] = re.sub(r"fill:#......;", f"fill:{c};", attr["style"])
    svgpathtools.wsvg(
        paths, attributes=attrs, svg_attributes=svg_attrs, filename=out_path
    )


def get_color(colors, amount):
    bins = [*colors[1::2], float("inf")]
    colors = colors[::2]

    for k, c in zip(bins, colors):
        if amount < k:
            return c


def compute_stats(votes, df, parties):

    render_pv_fn = lambda pv: f"{parties[int(pv < 0)]}+{abs(pv):.2f}%"

    seats_each, *_ = apportionpy.apportionment.calculate_huntington_hill(
        435, list(df.Population)
    )
    ec_each = [x + 2 for x in seats_each]
    pv = (votes * df["Population"]).sum() / df["Population"].sum()
    render_pv = render_pv_fn(pv)
    ec_first = sum((votes > 0) * ec_each)
    ec = [ec_first, sum(ec_each) - ec_first]
    assert all(ec)
    ec = ", ".join([f"{e} {p}" for e, p in zip(ec, parties)])

    ec_first = 0
    for idx in np.argsort(-votes):
        ec_first += ec_each[idx]
        if ec_first > sum(ec_each) / 2:
            tipping_point = f"{df.index[idx]} {render_pv_fn(votes[idx])}"
            break

    return dict(V=render_pv, C=ec, T=tipping_point)


def generate_map(df, year, typ):
    votes = get_for_year(df, year, party_dict[typ])
    stats = compute_stats(votes, df, parties[typ](year))
    produce_map(
        colors=[get_color(color_ramps[typ], x) for x in votes],
        index=df.index,
        out_path=f"output-images/{year}{typ}.svg",
    )
    return {f"${k}{typ}{year}": v for k, v in stats.items()}

def main():
    df = read_data()
    overall = {}
    for y in "16", "20":
        for t in "PG":
            overall.update(generate_map(df, y, t))
    with open("layout.svg") as f:
        svg = f.read()
    for k, v in overall.items():
        svg = svg.replace(k, v)
    with open("out.svg", "w") as f:
        f.write(svg)
    os.system("inkscape --export-type=png out.svg -h 4096")

if __name__ == "__main__":
    main()