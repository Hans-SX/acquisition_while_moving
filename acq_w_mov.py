"""
Created on  Feb. 03, 2025

@author: Shih-Xian

With andor3, https://gitlab.com/ptapping/andor3/-/tree/main
"""

import numpy as np
from tifffile import imwrite
from datetime import datetime
import argparse
import os
from os.path import join
import time
import threading, multiprocessing
import queue
from andor3 import Andor3

from utils import platform_DaisyChain, save_config_andor, fixed_acquisition, acquisition, Timer
from config import z_ini, x_ini, stepsize_z, velo_z, stepsize_x, config_andor
from moving_patterns import BigStepForward_SmallStepBack, SinusoidalForward, Refocused_range, shift

"""
Run this script within conda env cpi_tracking, under the parent folder of acquisition_while_moiving and cpi_optaxial_tracking.
It will save the data to the folder specified by --DataSet.
The folder structure is:
    |parent folder
        |acquisition_while_moving
        |cpi_optaxial_tracking
        |DataSet
--DataSet, names the folder of the acquired data.
--pattern, the pattern of the platform movement.
--steps, it should be adjust, originally it is the number of steps the platform will go through. It only apply to the linear step pattern and equal space fixed acquisition. It did not apply to BigStepForward_SmallStepBack and SinusoidalForward, bt it is used to decide the FrameCount of the camera. Not a good way to do it.
"""

if __name__ == "__main__":
    timer = Timer()
    parser = argparse.ArgumentParser()
    parser.add_argument("--DataSet", type=str)
    parser.add_argument("--steps", nargs='?', const=1, type=int)
    parser.add_argument("--pattern", nargs='?', const=1, choices=[0, 1, 2, 3, 4], type=int)
    args = parser.parse_args()

    pattern = {
                0: fixed_acquisition,
                1: BigStepForward_SmallStepBack(0, 17, 6, pattern=np.array((16, -8))).generate(),
                2: SinusoidalForward(0, 17, args.steps, frequency=3).generate(),
                3: [17],
                4: BigStepForward_SmallStepBack(0, 17, 6, pattern=np.array((16, -8))).generate()
    }
    expdate = datetime.now().strftime("_%Y_%m_%d_%H%M")

    #? Platforms configuration and Daisy chain connection.
    daisychain = platform_DaisyChain()
    pidz = daisychain.pid1
    pidx = daisychain.pid2
    daisychain.config_platform(pidz, z_ini, velo_z)  # Focus point: 7, with micrometer in 15.
    daisychain.config_platform(pidx, x_ini, velo=0.45)
    print("Daisy Chain platforms configurations done.")

    #? Camera congigurations and ROI settomg
    cam_ang = Andor3()
    print(f"{cam_ang.CameraFamily} {cam_ang.CameraModel} {cam_ang.CameraName} {cam_ang.InterfaceType}")

    config_andor(cam_ang)
    while cam_ang.SensorTemperature > 1:
        time.sleep(5)
    print("Camera configurations done.")

    print("Starting acquisition.")
    """
    Put the camera acquisition to a thread to parallel the acquisition and the platform movement. The control of PI controller and actuator is not responding while being threw into a thread.
    There must be a better way here.
    """
    if args.pattern == 1:
        #* The FrameCount of bigf_smallb is proportional to the number of 0.5 mm intervals. That's why it is the number of expected positions times 100.
        steps = len(Refocused_range(shift, pattern[1]).bigf_smallb()[1])
        cam_ang.FrameCount = steps * 100
        result_queue = queue.Queue()
        process_camera = threading.Thread(target=acquisition, args=(cam_ang, result_queue, timer,))

        process_camera.start()
        daisychain.execute_pattern_single_axis(pidz, pattern[args.pattern], timer)
        process_camera.join()
        raw_img = result_queue.get()
    elif args.pattern == 2:
        #* The FrameCount of sinusoidal may not be optimal, the current formula is follow by previous setup which has frequency = 10. When changed to freq = 3 and make the platform wait to simulate slow velocity, this should be changed. However, the result is good, lazy.
        cam_ang.FrameCount = args.steps * 100 / 2 * 3
        result_queue = queue.Queue()
        process_camera = threading.Thread(target=acquisition, args=(cam_ang, result_queue, timer,))

        process_camera.start()
        daisychain.execute_pattern_appx_sinusoidal(pidz, pattern[args.pattern], timer)
        process_camera.join()
        raw_img = result_queue.get()
    elif args.pattern == 3:
        cam_ang.FrameCount = args.steps * 100
        result_queue = queue.Queue()
        process_camera = threading.Thread(target=acquisition, args=(cam_ang, result_queue, timer,))

        process_camera.start()
        daisychain.execute_pattern_single_axis(pidz, pattern[args.pattern], timer)
        process_camera.join()
        raw_img = result_queue.get()
    elif args.pattern == 0:
        cam_ang.FrameCount = args.steps * 100
        raw_img, timer = fixed_acquisition(cam_ang, pidz, dp1=0.25)
    elif args.pattern == 4:
        posx = [9, 10]
        steps = len(Refocused_range(shift, pattern[1]).bigf_smallb()[1])
        cam_ang.FrameCount = steps * 100
        result_queue = queue.Queue()
        process_camera = threading.Thread(target=acquisition, args=(cam_ang, result_queue, timer,))

        process_camera.start()
        daisychain.execute_pattern_fixed_pts_x_axis(pidz, pattern[args.pattern], pidx, posx, timer)
        process_camera.join()
        raw_img = result_queue.get()

    save_config_andor(cam_ang, args.DataSet, expdate)

    #? Disonnect devieces.
    cam_ang.close()
    daisychain.CloseConnection()

    #? Save the images
    print("Pre processing data.")
    fpc = 100
    datapath = join(os.getcwd(), args.DataSet, "data", "angular")
    if not os.path.exists(datapath):
        os.makedirs(datapath)
    images = []
    cyc = 0
    for img in raw_img:
        images.append(cam_ang.decode_image(img)[0])
        if len(images) == fpc:
            images = np.asarray(images)
            # Orientation need to be rotated.
            images = np.rot90(images, 1, axes=(1,2))
            imwrite(join(datapath, f"angular_{cyc+1:02d}.tif"), images)
            images = []
            cyc += 1

    runtimep_name = "Runtime_profile_" + expdate + ".txt"
    timer.savefile(join(os.getcwd(), args.DataSet, runtimep_name))
    print("Acqusition done.")