#!/usr/bin/python3  
#-*- coding: utf-8 -*-

## Import common moduli

import datetime
import gphoto2 as gp
import numpy as np
import time

name = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S') # unix-convenient date format (not exactly ISO8601)



## -- capture raw image ---
camera = gp.Camera()
camera.init() # not needed?
cfg = camera.get_config()

cfg.get_child_by_name('imageformat').set_value('RAW 2')
cfg.get_child_by_name('capturesizeclass').set_value('Full Image')
print(cfg.get_child_by_name("shutterspeed").get_value())
cfg.get_child_by_name('shutterspeed').set_value('2')
print(cfg.get_child_by_name("shutterspeed").get_value())
cfg.get_child_by_name('iso').set_value('100')
camera.set_config(cfg)

a = camera.capture_preview() 


a.save(name + '_rawdata.cr2') # WORKS


#import io
#buf = io.BytesIO()
#a.save(buf)
#b_image = buf.getvalue()


#
#rawArray = raw.postprocess(gamma=(1,1), no_auto_bright=True, output_bps=16)
#rawArray = np.sum(rawArray, axis=2) # merge one RGBG cell, making monochrome img
#print(rawArray.shape, np.max(rawArray), np.mean(rawArray) )




### start anew to make new config work - and this should not be neccessary
#cfg.get_child_by_name('imageformat').set_value('RAW 2')
#cfg.get_child_by_name('capturesizeclass').set_value('Full Image')
#cfg.get_child_by_name('shutterspeed').set_value('2') #cfg.get_child_by_name('shutterspeed').set_value('1/100')
#cfg.get_child_by_name('iso').set_value('1600')
#camera.set_config(cfg)
#for x in range(10):
    #b = camera.capture_preview(); 
    #time.sleep(.001) # if it hangs - add some 1 sec delay?
#b.save(name + '_rawdata.cr2')




#camera.exit()


#my_set(name='imageformat', value='RAW')
#my_set(name='iso', value='{}'.format(iso))
#my_set(name='iso', value='1600') # does '3200' offer advantage over '1600' ?
#my_set(name='shutterspeed', value='30')
#my_set(name='shutterspeed', value='1/10')


# does nothing:
#cfg.get_child_by_name("shutterspeed").set_value("1/500")
#print(cfg.get_child_by_name("shutterspeed").get_value())
#camera.set_config(cfg)
#cfg = camera.get_config()  # ideally, `copy(cfg0)`, but "can't pickle CameraWidget object"
#cfg.get_child_by_name("shutterspeed").set_value("1/500")
#camera.set_config(cfg)

## --- raw file demosaic ---
import rawpy
#name = '2024-04-29_142117' # XXX debug only if camera not available
with rawpy.imread(name + '_rawdata.cr2') as raw: # TODO use open_buffer
    #print(raw)
    #rgb = raw.postprocess(demosaic_algorithm=0, gamma=(1,1), no_auto_bright=True, output_bps=16)
    #print(rgb)
    #print(rgb.shape)

    pixels = raw.raw_image_visible.copy() # note the dtype is uint16, and that numpy does not check for under/overflows 
#import imageio
#imageio.imsave('linear.tiff', rgb)



# TODO disable "manual focus drive" somehow to prevent delays & fails ?
# bash command with "--capture-tethered works perfectly" or fails randomly too ?
#   suggest simple use case (w/ settings) on https://github.com/jim-easterbrook/python-gphoto2

## --- interactive plotting ---

import matplotlib.pyplot as plt
minclip = 270
pixels = np.clip(pixels, minclip, 1000000) - minclip
pixels = (pixels/4096.)**.3

print(np.min(pixels), np.max(pixels))
plt.imshow(pixels, clim=(0, 1), cmap='inferno') #    vmin=-0.01, vmax=1
plt.show()

