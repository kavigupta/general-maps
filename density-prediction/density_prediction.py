import attr
import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import NearestNeighbors
import wquantiles


@attr.s
class Data:
    fipses = attr.ib()
    log_density = attr.ib()
    dem_margin = attr.ib()
    cvap = attr.ib()
    prediction = attr.ib()
    density_key = attr.ib()
    title = attr.ib()

    @staticmethod
    def of(df, density_key, title):
        density = np.array(df[density_key], dtype=np.float)
        log_density = np.log(density + 1)
        dem_margin = np.array(df["dem_margin"])
        cvap = np.array(df["CVAP"])

        knn = NearestNeighbors(radius=0.5).fit(log_density[:, None])

        # median_prediction = np.array(
        #     [knn_predict(knn, x, dem_margin, cvap, "median") for x in log_density]
        # )

        prediction = np.array(
            [knn_predict(knn, x, dem_margin, cvap, "mean") for x in log_density]
        )

        return Data(
            df.index, log_density, dem_margin, cvap, prediction, density_key, title
        )

    @property
    def error(self):
        return (
            np.abs(self.prediction - self.dem_margin) * self.cvap
        ).sum() / self.cvap.sum()

    def plot(self, ax):
        c = [color(c) for c in self.dem_margin]
        ax.scatter(
            self.log_density,
            self.dem_margin * 50,
            # alpha=self.cvap / self.cvap.max(),
            alpha=0.25,
            s=(self.cvap / self.cvap.max()) * 200,
            c=c,
        )
        ax.axhline(0, color="black")
        ax.grid()
        idxs = np.argsort(self.log_density)
        ax.plot(
            self.log_density[idxs],
            100 * self.prediction[idxs],
            label=f"Prediction [mean error={self.error:.2%}]",
            color="magenta",
            # lw=3,
        )
        # plt.plot(log_density[idxs], 100 * predictions_median[idxs], label="Prediction")
        ax.legend()
        ax.set_xlabel(f"log {self.density_key}")
        ax.set_ylabel("Biden margin [%]")
        ax.set_xlim(
            *[
                wquantiles.quantile(self.log_density, self.cvap, q)
                for q in (0.001, 1 - 0.001)
                # for q in (0.025, 0.975)
            ]
        )
        ax.set_ylim(-50, 50)
        ax.set_title(self.title)

    def map_prediction(self, series):
        d = dict(zip(self.fipses, self.prediction))
        return series.apply(lambda x: np.nan if x.startswith("02") else d[x])


def knn_predict(knn, x, ys, weight, strategy):
    _, idxs = knn.radius_neighbors(np.array([x])[:, None])
    idxs = idxs[0]
    if idxs.size == 0:
        return np.nan
    if strategy == "median":
        return wquantiles.median(ys[idxs], weight[idxs])
    else:
        return (ys[idxs] * weight[idxs]).sum() / weight[idxs].sum()


import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker")

from mapmaker.colors import STANDARD_PROFILE, get_color


def color(dem_margin):
    return (
        get_color(STANDARD_PROFILE.county_colorscale, (dem_margin + 1) * 0.5).astype(
            np.float
        )
        / 255
    )
