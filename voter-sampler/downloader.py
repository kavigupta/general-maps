import requests

from permacache import permacache

from geopy.geocoders import Nominatim


def api_key():
    with open("/home/kavi/.google_maps_api_key.txt") as f:
        return f.read().strip()


@permacache("voter-sampler/downloader/download_streetview")
def download_streetview(x, y, radius=250):
    key = api_key()
    url = (
        "https://maps.googleapis.com/maps/api/streetview?"
        + "size=2000x2000&"
        + f"location={y:.6f},{x:.6f}&"
        + f"radius={radius}&pitch=0&key={key}"
    )
    print(url)
    response = requests.get(url)
    return response.content


@permacache("voter-sampler/downloader/reverse_geocode_2")
def reverse_geocode(x, y):
    print("reverse geocode", y, x)
    locator = Nominatim(user_agent="kavig")
    result = locator.reverse(f"{y}, {x}")
    print(result)
    return result


road_types = {
    "Avenue": 1,
    "Street": 1,
    "Road": 1,
    "Crossing": 1,
    "Lane": 1,
    "Circle": 1,
    "Terrace": 1,
    "Drive": 0,
    "Court": 0,
    "Ct": 0,
    "Boulevard": 0,
    "Freeway": -1,
    "Business": -1,
}


def classify_road_type(road_name):
    for direction in ("Northwest",):
        if road_name.endswith(f" {direction}"):
            road_name = road_name[: -(len(direction) + 1)]
    road_type = road_name.split(" ")[-1]
    if road_type in road_types:
        return road_types[road_type]
    if road_type.isnumeric():
        return -1
    raise RuntimeError(road_name)


def refine_location(x, y, delta=0.001):
    deltas = [0, -delta, delta]
    neighboring_coordinates = [(x + dx, y + dy) for dx in deltas for dy in deltas]
    c = max(
        neighboring_coordinates,
        key=lambda xy: classify_road_type(reverse_geocode(*xy).raw["address"]["road"]),
    )
    c = reverse_geocode(*c)
    return c.longitude, c.latitude
