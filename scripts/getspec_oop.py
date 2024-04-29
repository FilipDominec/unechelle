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
cfg.get_child_by_name('shutterspeed').set_value('2')
cfg.get_child_by_name('iso').set_value('100')
camera.set_config(cfg)

a = camera.capture_preview() 
a.save(name + '_rawdata.cr2')
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


#camera.set_single_config('shutterspeed', '30') # ??? , camera_config

#camera.set_single_config('iso', cfg.get_child_by_name('iso')) # ???

# doesnt' work, missing 3rd arg ??:
#camera.set_single_config('shutterspeed', "1/500")

# does nothing:
#cfg.get_child_by_name("shutterspeed").set_value("1/500")
#print(cfg.get_child_by_name("shutterspeed").get_value())
#camera.set_config(cfg)
#cfg = camera.get_config()  # ideally, `copy(cfg0)`, but "can't pickle CameraWidget object"
#cfg.get_child_by_name("shutterspeed").set_value("1/500")
#print(cfg.get_child_by_name("shutterspeed").get_value())
#camera.set_config(cfg)

## --- raw file demosaic ---
import rawpy
#name = '2024-04-29_142117' # XXX debug only if camera not available
with rawpy.imread(name + '_rawdata.cr2') as raw:
    print(raw)
    rgb = raw.postprocess(demosaic_algorithm=0, gamma=(1,1), no_auto_bright=True, output_bps=16)
    print(rgb)
    print(rgb.shape)
#import imageio
#imageio.imsave('linear.tiff', rgb)



# TODO disable "manual focus drive" somehow to prevent delays & fails ?
# bash command with "--capture-tethered works perfectly" or fails randomly too ?
#   suggest simple use case (w/ settings) on https://github.com/jim-easterbrook/python-gphoto2

## --- interactive plotting ---
import matplotlib.pyplot as plt
plt.imshow(rgb)
plt.show()

## --- demosaic tweaking ---
#imageformat_cfg = cfg.get_child_by_name('imageformat')
#imageformat = imageformat_cfg.get_value()
#print('imageformat', imageformat)
#imageformat_cfg.set_value('RAW') #imageformat_cfg.set_value('Small Fine JPEG')
#camera.set_config(cfg)
#rawArray = raw.postprocess(demosaic_algorithm=rawpy.DemosaicAlgorithm.Linear,
                                   #half_size=True,no_auto_bright=True, output_bps=16,
                                   #four_color_rgb=False
                                   #)

                                   #output_color=rawpy.ColorSpace.raw,
                                   #output_bps=16,user_flip=None,
                                   #user_black=None,user_sat=None,
                                   #no_auto_bright=False,auto_bright_thr=0.01,
                                   #adjust_maximum_thr=0,bright=100.0,
                                   #highlight_mode=rawpy.HighlightMode.Ignore,
                                   #exp_shift=None,exp_preserve_highlights=0.0,
                                   #no_auto_scale=True,gamma=(2.222, 4.5),
                                   #chromatic_aberration=None,
                                   #bad_pixels_path=None)
#rgb = raw.postprocess(gamma=(1,1)) 
#print(rgb)
#
