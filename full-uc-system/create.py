import pandas as pd

def is_uc(x):
    acronyms = "".join(t[0] for t in x.split() if t[0].isupper())
    return acronyms.startswith("UC") and len(acronyms) > 2

dropped = [
    'University Center "César Ritz"',
    "University College of Arts, Crafts and Design",
    "University College of Borås",
    "University College of Cape Breton",
    "University College of Gävle",
    "University College of Kristianstad",
    "University College of Saint-Boniface",
    "University College of Skövde",
    "University College of Technology & Innovation (UCTI)",
    "University College of Trollhättan/Uddevalla",
    "University College of the Cariboo",
    "University College of the Fraser Valley",
    "University of California System",
    "University of California, Oakland",
    "University of Central Europe in Skalica",
    "University of Central Greece",
    "University of Central Texas",
    "University of Charleston South Carolina",
    "University of Colorado Health Sciences Center",
    "University of Commerce Luigi Bocconi",
    "University of Connecticut Health Center",
    "University of Constanta Medical School",
    "University of the City of Manila",
]
name_map = {
    "University College London, University of London": "University College London",
    "University of California, Hastings College of Law": "University of California, Hastings",
}
coords = {
    "Uganda Christian University": (0.356836942746774, 32.74072692089419),
    "Union College Kentucky": (36.8704065209229, -83.88836990369973),
    "Union College Nebraska": (40.77354704856708, -96.65255930371431),
    "University Canada West": (49.284145195811625, -123.11431505522704),
    "University Centre of the Westfjords": (66.06902442003603, -23.125888203709938),
    "University College Bahrain": (26.193180327101913, 50.47992223861721),
    "University College Cork": (51.893697872667076, -8.491834465598657),
    "University College Dublin": (53.30664370346626, -6.2256488325463675),
    "University College London": (
        51.52459257627619,
        -0.134061557672849,
    ),
    "University College of Applied Sciences": (31.49765811938991, 34.43680911720067),
    "University College of Nabi Akram": (38.07343, 46.243347013490734),
    "University of Cagayan Valley": (17.6235963, 121.73088194974702),
    "University of California, Berkeley": (37.87176369291613, -122.25842188279931),
    "University of California, Davis": (38.538181847886804, -121.76164812698146),
    "University of California, Hastings": (37.78112198156947, -122.41579435581787),
    "University of California, Irvine": (33.64067384134952, -117.84392069072514),
    "University of California, Los Angeles": (34.06879657652112, -118.44533130370998),
    "University of California, Merced": (37.36597140291848, -120.4224608153457),
    "University of California, Riverside": (33.97358983423597, -117.32796784047218),
    "University of California, San Diego": (32.878435356911886, -117.23556034907263),
    "University of California, San Francisco": (37.7626459, -122.45856039629003),
    "University of California, Santa Barbara": (
        34.413954048969686,
        -119.84881825396292,
    ),
    "University of California, Santa Cruz": (36.98777606668195, -122.05806982512648),
    "University of Cape Coast": (5.115453813896624, -1.2905325349072647),
    "University of Cape Town": (-33.957776586467304, 18.461123998145023),
    "University of Central Arkansas": (35.0780412190707, -92.45768775210796),
    "University of Central Florida": (28.602286107140557, -81.19987750978078),
    "University of Central Lancashire": (53.764357294775074, -2.7083030846543017),
    "University of Central Missouri": (38.757643970136684, -93.74037006930858),
    "University of Central Oklahoma": (35.65738395698176, -97.4709061846543),
    "University of Central Punjab": (31.446826475749376, 74.26838180370993),
    "University of Chemical Technology and Metallurgy": (
        42.655284257293964,
        23.3584073846543,
    ),
    "University of Colorado at Boulder": (39.746264587829, -105.00254671740744),
    "University of Colorado at Colorado Springs": (
        38.89652474569112,
        -104.8049036456154,
    ),
    "University of Colorado at Denver": (39.746326603137334, -105.00222398279936),
    "University of Computer Studies, Yangon": (17.00197922097845, 96.09248890185498),
    "University of Connecticut at Avery Point": (41.31789716809873, -72.06470921349072),
    "University of Connecticut at Hartford": (41.762569203457794, -72.67238609836332),
    "University of Connecticut at Stamford": (41.055942487530714, -73.5423833134907),
    "University of Connecticut at Waterbury": (41.555636799275845, -73.03845056602718),
}

def strip_uc(x):
    x = x.split()
    while True:
        if x.pop(0).startswith("C"):
            break
    while not x[0][0].isupper():
        x.pop(0)
    return "UC " + " ".join(x)

result = pd.read_csv(
    "https://raw.githubusercontent.com/endSly/world-universities-csv/master/world-universities.csv",
    header=0,
    names=["country", "Name", "link"],
)
filt = pd.DataFrame(
    result[
        result.Name.map(
            lambda x: is_uc(x)
            and not x.startswith("Universidad")
            and not x.startswith("Université")
            and not "Campus" in x
            and x not in dropped
        )
    ]
)
filt["Name"] = filt.Name.apply(lambda x: name_map.get(x, x))
filt["Latitude"] = filt.Name.apply(lambda x: coords[x][0])
filt["Longitude"] = filt.Name.apply(lambda x: coords[x][1])

filt.Name = filt.Name.map(lambda x: strip_uc(x))

from shapely.geometry import Point, mapping
from fiona import collection

schema = {
    "geometry": "Point",
    "properties": {"Name": "str", "Latitude": "float", "Longitude": "float"},
}

with collection("outputs/out.shp", "w", "ESRI Shapefile", schema, crs="epsg:4326") as output:
    for index, row in filt.iterrows():

        point = Point(row["Longitude"], row["Latitude"])
        output.write(
            {
                "properties": {
                    "Name": row["Name"],
                    "Latitude": row["Latitude"],
                    "Longitude": row["Longitude"],
                },
                "geometry": mapping(point),
            }
        )