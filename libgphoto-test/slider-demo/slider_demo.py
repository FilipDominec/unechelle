#!/usr/bin/python3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import collections

fig, (ax1, ax2) = plt.subplots(1,2)
fig.subplots_adjust(left=0.05, right=0.95, bottom=0.27, top=0.99, hspace=0)

## == static settings & built-in constants ==
t = np.arange(0.0, 1.0, 1e-4) # x-axis for plotting
sensor_xsize_mm     = 24
sensor_ysize_mm     = 16
focal_distance_mm   = 125
grooves_permm       = 75
spectral_lines_major_nm   = [585.249, 614.306, 640.225, 703.241]
spectral_lines_midi_nm   =  [576.4674, 588.189,594.483, 607.434, 609.616, 616.359, 626.649, 633.443, 638.299, 650.653, 667.828, 671.704, 692.947, 724.517]
spectral_lines_minor_nm   = [581.932, 597.553, 603.000, 621.728, 630.479, 653.288, 659.895, 717.394, 743.890]
#see also http://www.astrosurf.com/buil/us/spe2/calib2/neon.dat etc.

default_params = collections.OrderedDict()
## == GUI-tunable settings ==
## (range from, range to, initial value)
default_params['first_order_number']	=	  (-20, -18, 20)
default_params['last_order_number']	=	   (-20, -6, 20)
default_params['lambda_to_y_ofs']	=	     (-5, .67, 5)
default_params['lambda_to_y_lin']	=	     (-1, -.08, 1)
default_params['lambda_to_y_quad']	=	    (-1, -0.03, 1)
default_params['lambda_to_y_cub']	=	     (-1, 0, 1)
default_params['lambda_to_y_quart']	=	   (-1, 0, 1)
default_params['x_to_lambda_ofs']	=	     (-1, .335, 1)
default_params['x_to_lambda_lin']	=	     (-1, -.05, 1)
default_params['x_to_lambda_quad']	=	    (-1, 0, 1)


## == functions defining the geometrical transformation (x->grating, y->prism) ==

def p(pname): return paramsliders[pname].val
def x_to_lambda(xx, difrorder):
    return difrorder*(p('x_to_lambda_ofs') + xx*p('x_to_lambda_lin') + xx**2*p('x_to_lambda_quad'))
def lambda_to_y(lam):
    return p('lambda_to_y_ofs') + lam*p('lambda_to_y_lin') + lam**2*p('lambda_to_y_quad') + \
            lam**3*p('lambda_to_y_cub') + lam**4*p('lambda_to_y_quart')


## == User interaction ==

def update(val): ## update plots on manual parameter tuning
    # TODO define correct function:
    # starting
    lineindex = 0
    for difrorder in range(int(p('first_order_number')), int(p('last_order_number')+1)):
        yy = lambda_to_y(x_to_lambda(x,difrorder))
        lines[lineindex].set_ydata(yy)
        lineindex+=1
    fig.canvas.draw_idle()
paramsliders = {}
sliderheight, sliderpos = .02, .02
for key,item in list(default_params.items())[::-1]:
    paramsliders[key] = matplotlib.widgets.Slider(plt.axes([0.25, sliderpos, 0.65, sliderheight]), key, item[0], item[2], valinit=item[1])
    paramsliders[key].on_changed(update)
    sliderpos += sliderheight*1.1

def reset_values(event): 
    for key,item in paramsliders.items(): item.reset()
button = matplotlib.widgets.Button(plt.axes([0.8, 0.025, 0.1, 0.04]), 'Reset', color='.7', hovercolor='.9')
button.on_clicked(reset_values)

#rax1 = plt.axes([0.025, 0.5, 0.15, 0.15])
#radio = matplotlib.widgets.RadioButtons(rax1, ('red', 'blue', 'green'), active=0)
#def colorfunc(label):
    #l.set_color(label)
    #fig.canvas.draw_idle()
#radio.on_clicked(colorfunc)



## == plotting the image == 
raw_file_name = '../image_logs/output_debayered_.1s_ISO100_.cr2'
from rawkit.raw import Raw
from rawkit.options import interpolation
raw_image = Raw(filename=raw_file_name)
raw_image.options.interpolation = interpolation.amaze # or "amaze", see https://rawkit.readthedocs.io/en/latest/api/rawkit.html
#raw_image_process = raw_image.process()
#if raw_image_process == raw_image: print("they are identical")
npimage = np.array(raw_image.raw_image(include_margin=False)) # returns: 2D np. array
print(npimage.shape) ## gives 1-d array of values
ax1.imshow((npimage-np.min(npimage)*.9)**.1, extent=[0,1,0,1],cmap=matplotlib.cm.gist_earth_r)

## == plotting the diffr orders == 
x = np.linspace(0,1,10) # image pixel range to analyze
lines = []
for difrorder in range(int(p('first_order_number')), int(p('last_order_number')+1)):
    yy = lambda_to_y(x_to_lambda(x,difrorder))
    print('plotting line', difrorder, 'with data x,y=', x, yy)
    ll = ax1.plot(x, yy, lw=1) ## , color='red'
    print(ll)
    lines.append(ll[0])
#plt.axis([0, 1, -10, 10])

print('test', lambda_to_x(x_to_lambda(a,1),1))
print('test', x_to_lambda(lambda_to_x(a,1),1))
plt.show()
