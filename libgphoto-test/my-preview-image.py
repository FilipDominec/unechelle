#!/usr/bin/python3

# python-gphoto2 - Python interface to libgphoto2
# http://github.com/jim-easterbrook/python-gphoto2
# Copyright (C) 2015-17  Jim Easterbrook  jim@jim-easterbrook.me.uk
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

from __future__ import print_function

import io
import logging
import os
import subprocess
import sys
import numpy as np

from PIL import Image

import gphoto2 as gp

def main():
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    gp.check_result(gp.use_python_logging())
    camera = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(camera))
    # required configuration will depend on camera type!
    print('Checking camera config')
    # get configuration tree
    config = gp.check_result(gp.gp_camera_get_config(camera))

    # TODO  get the list of 'gp_abilities_list_get_abilities' or something like that ? 
    #  --> find out how to set image format
    #  --> also use it to set shutter and ISO
    def my_set(name, value):
        OK, widget = gp.gp_widget_get_child_by_name(config, name)
        if OK >= gp.GP_OK:
            widget_type = gp.check_result(gp.gp_widget_get_type(widget))
            gp.check_result(gp.gp_widget_set_value(widget, value))
            gp.check_result(gp.gp_camera_set_config(camera, config))
        else:
            print("Error setting value %s for %s using widget %s" % (value, name, widget))
    my_set(name='imageformat', value='Large Fine JPEG')
    my_set(name='shutterspeed', value='1')
    #my_set(name='imageformat', value='RAW') ## TODO now working yet

    # TODO my_get and find out how fractions of second are specified!


    # find the image format config item
    OK, image_format = gp.gp_widget_get_child_by_name(config, 'imageformat')
    if OK >= gp.GP_OK:
        # get current setting
        imgformat = gp.check_result(gp.gp_widget_get_value(image_format))
        print('image_format = ', imgformat)
        # make sure it's not raw
        if 'raw' in imgformat.lower(): print('FIXME Cannot preview raw images')
            #return 1

    # find the capture size class config item
    # need to set this on my Canon 350d to get preview to work at all
    OK, capture_size_class = gp.gp_widget_get_child_by_name(config, 'capturesizeclass')
    if OK >= gp.GP_OK:
        # set value
        value = gp.check_result(gp.gp_widget_get_choice(capture_size_class, 2))
        gp.check_result(gp.gp_widget_set_value(capture_size_class, value))
        # set config
        gp.check_result(gp.gp_camera_set_config(camera, config))
    # capture preview image (not saved to camera memory card)
    print('Capturing preview image')
    camera_file = gp.check_result(gp.gp_camera_capture_preview(camera))
    file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))


    # display image
    data = memoryview(file_data)
    print(type(data), len(data))
    print(data[:10].tolist())
    if 'raw' in imgformat.lower():
        #rawimage = open(io.BytesIO(file_data))
        ## FIXME raw format would be more accurate than JPEG, but  AttributeError: '_io.BytesIO' object has no attribute 'encode'
        from rawkit import raw
        raw_image_process = raw.Raw(io.BytesIO(file_data))
        buffered_image = numpy.array(raw_image_process.to_buffer())
        print(buffered_image.shape)
    else:
        image = Image.open(io.BytesIO(file_data))
        npimage = np.array(image)
        print(image, npimage)
        #image.show()
        from scipy import ndimage 
        import matplotlib.pyplot as plt
        plt.imshow(npimage)
        plt.plot([200,500], [300,-100], lw=5, c='k')
        plt.show()



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
