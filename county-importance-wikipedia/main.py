from importance import *

overall = data_by_county()


wordcount = compute_overperformance(
    overall,
    stat_col = "wordcount",
    name = "Wordcount",
    name_full = "Wikipedia article wordcount",
)
discourse = compute_overperformance(
    overall,
    stat_col = "google_discourse",
    name = "Discourse",
    name_full = "Google Trends Score",
)