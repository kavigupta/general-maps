import datetime
import os
import subprocess
import tempfile
import pandas as pd
import gspread

from constants import GITHUB_PATH, NAME, ROOT_PATH, TIME_TO_PUBLISH, TZ


def read_table(tweets_sheet):
    header, *values = tweets_sheet.get_all_values()
    return pd.DataFrame(values, columns=header)


def gather_row(tweets_table, column):
    to_ship = tweets_table[
        (tweets_table["Ship?"] == "TRUE") & (tweets_table[column] == "FALSE")
    ]
    if len(to_ship) == 0:
        return None
    index = min((idx for idx in to_ship["Index"]), key=int)
    row = to_ship[to_ship["Index"] == index].iloc[0]
    return row


def get_rendered_image(row, date_key):
    current_time = datetime.datetime.now(TZ)
    time_to_publish = get_time_to_publish(row, date_key)
    delta = current_time - time_to_publish
    if delta <= datetime.timedelta(0):
        return
    png_path = render_image(row["Flag path"])

    print("Image made")

    index, name, description = row["Index"], row["Flag name"], row["Flag description"]
    date = row[date_key]
    svg_path = row["Flag path"]
    return png_path, index, name, description, date, svg_path


def get_time_to_publish(row, date_key):
    return TZ.localize(
        datetime.datetime.strptime(
            row[date_key] + " " + TIME_TO_PUBLISH, "%Y-%m-%d %H:%M"
        )
    )


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

def update_full_list(index, name, date, svg_path, url):
    full_list = gspread.service_account().open("Full list of maps and flags")
    full_list.sheet1.append_row(
        [
            f"{NAME} {index}: {name}",
            int(index),
            date,
            "Flag redesign",
            NAME,
            GITHUB_PATH.format(
                hash=subprocess.check_output(["git", "rev-parse", "HEAD"]).decode(
                    "utf-8"
                ).strip()
            )
            + svg_path,
            url,
        ]
    )
