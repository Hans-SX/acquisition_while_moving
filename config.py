
from andor3 import Andor3
"""For re-aligned setup."""

# Platform configs
z_ini = 6.8       # focused at 8.8 mm, range from 0 to 10 mm. More than 10, angular started to torture 
x_ini = 7.76       # middle at 7.76 mm, x movement range from 10.4 to 12.6 mm when z = 17.
# velo_z = 0.45  # It seems to me with this is the just right speed for 100 frames in 0.5 mm step size while Python wait 5 ms. Compare to 0.4 and 0.5.
velo_z = 0.1

# Camera configs
def config_andor(camera):
    if type(camera) == type(Andor3()):
        # Camera congigurations
        camera.AccumulateCount = 1
        camera.SpuriousNoiseFilter = False
        camera.StaticBlemishCorrection = False
        camera.MetadataEnable = False
        camera.TriggerMode = "Software"
        camera.ElectronicShutteringMode = "Rolling"
        camera.ExposureTime = 2.771831E-005
        # camera.FrameCount = 3300
        camera.SimplePreAmpGainControl = "16-bit (low noise & high well capacity)"
        camera.PixelReadoutRate = "280 MHz"
        camera.PixelEncoding = "Mono16"
        camera.CycleMode = "Fixed"
        camera.SensorCooling = True
        camera.AuxiliaryOutSource = "FireAny"
        camera.FanSpeed = "On"
        camera.Overlap = True                 # reduces idle time between frames where supported

        # ROI settomg
        camera.AOIHeight = 800
        camera.AOITop = 675      #? The "Top" might be typo, it seems work as "bottom" in the Solis.
        camera.AOIWidth = 800
        camera.AOILeft = 880
        camera.AOIHBin = 4
        camera.AOIVBin = 4

        #? When trigger mode is in Software, the frame rate did not make sense. The frame will be triggered whenever the command is sent.
        # camera.FrameRate = 100

    else:
        print("Input is not an Andor camera.")