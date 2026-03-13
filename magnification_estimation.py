import numpy as np
from tifffile import imread
import matplotlib.pyplot as plt
import cv2


def rotate_image(image, angle):
    # Get image dimensions
    h, w = image.shape[:2]

    # Calculate rotation matrix around the center
    center = (w / 2, h / 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Apply affine transformation
    rotated = cv2.warpAffine(image, rotation_matrix, (w, h))
    return rotated


if __name__ == "__main__":
    """ The files are under 20250806-back2narrowFOV folder."""
    obj_s = 1 / 2 / 1.1 * 1e-3

    spa = imread('spa_mag.tif')
    spa = rotate_image(spa, -1.05)
    spa_his = np.sum(spa, 1) / 1e8
    spa_fft = np.fft.fft(spa_his)
    spa_cyc = np.argmax(np.abs(spa_fft)[1:len(spa_his)//2]**2) + 1
    spa_period = len(spa_his) / spa_cyc
    spa_strip = 6.5 * 1e-6 * spa_period / 2
    Msap = spa_strip / obj_s    # 3.6608
    # ! ???
    # 1.2 just roughly estimate the FWHM.
    1.2 / spa_period / 2
    # from auto completion, have no clue what it is
    rMsap = 2 * 6.5 * 1e-6 / spa_strip / spa_cyc * Msap

    ang_vig = imread('ang_vignetting.tif')
    ang_flat = imread('ang_flat_frame.tif')
    ang = ang_vig * np.mean(ang_flat) / ang_flat
    ang = ang[160:450, 300:500]
    ang = rotate_image(ang, 0.85)
    ang_his = np.sum(ang, 1) / 1e7
    ang_fft = np.fft.fft(ang_his)
    ang_cyc = np.argmax(np.abs(ang_fft)[1:len(ang_his)//2]**2) + 1
    ang_period = len(ang_his) / ang_cyc
    ang_strip = 6.5 * 1e-6 * ang_period / 2
    Mang = ang_strip / obj_s    # 0.4147
    # ! ???
    # 1.5 just roughly estimate the FWHM.
    1.5 / ang_period / 2
    rMang = 2 * 6.5 * 1e-6 / ang_strip / ang_cyc * Mang

    """
    obj_s = 1 / 2 / 1.1 * 1e-3
    
    spa = imread('spa_mag.tif')
    spa = rotate_image(spa, -1)
    spa_gra = np.gradient(np.sum(spa, -1)) / 1e7
    spa_gra = spa_gra[213:2337]
    spa_blur = sum(abs(spa_gra) > 1e-1) * 6.5 * 1e-6 / 9
    spa_im_s = np.sum(abs(spa_gra) < 1e-1) * 6.5 * 1e-6 / 8
    Mspa = spa_im_s / obj_s
    rMspa = 2 * spa_blur / spa_im_s * Mspa
    print('Spatial magnification:', Mspa, '±', rMspa)
    print('Relative spatial mag. error:', rMspa / Mspa * 100, '%')
    
    ang = imread('ang_mag.tif')
    ang = rotate_image(ang, 0.85)
    ang_gra = np.gradient(np.sum(ang, 1)) / 1e6
    ang_gra = ang_gra
    ang_blur = sum(abs(ang_gra) > 1e-1) * 6.5 * 1e-6 / 9
    ang_im_s = np.sum(abs(ang_gra) < 1e-1) * 6.5 * 1e-6 / 8
    Mang = ang_im_s / obj_s
    rMang = 2 * ang_blur / ang_im_s * Mang
    print('Angular magnification:', Mang, '±', rMang)
    print('Relative angular mag. error:', rMang / Mang * 100, '%')

    """

