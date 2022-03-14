from pdf2image import convert_from_path

import numpy as np

from PIL import Image
start_dpi = 10
true_width = 3700
true_height = 2900
pages = convert_from_path('wiki.pdf', start_dpi)
num_pages = len(pages)
w, h = pages[0].size
# ideal_width * ideal_height * len(num_pages) == true_width * true_height
# ideal_width ** 2 * ratio * len(num_pages) == true_width * true_height
ideal_width = (true_width * true_height / (num_pages * h / w)) ** 0.5
num_cols = int(true_width // ideal_width)
num_rows = (num_pages + num_cols - 1) // num_cols
true_dpi = ideal_width / w * start_dpi
pages = convert_from_path('wiki.pdf', true_dpi)
w, h = pages[0].size
image_overall = np.zeros((h * num_rows, w * num_cols, 3), dtype=np.uint8) + 255
for row in range(num_rows):
    for col in range(num_cols):
        page = row + col * num_rows
        if page < len(pages):
            image_overall[h * row:h*(row + 1), w*col:w*(col + 1)] = np.array(pages[page])
Image.fromarray(image_overall).save("wiki.png")