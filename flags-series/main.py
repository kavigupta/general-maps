import gspread
import pytumblr

from constants import NAME, TUMBLR_PATH
from utils import gather_row, get_rendered_image, read_table, update_full_list

from secret import *


def main_tumblr():

    print("Starting")
    tweets_sheet = gspread.service_account().open(NAME).sheet1
    row = gather_row(read_table(tweets_sheet), "Shipped Tumblr?")

    if row is None:
        return

    print("Running for row")
    print(row)

    client = pytumblr.TumblrRestClient(
        tumblr_consumer_key,
        tumblr_consumer_secret,
        tumblr_oauth_key,
        tumblr_oauth_secret,
    )

    run_for_row(client, tweets_sheet, row)


def run_for_row(client, tweets_sheet, row):
    row = get_rendered_image(row, "Date Tumblr")
    if row is None:
        return
    png_path, index, name, description, date, svg_path = row
    result = client.create_photo(
        "elimgarakdemocrat",
        state="published",
        slug=name.replace(" ", "-"),
        caption=f"{NAME} {index}: {name}\n\n{description}",
        tags=["flagration", "flags", "vexillology", "flag redesign"],
        data=png_path,
    )
    tweets_table = read_table(tweets_sheet)

    [idx] = tweets_table[tweets_table["Index"] == index].index
    row = idx + 2
    tweets_sheet.update_cell(
        row, list(tweets_table).index("Shipped Tumblr?") + 1, "TRUE"
    )
    tweets_sheet.update_cell(
        row, list(tweets_table).index("Tumblr id") + 1, result["id_string"]
    )

    tumblr_url = TUMBLR_PATH.format(id=result["id_string"])

    update_full_list(index, name, date, svg_path, tumblr_url)


if __name__ == "__main__":
    main_tumblr()
