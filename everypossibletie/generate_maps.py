from state_sets import get_subsets
from renderer import render_all_subsets, stitch_together
subsets = get_subsets(269)
paths = render_all_subsets(subsets, "Tie")
stitch_together(
    paths,
    W=1000,
    H=650,
    WH=1500,
    HH=650,
    ncols=6,
    nrows=8,
    header_path="header_ties.svg",
    output_path="outputs/ties.svg",
)
subsets = get_subsets(232, 306)
paths = render_all_subsets(subsets, "Repeat")
stitch_together(
    paths,
    W=1000,
    H=650,
    WH=2500,
    HH=650,
    ncols=8,
    nrows=10,
    header_path="header_repeats.svg",
    output_path="outputs/cursed.svg",
)