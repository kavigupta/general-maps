from colorsys import rgb_to_hsv
from permacache import stable_hash
import numpy as np
from PIL import Image


def pick_color(ocean_color, is_ocean, protect_radius, seed, idx):
    if is_ocean:
        return ocean_color
    rng = np.random.RandomState(int(stable_hash((seed, idx)), 16) % 2 ** 32)
    h_ocean, _, _ = rgb_to_hsv(*(ocean_color / 255))
    while True:
        color = rng.choice(256, size=3)
        h, _, _ = rgb_to_hsv(*(color / 255))

        delta_h = h - h_ocean
        delta_h %= 1
        if delta_h > 0.5:
            delta_h = delta_h - 1
        if abs(delta_h * 360) > protect_radius:
            return color


def convert_components(w, components):
    components = [np.array(list(c)) for c in components]
    components = [(c % w, c // w) for c in components]
    return components


def render_map(
    components,
    *,
    w,
    h,
    seed,
    ocean_color=np.array([115, 183, 255]),
    protect_radius=50,
    scale=1
):
    components = convert_components(w, components)
    image = np.zeros((h, w, 3), dtype=np.uint8)
    for i, (xc, yc) in enumerate(components):
        image[yc, xc] = pick_color(
            ocean_color,
            is_ocean=i == len(components) - 1,
            protect_radius=protect_radius,
            seed=seed,
            idx=i,
        )
    image = Image.fromarray(image).resize((w * scale, h * scale), Image.NEAREST)
    return image
