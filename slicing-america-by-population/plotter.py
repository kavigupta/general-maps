import numpy as np

import matplotlib.pyplot as plt
import matplotlib

from colorsys import hsv_to_rgb

import sys

sys.path.insert(0, "/home/kavi/2024-bot/mapmaker")
from mapmaker.mapper import USAPresidencyBaseMap
from mapmaker.colors import STANDARD_PROFILE
from mapmaker.stitch_map import remove_backgrounds


def plot_results(margins, years, colors, **kwargs):
    plt.figure(figsize=(7, 7), facecolor="white", tight_layout=True)
    assert len(margins) == len(colors)
    for k, margin in enumerate(margins):
        plt.plot(years, margin, label=f"Quintile {k + 1}", color=colors[k], **kwargs)
    plt.xticks(years)
    plt.legend()
    y_axis_margin()
    plt.grid()


def y_axis_margin():
    plt.gca().yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(
            lambda x, y: f"D+{x*100:.0f}"
            if x > 0
            else f"R+{-x*100:.0f}"
            if x < 0
            else "Even"
        )
    )


def plot_by_kile(data, series, tick_colors):
    quantile = {5: "quintile"}
    plt.figure(facecolor="white", figsize=(5, 4), dpi=200, tight_layout=True)
    xs = np.arange(data.shape[0]) + 1
    for y, a in zip(series, data.T):
        plt.plot(xs, a[::-1], label=y, linewidth=1, marker=".")
    y_axis_margin()
    plt.xlabel(f"Density {quantile[data.shape[0]]}")
    plt.axhline(0, color="black")
    plt.xticks(xs)
    plt.grid()
    plt.legend()
    ticks, lines = plt.gca().get_xticklabels(), plt.gca().get_xgridlines()
    assert len(ticks) == len(lines) == len(tick_colors)
    for tick, line, c in zip(ticks, lines, reversed(tick_colors)):
        tick.set_color(c)
        line.set_color(c)


def color(hue):
    rgb = np.array(hsv_to_rgb(hue / 360, 0.65, 1))
    greenness = 1 - abs(hue - 120) / 30
    greenness = greenness * (greenness > 0)
    rgb = rgb / rgb.sum() * (1.5 - greenness / 4)
    rgb = (rgb * 255).astype(np.int)
    return "#" + ("%02x" * 3) % tuple([*rgb])


def plot_map(densities, ordinals, hues):
    assert len(hues) == ordinals.max() + 1
    hue_points = np.linspace(0, 1, len(hues))
    counties, _ = USAPresidencyBaseMap().county_map(
        identifiers=densities["Fips Code"],
        variable_to_plot=ordinals,
        zmin=0,
        zmid=ordinals.max() / 2,
        zmax=ordinals.max(),
        colorscale=[(hp, color(h)) for hp, h in zip(hue_points, hues)],
        profile=STANDARD_PROFILE,
    )
    counties.write_image("out/map.svg")
    remove_backgrounds("out/map.svg", STANDARD_PROFILE, remove_lakes=True)
    return [color(h) for h in hues]


def plot_both(data, years, colors, ylabel, pathname):
    plot_by_kile(data, years, colors)
    plt.ylabel(ylabel)
    plt.savefig(f"out/{pathname}.png")
    plt.close()

    plot_results(data, years, colors)
    plt.ylabel(ylabel)
    plt.savefig(f"out/transposed_{pathname}.png")
    plt.close()

def plot_4(data, years, colors, ylabel, pathname):
    plot_both(data, years, colors, ylabel, pathname)
    plot_both(
        data[:, 1:] - data[:, :-1],
        years[1:],
        colors,
        f"{ylabel} Swing from last election",
        f"{pathname}_swing",
    )
