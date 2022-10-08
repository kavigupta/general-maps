import datetime
import os
import subprocess
import tempfile

import gspread
import tweepy
import pytz

import pandas as pd

from secret import *

NAME = "Flag Ration"

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

GITHUB_PATH = (
    "https://github.com/kavigupta/general-maps/blob/{hash}/flags-series/flags/"
)

TIME_TO_PUBLISH = "15:00"

TZ = pytz.timezone("America/New_York")


def render_image(file_name):
    png_path = tempfile.mktemp()

    subprocess.check_call(
        [
            "inkscape",
            os.path.join(ROOT_PATH, "flags", file_name),
            "-e",
            png_path,
            "-w",
            "4096",
        ]
    )
    return png_path


def kavis_tweet(id):
    return f"https://twitter.com/notkavi/status/{id}"


def tweet_image(tweets_table, api, *, png_path, index, name, description):
    root_tweet, reply_to = tweet_to_reply_to(tweets_table, 1), tweet_to_reply_to(
        tweets_table, index
    )
    status = f"{NAME} {index}: {name}\n\n{description}"
    main_tweet = api.update_with_media(png_path, status=status)
    thread_tweet = api.update_status(
        f"{NAME} {index}: {name}\n" + kavis_tweet(main_tweet.id),
        in_reply_to_status_id=reply_to,
    )
    api.update_status(
        status=f"Follow the rest of the series here!\n" + kavis_tweet(root_tweet),
        in_reply_to_status_id=main_tweet.id,
    )
    return main_tweet.id, thread_tweet.id


def tweet_to_reply_to(tweets_table, index):
    above = tweets_table[tweets_table["Index"] == str(int(index) - 1)]["Thread id"]
    assert len(above) == 1
    return above.iloc[0]


def read_tweets_table(tweets_sheet):
    header, *values = tweets_sheet.get_all_values()
    return pd.DataFrame(values, columns=header)


def update_tweets_table(tweets_sheet, *, update_index, main_tweet, thread_tweet):
    tweets_table = read_tweets_table(tweets_sheet)

    [idx] = tweets_table[tweets_table["Index"] == update_index].index
    row = idx + 2
    tweets_sheet.update_cell(row, list(tweets_table).index("Shipped?") + 1, "TRUE")
    tweets_sheet.update_cell(
        row, list(tweets_table).index("Main id") + 1, str(main_tweet)
    )
    tweets_sheet.update_cell(
        row, list(tweets_table).index("Thread id") + 1, str(thread_tweet)
    )


def get_time_to_publish(row):
    return TZ.localize(
        datetime.datetime.strptime(
            row["Date"] + " " + TIME_TO_PUBLISH, "%Y-%m-%d %H:%M"
        )
    )


def run_for_row(twitter_api, tweets_sheet, row):
    current_time = datetime.datetime.now(TZ)
    time_to_publish = get_time_to_publish(row)
    delta = current_time - time_to_publish
    if delta <= datetime.timedelta(0):
        return
    png_path = render_image(row["Flag path"])

    print("Image made")

    index, name, description = row["Index"], row["Flag name"], row["Flag description"]

    main_tweet, thread_tweet = tweet_image(
        read_tweets_table(tweets_sheet),
        twitter_api,
        png_path=png_path,
        index=index,
        name=name,
        description=description,
    )

    update_tweets_table(
        tweets_sheet,
        update_index=index,
        main_tweet=main_tweet,
        thread_tweet=thread_tweet,
    )

    full_list = gspread.service_account().open("Full list of maps and flags")
    full_list.sheet1.append_row(
        [
            f"{NAME} {index}: {name}",
            int(index),
            row["Date"],
            "Flag redesign",
            NAME,
            GITHUB_PATH.format(
                hash=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode(
                    "utf-8"
                ).strip()
            )
            + row["Flag path"],
            kavis_tweet(main_tweet),
        ]
    )


def gather_row(tweets_table):
    to_ship = tweets_table[
        (tweets_table["Ship?"] == "TRUE") & (tweets_table["Shipped?"] == "FALSE")
    ]
    if len(to_ship) == 0:
        return None
    index = min((idx for idx in to_ship["Index"]), key=int)
    row = to_ship[to_ship["Index"] == index].iloc[0]
    return row


def main():

    print("Starting")
    tweets_sheet = gspread.service_account().open(NAME).sheet1
    row = gather_row(read_tweets_table(tweets_sheet))

    if row is None:
        return

    print("Running for row")
    print(row)

    my_auth = tweepy.OAuthHandler(my_consumer_key, my_consumer_secret)
    my_auth.set_access_token(my_access_token, my_access_token_secret)
    twitter_api = tweepy.API(my_auth)

    run_for_row(twitter_api, tweets_sheet, row)


if __name__ == "__main__":
    main()
