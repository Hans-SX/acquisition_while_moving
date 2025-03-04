"""
Created on  Feb. 03, 2025

@author: Shih-Xian
"""

import os
from os.path import join
import time
from andor3 import Andor3
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

def config_andor(camera):
    if type(camera) == type(Andor3()):
        # Camera congigurations
        camera.AccumulateCount = 1
        camera.SpuriousNoiseFilter = False
        camera.StaticBlemishCorrection = False
        camera.MetadataEnable = True
        camera.TriggerMode = "Software"
        camera.ElectronicShutteringMode = "Rolling"
        camera.ExposureTime = 9.239437E-05
        camera.FrameCount = 3300
        camera.SimplePreAmpGainControl = "16-bit (low noise & high well capacity)"
        camera.PixelReadoutRate = "280 MHz"
        camera.PixelEncoding = "Mono16"
        camera.CycleMode = "Fixed"
        camera.SensorCooling = True
        camera.AuxiliaryOutSource = "FireAny"

        # ROI settomg
        camera.AOIHeight = 350
        camera.AOITop = 660      #? The "Top" might be typo, it seems work as "bottom" in the Solis.
        camera.AOIWidth = 350
        camera.AOILeft = 1575

        #? When trigger mode is in Software, the frame rate did not make sense. The frame will be triggered whenever the command is sent.
        # camera.FrameRate = 100

    else:
        print("Input is not an Andor camera.")

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
            # pitools.startup(self.pid2, stages='M-231.17', refmodes='FNL', servostates=True, controlmodes=0x1)
            pitools.waitontarget(self.pid1)
            # pitools.waitontarget(self.pid2)
        except:
            self.pid1.CloseConnection()
            self.pid2.CloseConnection()

    def config_platform(self, pid, init=None, velo=1):
        if init != None:
            pid.MOV('1', init)
            pitools.waitontarget(pid)
        # Set velocity
        pid.VEL('1', velo)
    
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
        
        for _ in range(fpc):
            timer.start("Acquisition cycle num " + str(cyc+1))
            cam.command("SoftwareTrigger")
            # timeout:int, in milliseconds
            data = cam.waitBuffer(timeout="INFINITY", copy=True, requeue=True)
            #! The effect of sleep 0.01 wasn't clear, other than the total time cost.
            # time.sleep(0.01)
            timer.stop("Acquisition cycle num " + str(cyc+1))
            raw_img.append(data)

        if cyc+1 % 10 == 0:
            print(str(cyc+1) + " steps finished.")
        pitools.waitontarget(pid1)
        # pitools.waitontarget(pid2)
    
    print("Sensor temperature after acquisition:", cam.SensorTemperature)
    cam.stop()
    cam.flush()
    timer.stop("Whole acquisition")

    return raw_img, timer