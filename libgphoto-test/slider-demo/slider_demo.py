#!/usr/bin/python3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import collections

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.25, bottom=0.25)

## == static settings & built-in constants ==
t = np.arange(0.0, 1.0, 0.001) # x-axis for plotting
default_params = collections.OrderedDict()
## (range from, range to, initial value)
default_params['first_order_number']	=	  (-20, -12, 20)
default_params['last_order_number']	=	   (-20, -4, 20)
default_params['lambda_to_y_ofs']	=	     (-5, 1, 5)
default_params['lambda_to_y_lin']	=	     (-1, .5, 1)
default_params['lambda_to_y_quad']	=	    (-1, .2, 1)
default_params['lambda_to_y_cub']	=	     (-1, 0, 1)
default_params['lambda_to_y_quart']	=	   (-1, 0, 1)
default_params['x_to_lambda_ofs']	=	     (-1, .1, 1)
default_params['x_to_lambda_lin']	=	     (-1, .1, 1)
default_params['x_to_lambda_quad']	=	    (-1, 0, 1)


## == User interaction ==

def update(val): ## update plots on manual parameter tuning
    # TODO define correct function:
    # starting
    lineindex = 0
    for difrorder in range(int(paramsliders['first_order_number'].val), int(paramsliders['last_order_number'].val+1)):
        yy = lambda_to_y(x_to_lambda(x,difrorder))
        print(x,yy)
        lines[lineindex].set_ydata(yy)
        lineindex+=1
    fig.canvas.draw_idle()

paramsliders = {}
sliderheight, sliderpos = .02, .02
for key,item in default_params.items():
    print('key,item', key,item)
    paramsliders[key] = matplotlib.widgets.Slider(plt.axes([0.25, sliderpos, 0.65, sliderheight]), key, item[0], item[2], valinit=item[1])
    paramsliders[key].on_changed(update)
    sliderpos+=sliderheight*1.1

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
def x_to_lambda(xx, difrorder):
    return difrorder*(paramsliders['x_to_lambda_ofs'].val + xx*paramsliders['x_to_lambda_lin'].val + xx**2*paramsliders['x_to_lambda_quad'].val)
def lambda_to_y(lam):
    return paramsliders['lambda_to_y_ofs'].val + lam*paramsliders['lambda_to_y_lin'].val + lam**2*paramsliders['lambda_to_y_quad'].val


## == plotting == 

x = np.linspace(0,1,10) # image pixel range to analyze
lines = []
for difrorder in range(int(paramsliders['first_order_number'].val), int(paramsliders['last_order_number'].val+1)):
    yy = lambda_to_y(x_to_lambda(x,difrorder))
    print('plotting line', difrorder, 'with data x,y=', x, yy)
    ll = ax.plot(x, yy, lw=2) ## , color='red'
    print(ll)
    lines.append(ll[0])
plt.axis([0, 1, -10, 10])

plt.show()
