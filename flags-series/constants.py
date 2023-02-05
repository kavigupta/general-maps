import os

import pytz

NAME = "Flag Ration"

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

GITHUB_PATH = (
    "https://github.com/kavigupta/general-maps/blob/{hash}/flags-series/flags/"
)

TUMBLR_PATH = "https://www.tumblr.com/elimgarakdemocrat/{id}"

TIME_TO_PUBLISH = "15:00"

TZ = pytz.timezone("America/New_York")
