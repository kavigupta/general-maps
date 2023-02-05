import datetime
import os
import subprocess
import tempfile

import gspread
import tweepy
import pytz

import pandas as pd

from secret import *
from constants import *
from utils import gather_row, get_rendered_image, read_table, update_full_list


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


def update_tweets_table(tweets_sheet, *, update_index, main_tweet, thread_tweet):
    tweets_table = read_table(tweets_sheet)

    [idx] = tweets_table[tweets_table["Index"] == update_index].index
    row = idx + 2
    tweets_sheet.update_cell(row, list(tweets_table).index("Shipped?") + 1, "TRUE")
    tweets_sheet.update_cell(
        row, list(tweets_table).index("Main id") + 1, str(main_tweet)
    )
    tweets_sheet.update_cell(
        row, list(tweets_table).index("Thread id") + 1, str(thread_tweet)
    )


def run_for_row(twitter_api, tweets_sheet, row):
    row = get_rendered_image(row, "Date")
    if row is None:
        return
    png_path, index, name, description, date, svg_path = row

    main_tweet, thread_tweet = tweet_image(
        read_table(tweets_sheet),
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

    update_full_list(index, name, date, svg_path, kavis_tweet(main_tweet))


def main_twitter():

    print("Starting")
    tweets_sheet = gspread.service_account().open(NAME).sheet1
    row = gather_row(read_table(tweets_sheet), "Shipped?")

    if row is None:
        return

    print("Running for row")
    print(row)

    my_auth = tweepy.OAuthHandler(my_consumer_key, my_consumer_secret)
    my_auth.set_access_token(my_access_token, my_access_token_secret)
    twitter_api = tweepy.API(my_auth)

    run_for_row(twitter_api, tweets_sheet, row)
