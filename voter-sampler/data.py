import pandas as pd
import numpy as np

from downloader import refine_location


def get_precincts():
    return pd.read_csv("/home/kavi/full-usa-precinct-map/out/centroids.csv")


def load_data(total_samples):
    precincts = get_precincts()
    overall = precincts[["R", "D"]].sum()
    samples_each = (total_samples / overall.sum() * overall).round()

    def select_precincts(sample_column, num_samples):
        weights = np.array(precincts[sample_column])
        weights[precincts.state == "KY"] = 0
        weights = weights / weights.sum()
        samples = np.random.RandomState(ord(sample_column)).choice(
            len(weights), p=weights, replace=False, size=int(num_samples)
        )
        selected_precincts = precincts.iloc[samples].copy()
        selected_precincts["selected_party"] = [sample_column] * len(selected_precincts)
        selected_precincts["ox"] = selected_precincts.x
        selected_precincts["oy"] = selected_precincts.y
        return selected_precincts.copy()

    to_interleave = [
        select_precincts(k, samples_each[k]) for k in sorted(samples_each.index)
    ]
    rows = []
    for i in range(max(x.shape[0] for x in to_interleave)):
        for ti in to_interleave:
            if i < ti.shape[0]:
                rows.append(ti.iloc[i])
    for row in rows:
        row.x, row.y = refine_location(row.x, row.y)
    return pd.DataFrame(rows)
