
from tifffile import imread, imwrite
import os
from os.path import join as PJ

# cd to the directory of tif file.

file = [k for k in os.listdir(os.getcwd()) if ".tif" in k]
print(file)
tifs = imread(file)

N = tifs.shape[0]
for cyc in range(N//100):
    imwrite(PJ(os.getcwd(), "spatial_" + str(cyc+1) + ".tif"), tifs[cyc*100:(cyc+1)*100])