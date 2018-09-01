#!/usr/bin/python3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import collections


"""
Formulation of the problem:
    * White-light collimated ray impinges (under angle α from its normal) a blazed diffraction grating (with Λ groove spacing)
    * It diffracts into multiple orders (e.g. 20-30 for an echelle grating under consideration) and 
      part of the light is collected by a digital camera (inclined by angle ξ from the grating normal, which should be
      given by finding the most efficient reflection on the blazed grating facets)
    * The camera lens has a focal length F and projects light on a CMOS/CCD sensor of width W
    * Given α, ξ, Λ, F and W, along with the selection of a integer diffraction order M,
      how does position X on the sensor translate into wavelength λ?

We know:
    * Grating equation:     
                                             sin α - sin β = Mλ/Λ,    
      where α, β are the angles of incident and diffracted rays.
    * Normalized coordinate in the middle of the sensor X = 0.5 corresponds to β = -ξ, and more generally, 
      any coordinate on sensor X ∈ {0...1} corresponds to the angle ξ of a diffracted ray as β = (0.5-X) × W / 2F  -  ξ
    * Thus we express the wavelength as
                                 λ = Λ/M × [sin α - sin((0.5-X) × W / 2F  -  ξ)]
     
TODOs:

    essential:
        updating of spectral peaks upon param change
        settings save
        spectral reduction 

    integration with hardware:
        move the actual λ-x-y conversion and into a separate module: echelle_process.py

    improvements:
        implement image convolution for smoother spectra
        HDR data composition



"""


fig, (ax1, ax2) = plt.subplots(1,2)
fig.subplots_adjust(left=0.05, right=0.95, bottom=0.30, top=0.99, hspace=0)

## == static settings & built-in constants ==
t = np.arange(0.0, 1.0, 1e-4) # x-axis for plotting
spectral_peaks_major   = np.array([585.249, 614.306, 640.225, 703.241]) / 1e9
spectral_peaks_midi   =  np.array([576.4674, 588.189,594.483, 607.434, 609.616, 616.359, 626.649, 633.443,  
        638.299, 650.653, 667.828, 671.704, 692.947, 724.517]) / 1e9
spectral_peaks_minor   = np.array([581.932, 597.553, 603.000, 621.728, 630.479, 653.288, 659.895, 717.394, 743.890]) / 1e9
#see also http://www.astrosurf.com/buil/us/spe2/calib2/neon.dat etc.


default_params = collections.OrderedDict()
## == GUI-tunable settings ==
## (range from, range to, initial value)
default_params['first_order_number']	    =	   (-20,    4, 20)
default_params['last_order_number']	    =	   (-20,    16, 20)

default_params['Λ groove spacing (μm)']	    =	   (0,  13.333, 30)
default_params['α incident angle (rad)']    =	   (-1,  .4, 1)
default_params['ξ horizontal camera inclination (rad)']  =	   (-1,  .1, 1)
default_params['F camera foc dist (mm)']    =	   (10,  150, 300)
default_params['W camera CMOS width (mm)']  =	   (1,  24, 50)

default_params['κ vertical camera declination (rad)']	    =	   (-2,    .89, 2)      ## TODO inclination/declination? 
default_params['prism_angle']	            =	   (-2,    -1.047, 2)
default_params['prism_n0']	            =	   (1,    1.38, 2)
default_params['prism_Sellmeyer_lambda0 (nm)']	=	   (50,    250, 500)
default_params['prism_Sellmeyer_F0']	    =	   (-1,    .05, 1)

## == functions defining the geometrical transformation (x->grating, y->prism) ==

def p(pname): return paramsliders[pname].val
def x_to_lambda(xx, difrorder):
    grooved = p('Λ groove spacing (μm)')       * 1e-6
    iangle  = p('α incident angle (rad)')
    cincli  = p('ξ horizontal camera inclination (rad)')
    fdist   = p('F camera foc dist (mm)')      * 1e-3
    cmosw   = p('W camera CMOS width (mm)')    * 1e-3
    #              λ = Λ/M × [sin α - sin((0.5-X) × W / 2F  -  ξ)]
    #print(" grooved , iangle  , cincli  , fdist   , cmosw  = ", grooved , iangle  , cincli  , fdist   , cmosw   )
    #print(difrorder, (np.sin(iangle)-np.sin((.5-xx[::5])*cmosw/2/fdist - cincli)))
    return grooved/difrorder*(np.sin(iangle)-np.sin((.5-xx)*cmosw/2/fdist - cincli))

def lambda_to_x(ll, difrorder): ## numerical inversion of (user-defined) function x_to_lambda for x in (0 ... 1)
    x = np.linspace(0, 1, 20) 
    return np.interp(ll, x_to_lambda(x, difrorder), x)

def lambda_to_y(ll):
    def sellmeyer(l):
        n0 = p('prism_n0') #1239.8e-9 / 5
        lambda0 = p('prism_Sellmeyer_lambda0 (nm)')*1e-9 #1239.8e-9 / 5
        F0 = p('prism_Sellmeyer_F0')
        n = n0 + (F0*lambda0**-2/(lambda0**-2-l**-2))**.5
        #print('n0, F0, lambda0' , n0, F0, lambda0, l,)
        #print('n =' , n)
        return n
    def symmetricprism(l):
        #incident_vert_inclination = -.5
        prism_angle = p('prism_angle')         # (rad)
        n = sellmeyer(l)
        return 2 * (np.arcsin(n * np.sin(prism_angle/2)) - prism_angle/2)   # refraction on a dispersive prism

    cmosh =  p('W camera CMOS width (mm)') * 1e-3   * 16/24 ## fixme: adapt for non-24x16mm frames
    #return p('vertical camera inclination') + lam*p('prism_angle') + lam**2*p('lambda_to_y_quad') + \
            #lam**3*p('lambda_to_y_cub') + lam**4*p('lambda_to_y_quart')
    
    return (p('κ vertical camera declination (rad)') + symmetricprism(ll)) / cmosh * p('F camera foc dist (mm)')*1e-3


## == User interaction ==

def update(val): ## update plots on manual parameter tuning
    for lineindex, difrorder in enumerate(range(int(p('first_order_number')), int(p('last_order_number')+1))):
        x = np.linspace(0, 1, 20) 
        yy = lambda_to_y(x_to_lambda(x, difrorder))
        lines[lineindex].set_ydata(yy)

        # update spectral peaks, too
        major_xs, major_ys = lambda_to_x(spectral_peaks_major, difrorder), lambda_to_y(spectral_peaks_major)
        peaks_major[lineindex].set_data(major_xs, major_ys)

        midi_xs, midi_ys = lambda_to_x(spectral_peaks_midi, difrorder), lambda_to_y(spectral_peaks_midi)
        peaks_midi[lineindex].set_data(midi_xs, midi_ys)

        minor_xs, minor_ys = lambda_to_x(spectral_peaks_minor, difrorder), lambda_to_y(spectral_peaks_minor)
        peaks_minor[lineindex].set_data(minor_xs, minor_ys)

        plot_lambdas, plot_intensity = ([], [])
        for xpixel in range(npimage.shape[1]):
            l = x_to_lambda(xpixel/npimage.shape[1], difrorder)
            ypixel = int((1.0-lambda_to_y(l)) * npimage.shape[0])
            try: 
                plot_intensity.append(npimage[ypixel, xpixel])
                plot_lambdas.append(l)
            except IndexError:
                pass
        spectral_curves[lineindex].set_data(np.array(plot_lambdas)*1e9, np.array(plot_intensity))
    fig.canvas.draw_idle()

paramsliders = {}
sliderheight, sliderpos = .02, .025
for key,item in list(default_params.items())[::-1]:
    paramsliders[key] = matplotlib.widgets.Slider(plt.axes([0.15, sliderpos, 0.80, sliderheight]), key, item[0], item[2], valinit=item[1])
    paramsliders[key].on_changed(update)
    sliderpos += sliderheight*1.4 if key in ('x_to_lambda_ofs','κ vertical camera declination (rad)') else sliderheight

def reset_values(event): 
    #for key,item in paramsliders.items(): item.reset()
    with open('echelle_settings.dat', 'w') as of:
        for key,item in paramsliders.items(): 
            print(key,'=',item)
            of.write(key,'=',item)

button = matplotlib.widgets.Button(plt.axes([.8, 0.02, 0.1, sliderheight]), 'Save settings', color='.7', hovercolor='.9')
button.on_clicked(reset_values)

#rax1 = plt.axes([0.025, 0.5, 0.15, 0.15])
#radio = matplotlib.widgets.RadioButtons(rax1, ('red', 'blue', 'green'), active=0)
#def colorfunc(label):
    #l.set_color(label)
    #fig.canvas.draw_idle()
#radio.on_clicked(colorfunc)

#print('test', lambda_to_x(x_to_lambda(a,1),1))
#print('test', x_to_lambda(lambda_to_x(a,1),1))


## == plotting the image == 
raw_file_name = '../image_logs/output_debayered_.1s_ISO100_.cr2'
from rawkit.raw import Raw
from rawkit.options import interpolation
raw_image = Raw(filename=raw_file_name)
raw_image.options.interpolation = interpolation.amaze # or "amaze", see https://rawkit.readthedocs.io/en/latest/api/rawkit.html
#raw_image_process = raw_image.process()
#if raw_image_process == raw_image: print("they are identical")
npimage = np.array(raw_image.raw_image(include_margin=False), dtype=float)  # returns: 2D np. array


#npimage = np.convolve(npimage,np.ones([5])) #TODO 2D convolution?
import scipy.ndimage

## vertical convolution to employ the multi-megapixel image and reduce noise 
## TODO: width as adjustable param
vertical_gaussian_kernel = np.outer(np.e**(-np.linspace(-1,1,100)**2),np.array([1]))
npimage = scipy.ndimage.convolve(npimage, vertical_gaussian_kernel/np.sum(vertical_gaussian_kernel)) 

npimage -= np.min(npimage) ## subtract constant background #TODO  should subtract known "black frame"

## optional: decimate data for faster processing
decimate_factor = 10
npimage = scipy.ndimage.convolve(npimage, np.ones([decimate_factor,decimate_factor])/decimate_factor**2)
npimage = npimage[::decimate_factor,::decimate_factor]

#ax1.imshow((npimage-np.min(npimage)*.9)**.1, extent=[0,1,0,1],cmap=matplotlib.cm.gist_earth_r)
im = ax1.imshow(np.log10(npimage), extent=[0,1,0,1], cmap=matplotlib.cm.gist_earth_r)

## == plotting the diffr orders == 
xs = np.linspace(0, 1, 20) # image pixel range to analyze
lines, peaks_major, peaks_midi, peaks_minor, spectral_curves = ([], [], [], [], [])
for difrorder in range(int(p('first_order_number')), int(p('last_order_number')+1)):
    lambdas  = x_to_lambda(xs, difrorder)
    ys       = lambda_to_y(lambdas)
    lines.append(ax1.plot(xs, ys, lw=1, ls='--' if difrorder==1 else '-')[0]) ## , color='red'

    major_xs, major_ys = lambda_to_x(spectral_peaks_major, difrorder), lambda_to_y(spectral_peaks_major)
    peaks_major.append(ax1.plot(major_xs, major_ys, marker='D', lw=0, markersize=8, markeredgecolor='k', markerfacecolor='none')[0])

    midi_xs, midi_ys = lambda_to_x(spectral_peaks_midi, difrorder), lambda_to_y(spectral_peaks_midi)
    peaks_midi.append(ax1.plot(midi_xs, midi_ys, marker='D', lw=0, markersize=6, markeredgecolor='k', markerfacecolor='none',alpha=.6)[0])

    minor_xs, minor_ys = lambda_to_x(spectral_peaks_minor, difrorder), lambda_to_y(spectral_peaks_minor)
    peaks_minor.append(ax1.plot(minor_xs, minor_ys, marker='D', lw=0, markersize=4, markeredgecolor='k', markerfacecolor='none',alpha=.4)[0])

    plot_lambdas, plot_intensity = ([], [])
    for xpixel in range(npimage.shape[1]):
        l = x_to_lambda(xpixel/npimage.shape[1], difrorder)
        ypixel = int((1.0-lambda_to_y(l)) * npimage.shape[0])
        try: 
            plot_intensity.append(npimage[ypixel, xpixel])
            plot_lambdas.append(l)
        except IndexError:
            pass
    spectral_curves.append(ax2.plot(np.array(plot_lambdas)*1e9, np.array(plot_intensity), lw=1.5, alpha=.8)[0])

## generate artificial neon spectrum
artif_x = np.linspace(300e-9, 1100e-9, 2000)
artif_y = np.zeros_like(artif_x) + 1
for peak in spectral_peaks_major: artif_y += np.exp(-(artif_x-peak)**2 * 1e9**2)*100
for peak in spectral_peaks_midi:  artif_y += np.exp(-(artif_x-peak)**2 * 1e9**2)*30
for peak in spectral_peaks_minor: artif_y += np.exp(-(artif_x-peak)**2 * 1e9**2)*10
ax2.plot(artif_x*1e9, artif_y, lw=.6, c='k', ls='--')


ax2.set_yscale('log')
ax2.grid(True)
ax2.set_xlabel('wavelength (nm)')
ax2.set_ylabel('uncalibrated intensity (a. u.)')
    
plt.show()
