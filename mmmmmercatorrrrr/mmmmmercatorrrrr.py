from PIL import Image
import numpy as np
from math import pi
import matplotlib.pyplot as plt
equir = Image.open("equirectangular.png")
data = np.array(equir)
def data_at(lam, phi):
    i = (-phi + pi / 2) / pi * data.shape[0]
    j = (lam + pi) / (2 * pi) * data.shape[1]
    i_int = int(i)
    j_int = int(j)
    
    return data[i_int, j_int]
R = 250
h = 16
standard_mercator = np.zeros((int(h * R), int(2 * pi * R), 3), np.uint8)
ivals, jvals = np.meshgrid(np.arange(standard_mercator.shape[1]), np.arange(standard_mercator.shape[0]))
xs = ivals - standard_mercator.shape[1] / 2
ys = -jvals + standard_mercator.shape[0] / 2
lams = xs / R
phis = 2 * np.arctan(np.exp(ys / R)) - np.pi / 2

cis = ((-phis + pi / 2) / pi * data.shape[0]).astype(np.int)
cjs = ((lams + pi) / (2 * pi) * data.shape[1]).astype(np.int)

print("hi")

for j in range(standard_mercator.shape[0]):
    for i in range(standard_mercator.shape[1]):
        ci = cis[j, i]
        cj = cjs[j, i]
        standard_mercator[j,i] = data[ci, cj]
plt.figure(figsize=(10, 10))
plt.imshow(standard_mercator)
Image.fromarray(standard_mercator).save("mmmmmercatorrrrr.png")