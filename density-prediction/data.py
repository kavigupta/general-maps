import gspread

import numpy as np
import pandas as pd

import electiondata as e
import addfips


def get_alt_density():
    gc = gspread.service_account()

    sh = gc.open("Alternate Population Density Metric v2")
    w = sh.worksheet("Counties")
    columns, *content = w.get_all_values()
    alt_density = pd.DataFrame(content, columns=columns)
    alt_density["state"] = alt_density.Counties.apply(lambda x: x.split(", ")[-1])
    alt_density["county"] = alt_density.Counties.apply(
        lambda x: ", ".join(x.split(", ")[:-1])
    )
    e.usa_county_to_fips(state_column="state").apply_to_df(
        alt_density, col_in="county", col_out="fips"
    )
    return alt_density.set_index("fips")


def get_election_data():
    election_2020 = pd.read_csv(
        "https://raw.githubusercontent.com/kavigupta/2024_bot/main/csvs/election_demographic_data%20-%202020.csv"
    )
    election_2020["fips"] = election_2020.FIPS.apply(lambda x: f"{x:05d}")
    return election_2020.set_index("fips")


def get_census_data():
    census_2020 = pd.read_csv(
        "https://raw.githubusercontent.com/kavigupta/census-downloader/master/outputs/counties_census2020.csv"
    )
    af = addfips.AddFIPS()
    census_2020["fips"] = census_2020.apply(
        lambda x: af.get_state_fips(x.STUSAB) + f"{int(x.COUNTY):03d}", axis=1
    )
    census_2020 = census_2020[["fips", "POP100", "AREALAND"]]
    census_2020.fips = census_2020.fips.apply(
        lambda x: "02261" if x in {"02063", "02066"} else x
    )
    census_2020 = e.Aggregator(
        grouped_columns=["fips"],
        aggregation_functions={"POP100": np.sum, "AREALAND": np.sum},
    )(census_2020)
    return census_2020.set_index("fips")


def get_data():
    alt_density = get_alt_density()
    election_data = get_election_data()
    census_data = get_census_data()
    combined = alt_density.join(election_data[["dem_margin", "CVAP"]]).join(
        census_data[["AREALAND", "POP100"]]
    )
    assert (
        combined[
            np.isnan(combined.dem_margin)
            & (combined.state != "PR")
            & (combined.county != "Kalawao")
        ].size
        == 0
    )
    combined = combined[~np.isnan(combined.dem_margin)]

    combined["Standard Density"] = combined.POP100 / (census_data.AREALAND / 1e6)
    return combined
