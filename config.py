
from andor3 import Andor3

# Platform configs
z_ini = 0       # focused at 6.87 mm
x_ini = 9.5       # middle at 9.5 mm, put it 9 for involving x movement.
# velo_z = 0.45  # It seems to me with this is the just right speed for 100 frames in 0.5 mm step size while Python wait 5 ms. Compare to 0.4 and 0.5.
velo_z = 1

# Camera configs
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
        # camera.FrameCount = 3300
        camera.SimplePreAmpGainControl = "16-bit (low noise & high well capacity)"
        camera.PixelReadoutRate = "280 MHz"
        camera.PixelEncoding = "Mono16"
        camera.CycleMode = "Fixed"
        camera.SensorCooling = True
        camera.AuxiliaryOutSource = "FireAny"

        # ROI settomg
        camera.AOIHeight = 250
        camera.AOITop = 700      #? The "Top" might be typo, it seems work as "bottom" in the Solis.
        camera.AOIWidth = 250
        camera.AOILeft = 1600
        camera.AOIHBin = 2
        camera.AOIVBin = 2

        #? When trigger mode is in Software, the frame rate did not make sense. The frame will be triggered whenever the command is sent.
        # camera.FrameRate = 100

    else:
        print("Input is not an Andor camera.")