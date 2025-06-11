import numpy as np
from tifffile import imwrite
from datetime import datetime
import argparse
import os
from os.path import join
import time
from andor3 import Andor3
import matplotlib.pyplot as plt
from acquisition_while_moving.utils import platform_DaisyChain, save_config_andor, acquisition_moving_2axes
from acquisition_while_moving.config import z_ini, x_ini, stepsize_z, velo_z, stepsize_x, config_andor

daisychain = platform_DaisyChain()
pidz = daisychain.pid1
pidx = daisychain.pid2
daisychain.config_platform(pidz, z_ini, velo_z)  # Focus point: 7, with micrometer in 15.
daisychain.config_platform(pidx, x_ini)

daisychain.pid1.MOV('1', 16.5)

cam_ang = Andor3()
config_andor(cam_ang)
while cam_ang.SensorTemperature > 1:
    time.sleep(5)
cam_ang.queueBuffer()
raw_img = []
cam_ang.start()
for _ in range(cam_ang.FrameCount):
    cam_ang.command("SoftwareTrigger")
    # timeout:int, in milliseconds
    data = cam_ang.waitBuffer(timeout="INFINITY", copy=True, requeue=True)
    #! The effect of sleep 0.01 wasn't clear, other than the total time cost.
    #? 0.005 is enough for 1500 ** 2 with bining 5 (0.001 is not enough)
    time.sleep(0.005)
    raw_img.append(data)
cam_ang.stop()
cam_ang.flush()
cam_ang.close()

images = []
for img in raw_img:
    images.append(cam_ang.decode_image(img)[0])
images = np.asarray(images)
images = np.rot90(images, 1, axes=(1,2))

imwrite("angular.tif", images)

daisychain.CloseConnection()

