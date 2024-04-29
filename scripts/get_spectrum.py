#!/usr/bin/python3

# python-gphoto2 - Python interface to libgphoto2
# http://github.com/jim-easterbrook/python-gphoto2
# Adapted from the example by
# Copyright (C) 2015-17  Jim Easterbrook  jim@jim-easterbrook.me.uk
# by
# Copyright (C) 2018-   
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import logging
import os
import subprocess
import sys
import numpy as np
import time

import gphoto2 as gp

from PIL import Image
from scipy import ndimage 
#import matplotlib.pyplot as plt

shutterspeed    = sys.argv[1] if len(sys.argv)>1 else 3
iso             = sys.argv[2] if len(sys.argv)>2 else 100
comment         = sys.argv[3] if len(sys.argv)>3 else ''
## Make sure your camera has configuration: "PC Connection", not "PTP mode" - that wouldn't work

#def get_img(camera, imageformat='RAW', shutterspeed=shutterspeed, iso=iso)
def main():
    t0 = time.time()
    logging.basicConfig( format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    gp.check_result(gp.use_python_logging())
    print('Establishing communication with the camera (wait few seconds)')
    camera = gp.check_result(gp.gp_camera_new())

    gp.check_result(gp.gp_camera_init(camera)) # unnecessary ?

    # required configuration will depend on camera type!
    config = gp.check_result(gp.gp_camera_get_config(camera))
    print(time.time()-t0, 'Camera ready', config)

    # TODO  get the list of 'gp_abilities_list_get_abilities' or something like that ? 
    #  --> find out how to set image format
    #  --> also use it to set shutter and ISO
    def my_set(name, value):
        OK, widget = gp.gp_widget_get_child_by_name(config, name)
        if OK >= gp.GP_OK:
            widget_type = gp.check_result(gp.gp_widget_get_type(widget))
            gp.check_result(gp.gp_widget_set_value(widget, value))
            print(gp.check_result(gp.gp_camera_set_config(camera, config)))
        else:
            print("Error setting value %s for %s using widget %s, result = %s" % (value, name, widget, OK))
    #my_set(name='imageformat', value='Large Fine JPEG')
    my_set(name='imageformat', value='RAW2')
    my_set(name='imageformat', value='RAW')

    #my_set(name='iso', value='{}'.format(iso))
    my_set(name='iso', value='1600') # does '3200' offer advantage over '1600' ?

    #my_set(name='shutterspeed', value='30')
    my_set(name='shutterspeed', value='1/10')

    #my_set(name='shutterspeed', value='{}'.format(shutterspeed))
    #for s in ('1/10','1/100'):
    #my_set(name='shutterspeed', value=s)

    # find the image format config item
    OK, image_format = gp.gp_widget_get_child_by_name(config, 'imageformat')
    if OK >= gp.GP_OK:
        imgformat = gp.check_result(gp.gp_widget_get_value(image_format))

    # find the capture size class config item
    # need to set this on my Canon 350d to get preview to work at all
    OK, capture_size_class = gp.gp_widget_get_child_by_name(config, 'capturesizeclass')
    if OK >= gp.GP_OK:
        value = gp.check_result(gp.gp_widget_get_choice(capture_size_class, 2))
        gp.check_result(gp.gp_widget_set_value(capture_size_class, value)) 
        gp.check_result(gp.gp_camera_set_config(camera, config)) 

    # capture preview image (not saved to camera memory card)
    print(time.time()-t0, 'Capturing preview image')

    camera_file = gp.check_result(gp.gp_camera_capture_preview(camera)) # takes 2.2s + shutter
    print(time.time()-t0, ' p f')
    file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))
    print(time.time()-t0, '01----------', type(file_data),file_data)


    ## TEST
    # find the capture target config item
    capture_target = gp.check_result(gp.gp_widget_get_child_by_name(config, 'capturetarget'))
    # print current setting
    value = gp.check_result(gp.gp_widget_get_value(capture_target))
    print('Current setting:', value)
    # print possible settings
    for n in range(gp.check_result(gp.gp_widget_count_choices(capture_target))):
        choice = gp.check_result(gp.gp_widget_get_choice(capture_target, n))
        print('Choice:', n, choice)
    # clean up
    gp.check_result(gp.gp_camera_exit(camera))

    #After getting the .jpg file you need to call gp_camera_wait_for_event until you get a GP_EVENT_FILE_ADDED event. 
    # The event data is the path of the .cr2 file which you can then fetch with gp_camera_file_get.

    # display image
    data = memoryview(file_data)
    print(time.time()-t0, '02----------', type(data), data)
    print('    ', len(data))
    print(data[:10].tolist())
    if 'raw' in imgformat.lower():
        #rawimage = open(io.BytesIO(file_data))
        ## FIXME raw format would be more accurate than JPEG, but  AttributeError: '_io.BytesIO' object has no attribute 'encode'
        #xx from rawkit import raw
        #xx raw_image_process = raw.Raw(io.BytesIO(file_data))

        #import rawpy
        #raw = rawpy.imread(bytesio)
        #rgb = raw.postprocess()

        #bytesio = io.BytesIO(file_data)
        #print('bytesio', bytesio)
        raw_file_name = 'image_logs/output_debayered_{}s_ISO{}_{}.cr2'.format(str(shutterspeed).replace('/','div'), iso, comment)
        gp.gp_file_save(camera_file, raw_file_name)

        # Note that - if Canon cameras are used - the dependency on rawkit can be replaced with a dedicated parser
        #https://codereview.stackexchange.com/questions/75374/cr2-raw-image-file-parser-in-python-3

        from rawkit.raw import Raw
        from rawkit.options import interpolation
        raw_image = Raw(filename=raw_file_name)
                # 'bayer_data', 'close', 'color', 'color_description', 'color_filter_array', 'data', 
                # 'image_unpacked', 'libraw', 'metadata', 'options', 'process', 'raw_image', 'save', 
                # 'save_thumb', 'thumb_unpacked', 'thumbnail_to_buffer', 'to_buffer', 'unpack', 'unpack_thumb'
        #raw_image.options.interpolation = interpolation.linear # or "amaze", see https://rawkit.readthedocs.io/en/latest/api/rawkit.html
        raw_image.options.interpolation = interpolation.amaze # or "amaze", see https://rawkit.readthedocs.io/en/latest/api/rawkit.html

        raw_image.save("output-test.ppm") ## FIXME - saved ppm image has auto-normalized brightness, why?

        raw_image_process = raw_image.process()
        if raw_image_process is raw_image: print("they are identical")

        #from rawkit.raw import Raw
        #from rawkit.options import WhiteBalance
        #with Raw(filename='some/raw/image.CR2') as raw:
          #raw.options.white_balance = WhiteBalance(camera=False, auto=True)
          #raw.save(filename='some/destination/image.ppm')

        ## FIXME - 
        npimage = np.array(raw_image.raw_image(include_margin=False)) # returns: 2D np. array
        #print('bayer_data', raw_image.bayer_data()) #  ? 
        #print('as_array', raw_image.as_array()) # does not exist, although documented??
        #print(type(raw_image.to_buffer())) # Convert the image to an RGB buffer. Return type:	bytearray

        #npimage = np.array(flat_list).reshape(4)
        print(npimage) ## gives 1-d array of values
        print(npimage.shape) ## gives 1-d array of values

        #plt.imshow(npimage)
        #plt.hist(npimage.flatten(), 4096)
        #plt.plot([200,500], [300,-100], lw=5, c='r')
        #plt.show()

        ## Save the raw pixels
        try: import cPickle as pickle
        except: import pickle

        print('retrieved image as numpy array with dimensions:', npimage.shape)

        #scipy.ndimage.
        print('', )
        print('', )

        print(npimage.shape)
    else:
        image = Image.open(io.BytesIO(file_data))
        npimage = np.array(image)
        return npimage 
        print('retrieved image as numpy array with dimensions:', npimage.shape)
        #image.show()
        #plt.imshow(npimage)
        #plt.plot([200,500], [300,-100], lw=5, c='k')
        #plt.show()



        # TODO  http://www.scipy-lectures.org/advanced/image_processing/#blurring-smoothing
        # display with polynomially curved paths, 
        # linear convolve, 
        # linearize along the paths, (possibly subtract background?)
        # generate polynomial x-axis
        # stitch smoothly
    gp.check_result(gp.gp_camera_exit(camera))
    return 0

if __name__ == "__main__":
    sys.exit(main())

""" 
Troubleshooting 2022


### fails with ```gphoto2.GPhoto2Error: [-105] Unknown model```

Install fresh version of gphoto2:

    sudo snap install gphoto2


### fails with ```ImportError: Unsupported Libraw version: 0.19.5```

"it appears rawkit has gone unmaintained"

To fix it, edit /usr/local/lib/python3.8/dist-packages/libraw/bindings.py according to https://github.com/mateusz-michalik/cr2-to-jpg/issues/4

That is, duplicate the line starting "18:", and make it "19:". And add "20:" ... etc.


### Rawkit is hard to use

"It may be easier if you use rawpy" https://stackoverflow.com/questions/45704689/opencv-and-rawkit-python#45721804

    raw = rawpy.imread("path/to/file") # access to the RAW image
    rgb = raw.postprocess() # a numpy RGB array


 D350 = 22.2 x 14.8 mm CMOS
"""


