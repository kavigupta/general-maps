import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker/")

import copy
import torch
import numpy as np
import tqdm.auto as tqdm

from mapmaker.colors import Profile, DEFAULT_CREDIT
from mapmaker.generate_image import get_model
from mapmaker.stitch_map import produce_entire_map
from mapmaker.alternate_universe import create_alternate_universe
from mapmaker.data import data_by_year
from mapmaker.mapper import USAPresidencyBaseMap
from mapmaker.aggregation import (
    get_electoral_vote_by_voteshare,
    get_popular_vote_by_voteshare,
)

from permacache import permacache

k = 10_000

credit = (
    f"Calculated by sampling {k} bot_althistory runs where the PV/EC diverge "
    + "and computing the % of runs where the given county appears on the winning side. "
    + DEFAULT_CREDIT
)
profile = Profile(
    symbol=dict(dem="B", gop="D"),
    name=dict(dem="Benefited", gop="Disadvantaged"),
    hue=dict(dem=270 / 360, gop=90 / 360),
    bot_name="bot_althistory",
    credit=credit,
    credit_scale=0.5,
    suffix=" by the EC",
    value="normalize",
)


def sample(i):
    model = get_model(calibrated=False, num_demographics=30)
    copied_model = copy.deepcopy(model)
    data = data_by_year()[2020]

    torch.manual_seed(i)
    t, voteshare_by_party = create_alternate_universe(copied_model, profile)

    popular_vote = get_popular_vote_by_voteshare(
        data, voteshare_by_party=voteshare_by_party, turnout=t
    )
    ec = get_electoral_vote_by_voteshare(
        data,
        voteshare_by_party=voteshare_by_party,
        turnout=t,
        basemap=USAPresidencyBaseMap(),
    )
    if ec["dem"] >= ec["gop"]:
        return
    dem_pv_win = popular_vote["dem"] > popular_vote["gop"]
    if not dem_pv_win:
        return
    return voteshare_by_party, popular_vote, ec


@permacache("general-maps-and-flags/ec-bias/sample_guaranteed_5")
def sample_guaranteed(i):
    rng = np.random.RandomState(i)
    while True:
        x = sample(rng.choice(2 ** 32))
        if x is not None:
            return x


def main():
    data = data_by_year()[2020]
    in_winning_side = []
    for i in tqdm.tqdm(range(k)):
        shares = sample_guaranteed(i)[0]
        in_winning_side += [shares["gop"] > shares["dem"]]
    on_winning_side = np.array(in_winning_side).mean(0)
    _ = produce_entire_map(
        data,
        title="Mean EC benefit under random coalitions",
        out_path="result.svg",
        dem_margin=on_winning_side * 2 - 1,
        turnout=1,
        basemap=USAPresidencyBaseMap(),
        year=2020,
        use_png=True,
        profile=profile,
    )


if __name__ == "__main__":
    main()
