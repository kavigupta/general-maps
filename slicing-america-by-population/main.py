from data import *
from plotter import *


election_data = load_election_data()
populations = load_populations()
densities = load_densities(populations, election_data)

margins, ordinals = classify_americas(densities, election_data, 5)

margin_swing = margins[:, 1:] - margins[:, :-1]
pvi = margins - margins.mean(0)

colors = plot_map(densities, ordinals, hues=[300, 240, 180, 100, 0])

plot_4(margins, list(election_data), colors, "Margin", "margin")
plot_4(pvi, list(election_data), colors, "PVI", "pvi")