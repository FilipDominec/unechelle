#!/usr/bin/python3  
#-*- coding: utf-8 -*-

## Import common moduli

import datetime
import gphoto2 as gp # camera control
import io
import numpy as np
import rawpy # because libraw and RawKit are obsolete/defunct as of 2024
import time



## -- capture raw image ---

def capture(camera=None, shutterspeed='1/500', iso='100', save_to_rawfile=None, raw_format=False):
    """
    Returns a tuple: image and the camera instance
    """
    # Get data, or exit gracefully
    try:
        if not camera:
            camera = gp.Camera()
            camera.init() 

        cfg = camera.get_config()
        cfg.get_child_by_name('imageformat').set_value('RAW 2')
        cfg.get_child_by_name('capturesizeclass').set_value('Full Image')
        cfg.get_child_by_name('shutterspeed').set_value('1/50') # typically '1' or '0.5' or '1/10' etc. according to menu, use: gphoto2 --list-all-config
        cfg.get_child_by_name('iso').set_value('100') # use '100', '200', '400', '800' or '1600' only for 350D
        camera.set_config(cfg)

        camera_file = gp.check_result(gp.gp_camera_capture_preview(camera))
        file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

    except gp.GPhoto2Error:
        print('\nWarning: Camera not available')
        return None, None

    # Optionally save data for further debug
    if save_to_rawfile is True:
        name = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S') # unix-convenient date format (not exactly ISO8601)
        file_data.save(save_to_rawfile) 
    elif isinstance(save_to_rawfile, str):
        file_data.save(save_to_rawfile) 

    if raw_format:
        return io.BytesIO(file_data), camera
    else:
        # raw data extraction from CR2 into a numpy array
        # Note that the obtained dtype is uint16 (ranging from 0 to 4095 for canon 350D)
        # and for this data type numpy does not check for under/overflows.
        return rawpy.imread(io.BytesIO(file_data)).raw_image_visible.copy(), camera

def load(filename):
    return rawpy.imread(filename).raw_image_visible.copy() # debug only if camera not available




def rm_background(pixels):
    minclip = np.min(pixels[200:-200, 200:-200])
    return np.clip(pixels, minclip, 1000000) - minclip

## --- interactive plotting ---

if __name__ == '__main__':
    try:
        camera = gp.Camera()
        camera.init() # not needed?
        pixels = capture(camera, rm_background=1)
        camera.exit()
    except gp.GPhoto2Error:
        print('\n\nCamera not available')
        default_image = "../image_logs/output_debayered_.1s_ISO100_.cr2"
        pixels = load(default_image)


    import matplotlib.pyplot as plt
    pixels = rm_background(pixels)
    plt.imshow((pixels/4096.)**.13) #, clim=(0, 1), cmap='inferno') #    vmin=-0.01, vmax=1
    print('min, max = ', np.min(pixels), np.max(pixels))
    plt.show()


# ==== REMARKS ==== 
#a = camera.capture_preview()  # alternate capture command, why? 

# (todo:) disable "manual focus drive" somehow to prevent delays & fails ?
# bash command with "--capture-tethered works perfectly" or fails randomly too ?
#   suggest simple use case (w/ settings) on https://github.com/jim-easterbrook/python-gphoto2

