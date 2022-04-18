import pandas as pd
import numpy as np

import addfips
import gspread
import wquantiles

import electiondata as e

import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker")

from mapmaker.data import data_by_year


def load_election_data():
    election_data = data_by_year()
    ed0812 = (
        election_data[2012]
        .set_index("FIPS")
        .rename(columns={"past_pres_partisanship": 2008, "dem_margin": 2012})[
            [2008, 2012]
        ]
    )
    ed1620 = pd.DataFrame(
        {y: election_data[y].set_index("FIPS")["dem_margin"] for y in (2016, 2020)}
    )
    return pd.merge(ed0812, ed1620, left_index=True, right_index=True)


def load_densities(populations, election_data):
    gc = gspread.service_account()
    sh = gc.open("Alternate Population Density Metric v2")
    values = sh.worksheet("Counties").get_all_values()

    densities = pd.DataFrame(values[1:], columns=values[0])
    assert set(populations) == set(densities["Fips Code"])
    densities["population"] = densities["Fips Code"].apply(lambda x: populations[x])
    densities = densities[
        densities["Fips Code"].apply(lambda x: not x.startswith("72") and x != "15005")
    ]
    alaska_map = e.alaska.FIVE_REGIONS()
    densities["Fips Code"] = densities["Fips Code"].apply(
        lambda x: alaska_map.get(x, x)
    )
    assert set(densities["Fips Code"]) == set(election_data.index)
    densities = densities[["Fips Code", "Mean within 1km", "population"]].rename(
        columns={"Mean within 1km": "densities"}
    )
    densities.densities = densities.densities.apply(int)
    densities.densities *= densities.population
    densities = densities.groupby("Fips Code").sum().reset_index()
    densities.densities /= densities.population
    return densities


def load_populations():
    populations = pd.read_csv(
        "https://raw.githubusercontent.com/kavigupta/census-downloader/master/outputs/counties_census2020.csv"
    )
    populations.STUSAB = populations.STUSAB.apply(addfips.AddFIPS().get_state_fips)
    populations.COUNTY = populations.COUNTY.apply(lambda x: f"{int(x):03d}")
    populations["FIPS"] = populations.STUSAB + populations.COUNTY
    populations = dict(zip(populations.FIPS, populations.POP100))
    populations["02261"] = populations.pop("02063") + populations.pop("02066")
    return populations


def classify_americas(densities, election_data, n_quantiles):
    thresholds = [
        wquantiles.quantile(densities.densities, densities.population, x)
        for x in np.arange(0, 1.01, 1 / n_quantiles)
    ]
    thresholds[0] = -100
    masks = [
        (low < densities.densities) & (densities.densities <= high)
        for low, high in reversed(list(zip(thresholds, thresholds[1:])))
    ]
    masks = np.array(masks)
    assert (np.array(masks).sum(0) == 1).all()
    ordinal = np.argmax(masks, 0)
    raw_votes = np.array(election_data) * np.array(densities.population)[:, None]
    margins = (masks @ raw_votes) / (masks @ np.array(densities.population))[:, None]
    return margins, ordinal
