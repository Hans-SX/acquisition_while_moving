
from tifffile import imread, imwrite
import os
from os.path import join as PJ

# cd to the directory of tif file.

file = [k for k in os.listdir(os.getcwd()) if ".tif" in k]
print(file)
tifs = imread(file)

N = tifs.shape[0]

spadir = PJ(os.getcwd(), "spatial")
if not os.path.exists(spadir):
    os.makedirs(spadir)
for cyc in range(N//100):
    imwrite(PJ(spadir, f"spatial_{cyc+1:02d}.tif"), tifs[cyc*100:(cyc+1)*100])