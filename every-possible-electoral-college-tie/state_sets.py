import itertools
import pandas as pd
import us


ec_csv = pd.read_csv(
    "https://raw.githubusercontent.com/kavigupta/2024_bot/main/csvs/ec.csv"
)
results = {
    us.states.lookup(r.state).abbr: r.electoral_college for _, r in ec_csv.iterrows()
}
del results["ME"]
results["ME-AL"] = 2
results["ME-1"] = 1
results["ME-2"] = 1

del results["NE"]
results["NE-AL"] = 2
results["NE-1"] = 1
results["NE-2"] = 1
results["NE-3"] = 1
safe_dem = {
    "DC",
    "VT",
    "MA",
    "MD",
    "HI",
    "CA",
    "NY",
    "ME-1",
    "RI",
    "CT",
    "DE",
    "WA",
    "IL",
    "NJ",
    "OR",
    "CO",
    "NM",
    "VA",
    "MN",
}
safe_gop = {
    "NE-3",
    "WY",
    "WV",
    "ND",
    "OK",
    "ID",
    "AR",
    "SD",
    "KY",
    "AL",
    "TN",
    "UT",
    "NE-AL",
    "LA",
    "MT",
    "IN",
    "MS",
    "NE-1",
    "MO",
    "KS",
    "SC",
    "AK",
    "IA",
    "OH",
}

likely_dem = {"ME-AL", "NH", "NV"}

likely_gop = {"FL", "NC", "TX", "ME-2"}


def plausibility(subset):
    return (set(subset) & likely_dem) | (likely_gop - set(subset))


tossup = {"AZ", "GA", "WI", "MI", "PA", "NE-2"}

assert (safe_dem | safe_gop) - set(results) == set()
states_under_discussion = set(results) - safe_dem - safe_gop

assert states_under_discussion == likely_dem | likely_gop | tossup

STATES = sorted(results)


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(s, r) for r in range(len(s) + 1)
    )


def grouped(result, whole, *parts):
    if whole in result:
        return any(part in result for part in parts)
    else:
        return any(part not in result for part in parts)


def get_subsets(*target_dem):
    starting_dem = sum(results[s] for s in safe_dem)
    subsets = []
    for subset in powerset(states_under_discussion):
        if sum(results[s] for s in subset) not in {
            t - starting_dem for t in target_dem
        }:
            continue
        full_dem = safe_dem | set(subset)

        if not grouped(full_dem, "ME-AL", "ME-1", "ME-2"):
            continue
        if not grouped(full_dem, "NE-AL", "NE-1", "NE-2", "NE-3"):
            continues
        subsets.append(subset)
    return sorted(subsets, key=lambda x: [-len(plausibility(x)), sorted(x)])
