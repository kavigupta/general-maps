import urllib
import bs4 as bs
import time
from types import SimpleNamespace

from permacache import permacache
import tqdm.auto as tqdm

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import wikipediaapi
from sklearn.neighbors import NearestNeighbors
import addfips
import electiondata as e

from pytrends.request import TrendReq

url = "https://en.wikipedia.org/wiki/List_of_United_States_counties_and_county_equivalents"


def data_by_county():
    #     p = wiki_wiki.page("List_of_United_States_counties_and_county_equivalents")
    with urllib.request.urlopen(url) as f:
        soup = bs.BeautifulSoup(f, "lxml")
        parsed_table = soup.find_all("table")[0]
        data = []
        for row in parsed_table.find_all("tr"):
            cells = list(row.find_all("td"))
            if not cells:
                continue
            cell = cells[0]
            data.append((cell.a["href"], cell.a["title"]))
    #     data = pd.DataFrame(data[1:])
    lengths = []
    for path, _ in tqdm.tqdm(data):
        title = path.split("/")[-1]
        title = urllib.parse.unquote(title)
        x = download_page(title)
        lengths.append(len(x.split()))
        if lengths[-1] < 100:
            print(path)
            print(x)
    df = pd.DataFrame(
        [[*county_state(x[1]), l] for x, l in zip(data, lengths)],
        columns=["county", "state", "wordcount"],
    )
    df = df[df.state != "REMOVE"]
    norm = e.usa_county_to_fips(state_column="state")
    norm.rewrite["hoonah–angoon census area"] = "hoonah-angoon census area"
    norm.rewrite[
        "prince of wales – hyder census area"
    ] = "prince of wales-hyder census area"
    norm.rewrite["yukon–koyukuk census area"] = "yukon-koyukuk census area"
    norm.rewrite["new orleans"] = "orleans"
    norm.rewrite["saint thomas"] = "saint thomas island"
    norm.rewrite["baltimore"] = "baltimore city"
    norm.rewrite["st. louis"] = "st. louis city"
    norm.rewrite["franklin"] = "franklin city"
    norm.rewrite["richmond"] = "richmond city"
    norm.rewrite["fairfax"] = "fairfax city"
    norm.rewrite["roanoke"] = "roanoke city"
    norm.rewrite["saint john"] = "saint john island"
    norm.rewrite["coös county"] = "coos county"
    norm.rewrite["chugach census area"] = "ERROR"
    norm.apply_to_df(df, "county", "fips", var_name="norm")
    df.loc[df.county == "Chugach Census Area", "fips"] = "02063"
    df["google_discourse"] = df.apply(
        lambda row: trend_state(row.county, row.state), axis=1
    ).apply(google_discourse)
    df = population().merge(df, on="fips")
    return df


@permacache("county-importance-wikipedia/download_page/2")
def download_page(name):
    print(name)
    time.sleep(0.01)
    wiki_wiki = wikipediaapi.Wikipedia("en")
    return wiki_wiki.page(name).text


def county_state(s):
    if s.endswith(" (page does not exist)"):
        s = s[: -len(" (page does not exist)")]
    if ", " in s:
        return s.split(", ")
    if s in [
        "Rose Atoll",
        "Guam",
        "Swains Island",
        "Northern Islands Municipality",
        "Rota (island)",
        "Saipan",
        "Tinian",
        "Bajo Nuevo Bank",
        "Baker Island",
        "Howland Island",
        "Jarvis Island",
        "Johnston Atoll",
        "Kingman Reef",
        "Midway Atoll",
        "Navassa Island",
        "Palmyra Atoll",
        "Serranilla Bank",
        "Wake Island",
        "Saint Croix",
    ]:
        return "REMOVE", "REMOVE"
    known = {
        "San Francisco": "California",
        "Denver": "Colorado",
        "District of Columbia": "District of Columbia",
        "New Orleans": "Louisiana",
        "Baltimore": "Maryland",
        "St. Louis": "Missouri",
        "The Bronx": "New York",
        "Brooklyn": "New York",
        "Queens": "New York",
        "Staten Island": "New York",
    }
    if s in known:
        return s, known[s]
    print(s)
    1 / 0


def trend_state(county, state):
    default = county + " " + state
    if county.endswith("County"):
        return default
    if county.endswith("Borough"):
        return default
    if county.endswith("Census Area"):
        return default
    if county.endswith("District"):
        return default
    if county.endswith("Parish"):
        return default
    if state == "Alaska":
        return county + " Borough " + state
    if state in {"California", "Colorado", "District of Columbia", "Massachusetts"}:
        return county + " County " + state
    if state == "Louisiana":
        return county + " Parish " + state
    if state in {"Maryland", "Missouri", "Virginia", "Nevada"}:
        return county.replace(" City", "") + " Independent City " + state
    if state == "New York":
        return county + " Borough " + state
    if state == "Puerto Rico":
        return county + " Municipo " + state
    if state == "U.S. Virgin Islands":
        return county + " Island " + state
    print(county, state)
    1 / 0


def google_discourse(x):
    z = get_trends(x)
    if z is None:
        return 0
    return z.sum()


def population():
    pop = pd.read_csv(
        "https://raw.githubusercontent.com/kavigupta/census-downloader/master/outputs/counties_census2020.csv"
    )
    pop = pop[["STUSAB", "COUNTY", "POP100"]]
    pop["fips"] = pop.STUSAB.apply(addfips.AddFIPS().get_state_fips) + pop.COUNTY.apply(
        lambda x: f"{int(x):03d}"
    )
    return pop


def knn_predict(knn, x, ys, weight, strategy):
    _, idxs = knn.radius_neighbors(np.array([x])[:, None])
    idxs = idxs[0]
    if idxs.size == 0:
        return np.nan
    return (ys[idxs] * weight[idxs]).sum() / weight[idxs].sum()


def compute_overperformance(overall, stat_col, name, name_full):
    overall = overall.copy()

    pop = np.array(overall.POP100)
    log_pop = np.log(pop)
    stat = np.array(overall[stat_col])
    knn = NearestNeighbors(radius=1).fit(log_pop[:, None])

    prediction = np.array([knn_predict(knn, x, stat, pop, "mean") for x in log_pop])
    plt.figure(dpi=200)
    plt.scatter(log_pop, stat, alpha=0.2, label=name)
    plt.plot(
        log_pop[np.argsort(log_pop)],
        prediction[np.argsort(log_pop)],
        color="orange",
        label=f"Expected {name}",
    )
    plt.xlabel("log population")
    plt.ylabel(name_full)
    plt.title("Counties")
    plt.legend()
    overall["expected"] = prediction
    overall["overperformance"] = (stat - prediction) / prediction * 100
    mapping = dict(zip(overall.fips, overall.overperformance))

    csv = overall[
        ["state", "county", "POP100", stat_col, "expected", "overperformance"]
    ].rename(
        columns={
            "POP100": "population",
            stat_col: name,
            "expected": f"expected {name}",
            "overperformance": f"relative {name}",
        }
    )
    csv[f"relative {name}"] /= 100
    csv.to_csv(f"{name}.csv", index=False)

    geojson = geojson_to_use()
    geojson["overperformance"] = geojson.apply(lambda row: mapping[row.fips], axis=1)
    geojson.to_file(f"temp/{name}.shp")

    return overall


@permacache("county-importance-wikipedia/get_trends")
def get_trends(keyword):
    print(keyword)
    time.sleep(0.1)
    trends = TrendReq(hl="en-US", tz=0, retries=10)
    trends.build_payload([keyword], timeframe="all")
    res = trends.interest_over_time()
    if res.size == 0:
        return None
    return res[keyword]


@permacache("county_importance_wikipedia/load_county_geojson_2")
def load_county_geojson():
    tempdir = tempfile.TemporaryDirectory()
    rootpath = tempdir.name
    os.system(f"mkdir -p {rootpath}")
    zip = requests.get(
        "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_county_500k.zip"
    ).content
    with open(f"{rootpath}/hi.zip", "wb") as f:
        f.write(zip)
    os.system(f"cd {rootpath}; unzip hi.zip")

    return geopandas.read_file(f"{rootpath}/cb_2020_us_county_500k.shp")


def geojson_to_use():
    geojson = load_county_geojson()
    geojson["fips"] = geojson.STATEFP + geojson.COUNTYFP
    geojson = geojson[
        geojson.STATEFP.apply(lambda x: x not in {"78", "60", "69", "66"})
    ]
    geojson = geojson.copy()
    return geojson
