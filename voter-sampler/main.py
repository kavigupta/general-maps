import io
from PIL import Image

from data import load_data, get_precincts
from downloader import download_streetview
from renderer import populate_template


def main(count):
    selection = load_data(count)
    total = get_precincts()
    rs_in_d, ds_in_r = (
        total.R[total.R < total.D].sum() / total.R.sum(),
        total.D[total.R > total.D].sum() / total.D.sum(),
    )
    print(rs_in_d, ds_in_r)
    images = []
    for _, row in selection.iterrows():
        images.append(Image.open(io.BytesIO(download_streetview(row.x, row.y))))
    for idx in range(len(images)):
        images[idx].save(f"out/images/{idx}.png")

    with open("out/random-voters-2020.html", "w") as f:
        f.write(populate_template(selection))

main(10)