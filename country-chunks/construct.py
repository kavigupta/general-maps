from functools import lru_cache

import subprocess
import numpy as np
import pandas as pd
import geopandas as gpd
import tqdm.auto as tqdm
import shapely

import wquantiles
from permacache import permacache

terr = {"78", "72", "69", "66", "60", "11"}


def usa():
    csv = pd.read_csv("/home/kavi/temp/census_downloaded/usa.csv")
    csv = csv[csv.INTPTLON < 0].copy()
    csv = csv[csv.GEOID.apply(lambda x: x.split("US")[1][:2] not in terr)]
    return csv


@permacache("construct/shapefile")
def shapefile():
    sh = gpd.read_file("shapefiles/cb_2018_us_state_500k.shp")
    sh = sh[sh.GEOID.apply(lambda x: x not in terr)]
    sh = shapely.ops.unary_union(list(sh.geometry))
    return sh.intersection(shapely.geometry.box(-180, 0, 0, 90))


slab_maker = dict(
    y=lambda start, end: shapely.geometry.box(-1000, start, 1000, end),
    x=lambda start, end: shapely.geometry.box(start, -1000, end, 1000),
)

bounds = dict(y=(-90, 90), x=(-180, 180))

key_cols = dict(y="INTPTLAT", x="INTPTLON")


def split_slabs(*, universe, table, direction, split_points):
    keys = table[key_cols[direction]]
    start, end = bounds[direction]
    weights = table.POP100
    slab_maker = dict(
        y=lambda start, end: shapely.geometry.box(-1000, start, 1000, end),
        x=lambda start, end: shapely.geometry.box(start, -1000, end, 1000),
    )
    splits = [wquantiles.quantile(keys, weights, q) for q in split_points]
    splits = [start, *splits, end]
    slabs = [
        slab_maker[direction](a, b).intersection(universe)
        for a, b in zip(splits, splits[1:])
    ]
    tables = [
        table[(keys >= start) & (keys < end)] for start, end in zip(splits, splits[1:])
    ]
    return dict(slabs=slabs, tables=tables)


def table_of_slabs(*, universe, table, rows, columns):
    sh = shapefile()
    chunks = []
    counts = []
    result = split_slabs(
        universe=universe,
        table=table,
        num_splits=np.linspace(0, 1, rows + 1)[1:-1],
        direction="y",
    )
    for slab, table in zip(result["slabs"], result["tables"]):
        row = split_slabs(
            universe=slab,
            table=table,
            num_splits=np.linspace(0, 1, columns + 1)[1:-1],
            direction="x",
        )
        for chunk, t in zip(row["slabs"], row["tables"]):
            chunks.append(chunk)
            counts.append(t.sum().POP100)
    chunks = [chunk.intersection(sh) for chunk in chunks]
    return chunks


def res_up(chunk):
    if isinstance(chunk, shapely.geometry.MultiPolygon):
        return shapely.geometry.MultiPolygon([res_up(z) for z in chunk])
    ext = chunk.exterior
    assert isinstance(ext, shapely.geometry.polygon.LinearRing)
    ext = type(ext)(
        [ext.interpolate(i, normalized=True) for i in np.linspace(0, 1, 1000)]
    )
    return shapely.geometry.Polygon(ext)


def squariness(geo):
    xmin, ymin, xmax, ymax = geo.bounds
    w, h = xmax - xmin, ymax - ymin
    return min(w, h) / max(w, h)


def min_squariness(s):
    return min(squariness(x) for x in s)


def split_into(*, rng, universe, amount, table, **kwargs):
    if amount == 1:
        yield (universe, table)
        return
    slab_sets = []
    table_sets = []
    belows = []
    for _ in range(kwargs["repeats"]):
        below = rng.choice(list(range(1, amount)))
        direction = rng.choice(list("xy"))
        res = split_slabs(
            universe=universe,
            table=table,
            direction=direction,
            split_points=[below / amount],
        )
        slab_sets.append(res["slabs"])
        table_sets.append(res["tables"])
        belows.append(below)
    idx = max(range(len(slab_sets)), key=lambda i: min_squariness(slab_sets[i]))
    below = belows[idx]
    b, a = slab_sets[idx]
    bt, at = table_sets[idx]
    yield from split_into(rng=rng, universe=b, amount=below, table=bt, **kwargs)
    yield from split_into(
        rng=rng, universe=a, amount=amount - below, table=at, **kwargs
    )


@lru_cache(None)
def centroids():
    return pd.read_csv("/home/kavi/full-usa-precinct-map/out/centroids.csv")


def margin(chunk):
    res = centroids()
    minx, miny, maxx, maxy = chunk.bounds
    votes = res[(minx < res.x) & (res.x < maxx) & (miny < res.y) & (res.y < maxy)][
        ["R", "D", "O"]
    ].sum()
    result = (votes.D - votes.R) / votes.sum()
    return 0 if np.isnan(result) else result

@permacache("construct/produce_map")
def produce_map(amount, seed):
    us = usa()
    universe = shapefile()

    chunks, tables = zip(
        *tqdm.tqdm(
            split_into(
                rng=np.random.RandomState(seed),
                universe=universe,
                amount=amount,
                table=us,
                repeats=10,
            )
        )
    )
    pops = [x.POP100.sum() for x in tables]
    np.max(pops) / np.min(pops)
    margins = [margin(c) for c in chunks]
    chunks = [res_up(chunk) for chunk in tqdm.tqdm(chunks)]
    frame = gpd.GeoDataFrame(
        {"id": [x + 1 for x in range(len(chunks))], "margin": margins}, geometry=chunks
    )
    return frame


def export_map(amount, plan):
    frame = produce_map(amount, plan)
    plan = str(plan)
    margins = np.array(frame.margin)
    biden, trump = (np.array(margins) > 0).sum(), (np.array(margins) < 0).sum()
    median_district = 100 * np.median(margins)
    partisanship = (
        f"D+{median_district:.2f}"
        if median_district > 0
        else f"R+{-median_district:.2f}"
    )
    layout = dict(partisanship="Partisanship", atlas="Main")
    frame.to_file("temp/temp.shp")
    with open(f"out/{amount}_{plan}.geojson", "w") as f:
        f.write(frame.to_json())
    for typ in layout:
        print(amount, plan, typ)
        subprocess.check_call(
            [
                "/usr/bin/python3",
                "export.py",
                layout[typ],
                f"{margins.shape[0]} districts, {biden} Biden - {trump} Trump, median: {partisanship}",
                f"{plan}",
                f"out/{typ}_{amount}_{plan}.png",
            ]
        )


def main():
    for plan in range(1, 5):
        export_map(435 if plan % 2 == 1 else 1000, plan)
        


if __name__ == "__main__":
    main()
