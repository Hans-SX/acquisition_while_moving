"""
Created on  Feb. 03, 2025

@author: Shih-Xian
"""

import os
from os.path import join
import time
from itertools import cycle
# from andor3 import Andor3
from pipython import GCSDevice
from pipython import pitools


class Timer:
    def __init__(self):
            self.start_times = {}
            self.elapsed_times = {}
    def start(self, label):
        #   self.start_times[label] = time.time()
          self.start_times[label] = time.perf_counter()
    def stop(self, label):
        if label in self.start_times:
            # elapsed_time = time.time() - self.start_times[label]
            elapsed_time = time.perf_counter() - self.start_times[label]
            self.elapsed_times[label] = elapsed_time
        else:
             print(f"Timer for {label} is not started.")
    def savefile(self, filename):
        with open(filename, 'w') as file:
            for label in self.elapsed_times:
                file.write(f"{label}, {self.elapsed_times[label]}\n")

def save_config_andor(cam, name, expdate):
    # To see details about avaliable camera features, such as data type and valid ranges:
    exppath = join(os.getcwd(), name)
    if not os.path.exists(exppath):
        os.makedirs(exppath)
    config_name = "config_andor_" + expdate +".txt"
    config = open(join(exppath, config_name), "w")
    config.writelines(cam.describe_features())
    config.close()

class platform_DaisyChain():
    def __init__(self):
        #? First set up the dasiy chain on the master device, the one connected to the PC. Address could be any, as long as one in 1 in the chain. 
        try:
            self.pid1 = GCSDevice("C-863")
            devices = self.pid1.EnumerateUSB()       #? Returns serialnum
            self.pid1.OpenUSBDaisyChain(devices[0])
            daisychainid = self.pid1.dcid

            #? Add the devices into the dasiy chain.
            self.pid1.ConnectDaisyChainDevice(1, daisychainid)
            self.pid2 = GCSDevice("C-863")
            self.pid2.ConnectDaisyChainDevice(2, daisychainid)
        
            #? Printing the info of the connection.
            print('\n{}:\n{}'.format(self.pid1.GetInterfaceDescription(), self.pid1.qIDN()))
            print('\n{}:\n{}'.format(self.pid2.GetInterfaceDescription(), self.pid2.qIDN()))

            #? Set up the reference point for each actuator and control mode.
            #todo difference between different controlmodes isn't clear to me.
            #! Somehow startup did not work! After one or two test.
            pitools.startup(self.pid1, stages='M-231.17', refmodes='FNL', servostates=True, controlmodes=0x1)
            pitools.startup(self.pid2, stages='M-231.17', refmodes='FNL', servostates=True, controlmodes=0x1)
            pitools.waitontarget(self.pid1)
            pitools.waitontarget(self.pid2)
        except:
            self.pid1.CloseConnection()
            self.pid2.CloseConnection()

    def config_platform(self, pid, init=None, velo=1):
        if init != None:
            pid.MOV('1', init)
            pitools.waitontarget(pid)
        # Set velocity
        pid.VEL('1', velo)

    def execute_pattern_single_axis(self, pid, positions, timer):
        timer.start("Platform movement")
        for pos in positions:
            pid.MOV('1', pos)
            pitools.waitontarget(pid)
        timer.stop("Platform movement")
        print("Platform movement finished.")

    def execute_pattern_appx_sinusoidal(self, pid, positions, timer):
        timer.start("Platform movement")
        diff = positions[1:] - positions[:-1]
        for i in range(len(positions)):
            # start = time.perf_counter()
            pid.MOV('1', positions[i])
            pitools.waitontarget(pid)

            if i == 0:
                continue
            elif abs(diff[i-1]) < 0.25:
                time.sleep(0.5)
            elif abs(diff[i-1]) > 0.25 and abs(diff[i-1]) < 0.48:
                time.sleep(0.2)

            # dur = time.perf_counter() - start
            # if dur <= 0.5:
            #     time.sleep(0.5)
            # elif dur < 0.5/0.45 and dur > 0.5:
            #     time.sleep(0.3)

        timer.stop("Platform movement")
        print("Platform movement finished.")

    def execute_pattern_fixed_pts_x_axis(self, pid1, pos1, pid2, pos2, timer):
        """
        It is designed for the scenario which the elements of pos1 > elements of pos2.
        """
        timer.start("Platform movement")
        pos2 = cycle(pos2)

        for p1 in range(len(pos1)):
            pid1.MOV('1', pos1[p1])
            while p1 <= len(pos1):
                pitools.waitontarget(pid2)
                pid2.MOV('1', next(pos2))
                if pitools.ontarget(pid1, '1'):
                    break
            
        timer.stop("Platform movement")
        print("Platform movement finished.")
    
    def CloseConnection(self):
        self.pid1.CloseConnection()
        self.pid2.CloseConnection()

def acquisition_moving_2axes(cam, pid1, pid2, steps, dp1=1, dp2=1):
    timer = Timer()
    fpc = int(cam.FrameCount / steps)
    cam.queueBuffer()
    raw_img = []
    ini1 = pid1.qPOS()['1']
    # ini2 = pid2.qPOS()['1']

    timer.start("Whole acquisition")
    cam.start()
    for cyc in range(steps):
        #todo moving pattern depends on the need of exp.
        pid1.MOV('1', ini1 + (cyc+1)*dp1)
        # pid2.MOV('1', ini2 + (cyc+1)*dp2)
        
        timer.start("Acquisition cycle num " + str(cyc+1))
        for _ in range(fpc):
            cam.command("SoftwareTrigger")
            # timeout:int, in milliseconds
            data = cam.waitBuffer(timeout="INFINITY", copy=True, requeue=True)
            #! The effect of sleep 0.01 wasn't clear, other than the total time cost.
            #? 0.005 is enough for 1500 ** 2 with bining 5 (0.001 is not enough)
            time.sleep(0.005)
            
            raw_img.append(data)
        timer.stop("Acquisition cycle num " + str(cyc+1))   
        if cyc+1 % 10 == 0:
            print(str(cyc+1) + " steps finished.")
        pitools.waitontarget(pid1)
        # pitools.waitontarget(pid2)
    
    print("Sensor temperature after acquisition:", cam.SensorTemperature)
    cam.stop()
    cam.flush()
    timer.stop("Whole acquisition")

    return raw_img, timer, fpc

def acquisition(cam, queue, timer):
    cam.queueBuffer()
    raw_img = list()

    timer.start("Whole acquisition")
    cam.start()
    i = 0
    while not i == cam.FrameCount:
        cam.command("SoftwareTrigger")
        data = cam.waitBuffer(timeout="INFINITY", copy=True, requeue=True)
        #? 0.005 is enough for 1500 ** 2 with bining 5 (0.001 is not enough)
        time.sleep(0.005)
        
        raw_img.append(data)
        i += 1
    
    print("Sensor temperature after acquisition:", cam.SensorTemperature)
    print("Acquisition finished.")
    cam.stop()
    cam.flush()
    timer.stop("Whole acquisition")

    queue.put(raw_img)
    # return raw_img, timer

def fixed_acquisition(cam, pid1, dp1, fpc=100):
    """
    Acquiring frames at certain positions. For comparison.
    """
    timer = Timer()
    steps = int(16.5 / dp1)
    cam.FrameCount = int(fpc) * steps
    cam.queueBuffer()
    raw_img = []
    ini1 = pid1.qPOS()['1']
    # ini2 = pid2.qPOS()['1']

    timer.start("Whole acquisition")
    cam.start()
    for cyc in range(steps):
        #todo moving pattern depends on the need of exp.
        pid1.MOV('1', ini1 + (cyc+1)*dp1)
        # pid2.MOV('1', ini2 + (cyc+1)*dp2)
        
        pitools.waitontarget(pid1)
        # pitools.waitontarget(pid2)
        timer.start("Acquisition cycle num " + str(cyc+1))
        for _ in range(fpc):
            cam.command("SoftwareTrigger")
            # timeout:int, in milliseconds
            data = cam.waitBuffer(timeout="INFINITY", copy=True, requeue=True)
            #! The effect of sleep 0.01 wasn't clear, other than the total time cost.
            #? 0.005 is enough for 1500 ** 2 with bining 5 (0.001 is not enough)
            time.sleep(0.005)
            
            raw_img.append(data)
        timer.stop("Acquisition cycle num " + str(cyc+1))   
        if cyc+1 % 10 == 0:
            print(str(cyc+1) + " steps finished.")
    
    print("Sensor temperature after acquisition:", cam.SensorTemperature)
    cam.stop()
    cam.flush()
    timer.stop("Whole acquisition")

    return raw_img, timer