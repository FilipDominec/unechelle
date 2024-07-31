#!/usr/bin/python3  
#-*- coding: utf-8 -*-

## Import common moduli

import datetime
import gphoto2 as gp
import io
import numpy as np
import rawpy # because libraw is defunct as of 2024
import time




## -- capture raw image ---
camera = gp.Camera()
camera.init() # not needed?
cfg = camera.get_config()

cfg.get_child_by_name('imageformat').set_value('RAW 2')
cfg.get_child_by_name('capturesizeclass').set_value('Full Image')
cfg.get_child_by_name('shutterspeed').set_value('1/500') # typically '1' or '0.5' or '1/10' etc. according to menu, use: gphoto2 --list-all-config
cfg.get_child_by_name('iso').set_value('100') # use '100', '200', '400', '800' or '1600' only for 350D
camera.set_config(cfg)

#name = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S') # unix-convenient date format (not exactly ISO8601)
#a.save(name + '_rawdata.cr2') # for debug - save data

camera_file = gp.check_result(gp.gp_camera_capture_preview(camera))
file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

#camera_file = gp.check_result(gp.gp_camera_capture_preview(camera))
#file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))

camera.exit()



## --- raw data exctraction from CR2 into a numpy array ---

#name = '2024-04-29_142117' 
#with rawpy.imread(name + '_rawdata.cr2') as raw: # debug only if camera not available
with rawpy.imread(io.BytesIO(file_data)) as raw:  # saves no data on harddrive
    # note that the obtained dtype is uint16, ranging up to 2**12 for canon 350D, 
    # and that numpy does not check for under/overflows 
    pixels = raw.raw_image_visible.copy() 


## --- interactive plotting ---

import matplotlib.pyplot as plt

minclip = np.min(pixels[200:-200, 200:-200])

pixels = np.clip(pixels, minclip, 1000000) - minclip
pixels = (pixels/4096.)**.3

print(np.min(pixels), np.max(pixels))
plt.imshow(pixels, clim=(0, 1), cmap='inferno') #    vmin=-0.01, vmax=1
plt.show()


# ==== REMARKS ==== 
#a = camera.capture_preview()  # alternate capture command, why? 

# (todo:) disable "manual focus drive" somehow to prevent delays & fails ?
# bash command with "--capture-tethered works perfectly" or fails randomly too ?
#   suggest simple use case (w/ settings) on https://github.com/jim-easterbrook/python-gphoto2

