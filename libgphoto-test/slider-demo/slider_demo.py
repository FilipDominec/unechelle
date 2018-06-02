#!/usr/bin/python3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import collections

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.25, bottom=0.25)

## == static settings & built-in constants ==
t = np.arange(0.0, 1.0, 1e-4) # x-axis for plotting
default_params = collections.OrderedDict()
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


## == User interaction ==

def update(val): ## update plots on manual parameter tuning
    # TODO define correct function:
    # starting
    lineindex = 0
    for difrorder in range(int(p('first_order_number')), int(p('last_order_number')+1)):
        yy = lambda_to_y(x_to_lambda(x,difrorder))
        print(x,yy)
        lines[lineindex].set_ydata(yy)
        lineindex+=1
    fig.canvas.draw_idle()

paramsliders = {}
sliderheight, sliderpos = .02, .02
for key,item in default_params.items():
    paramsliders[key] = matplotlib.widgets.Slider(plt.axes([0.25, sliderpos, 0.65, sliderheight]), key, item[0], item[2], valinit=item[1])
    paramsliders[key].on_changed(update)
    sliderpos += sliderheight*1.1

def reset(event): 
    for key,item in paramsliders.items(): item.reset()

button = matplotlib.widgets.Button(plt.axes([0.8, 0.025, 0.1, 0.04]), 'Reset', color='.7', hovercolor='.9')
button.on_clicked(reset)

#rax = plt.axes([0.025, 0.5, 0.15, 0.15])
#radio = matplotlib.widgets.RadioButtons(rax, ('red', 'blue', 'green'), active=0)
#def colorfunc(label):
    #l.set_color(label)
    #fig.canvas.draw_idle()
#radio.on_clicked(colorfunc)


## == functions defining the geometrical transformation (x->grating, y->prism) ==
def p(pname): return paramsliders[pname].val
def x_to_lambda(xx, difrorder):
    return difrorder*(p('x_to_lambda_ofs') + xx*p('x_to_lambda_lin') + xx**2*p('x_to_lambda_quad'))
def lambda_to_y(lam):
    return p('lambda_to_y_ofs') + lam*p('lambda_to_y_lin') + lam**2*p('lambda_to_y_quad')


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
ax.imshow((npimage-np.min(npimage)*.9)**.1, extent=[0,1,0,1],cmap=matplotlib.cm.gist_earth_r)

## == plotting the diffr orders == 
x = np.linspace(0,1,10) # image pixel range to analyze
lines = []
for difrorder in range(int(p('first_order_number')), int(p('last_order_number')+1)):
    yy = lambda_to_y(x_to_lambda(x,difrorder))
    print('plotting line', difrorder, 'with data x,y=', x, yy)
    ll = ax.plot(x, yy, lw=1) ## , color='red'
    print(ll)
    lines.append(ll[0])
#plt.axis([0, 1, -10, 10])

plt.show()
