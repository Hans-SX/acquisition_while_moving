"""
Created on  Feb. 03, 2025

@author: Shih-Xian

With andor3, https://gitlab.com/ptapping/andor3/-/tree/main
"""

import numpy as np
from tifffile import imwrite
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import os
from os.path import join
from andor3 import Andor3
from utils import config_andor, platform_DaisyChain, save_config_andor, acquisition_moving_2axes

parser = argparse.ArgumentParser()
parser.add_argument("--name", type=str)
parser.add_argument("--steps", nargs='?', const=1, type=int)
args = parser.parse_args()

expdate = datetime.now().strftime("_%Y_%m_%d_%H%M")

#? Platforms configuration and Daisy chain connection.
daisychain = platform_DaisyChain()
pidz = daisychain.pid1
pidx = daisychain.pid2
daisychain.config_platform(pidz, 3)  # Focus point: 7, with micrometer in 15.
daisychain.config_platform(pidx, 9.5)
print("Daisy Chain platforms configurations done.")

#? Camera congigurations and ROI settomg
cam_ang = Andor3()
print(f"{cam_ang.CameraFamily} {cam_ang.CameraModel} {cam_ang.CameraName} {cam_ang.InterfaceType}")

config_andor(cam_ang)
print("Camera configurations done.")

save_config_andor(cam_ang, args.name, expdate)

print("Starting acquisition.")
raw_img, timer = acquisition_moving_2axes(cam_ang, pidz, pidx, args.steps)

#? Disonnect devieces.
cam_ang.close()
daisychain.CloseConnection()

#? Save the images
print("Processing data.")
images = []
for img in raw_img:
    images.append(cam_ang.decode_image(img)[0])
images = np.asarray(images)
images = np.rot90(images, 1, axes=(1,2))
print("Saving as tif.")
datapath = join(os.getcwd(), args.name, "data", "angular")
if not os.path.exists(datapath):
    os.makedirs(datapath)
imwrite(join(datapath, "angular.tif"), images)

runtimep_name = "Runtime_profile_" + expdate + ".txt"
timer.savefile(join(os.getcwd(), args.name, runtimep_name))
print("Acqusition done.")