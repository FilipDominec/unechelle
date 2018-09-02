#!/usr/bin/python3
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import collections
import time

from rawkit.raw import Raw
from rawkit.options import interpolation
from scipy import ndimage

"""
Formulation of the problem:
    * Light of unknown spectrum, further denoted as "white light", is introduced into the instrument in an optical fibre, 
      at a defined position it is outcoupled and collimated by a lens/mirror
    * The collimated ray is vertically dispersed by an optical prism (with known angle and Sellmeyer parameters)
    * Then it impinges (under angle α from its normal) a blazed "echelle" diffraction grating (with Λ groove spacing)
    * It diffracts into multiple high orders (typically 5-30), which are however all limited to a narrow angle due to relatively
      wide facets of the echelle grating.
      part of the light is collected by a digital camera (inclined by angle ξ from the grating normal, which should be
      given by finding the most efficient reflection on the blazed grating facets)
    * The camera lens has a focal length F and projects light on a CMOS/CCD sensor of width W
    * Given α, ξ, Λ, F and W, along with the selection of a integer diffraction order M,
      how does position X on the sensor translate into wavelength λ?

Derivation of the equations used:
    * Grating equation:     
                                             sin α - sin β = Mλ/Λ,    
      where α, β are the angles of incident and diffracted rays.
    * Normalized coordinate in the middle of the sensor X = 0.5 corresponds to β = -ξ, and more generally, 
      any coordinate on sensor X ∈ {0...1} corresponds to the angle ξ of a diffracted ray as β = (0.5-X) × W / 2F  -  ξ
    * Thus we express the wavelength as
                                 λ = Λ/M × [sin α - sin((0.5-X) × W / 2F  -  ξ)]
     
TODOs:

    * interpolate to a single spectral curve

    integration with hardware:
        move the actual λ-x-y conversion and into a separate module: echelle_process.py

    improvements:
        HDR data composition



"""
## Static settings & built-in constants
raw_file_name                   = '../image_logs/output_debayered_.1s_ISO100_.cr2'      # FIXME
settingsfilename                = './echelle_parameters.dat'
vertical_convolution_length_px  = 100           ## adjust if orders start to overlap (e.g. with higher blazing angle)
cmos_aspect_ratio               = 16./24        ## for "APS-C"; change if using CMOS/CCD with different aspect
decimate_factor                 = 4             ## less than 2 introduces noise from Bayer mask residuals

## Echelle processing parameters accesible as sliders in the GUI, or via direct editing of the settings file
default_params = collections.OrderedDict()
default_params['first_order_number']	    =	   (-20,    4,      20)  # (range from, range to, initial value)
default_params['last_order_number']	    =	   (-20,    16,     20)
## Horizontal dispersion (blazed grating):
default_params['Λ groove spacing (μm)']	    =	   (0,      13.333, 30)
default_params['α incident angle (rad)']    =	   (-1,     .4,     1)
default_params['ξ horizontal camera inclination (rad)'] = (-0,  .12, .2)
default_params['F camera foc dist (mm)']    =	   (10,     84,     300)
default_params['W camera CMOS width (mm)']  =	   (1,      24,     50)
## Vertical dispersion (prism):
default_params['κ vertical camera declination (rad)']	    =	   (1.4,   1.534, 1.55)      # TODO inclination/declination? 
default_params['prism_angle']	            =	   (-2,    -1.045, -1)
default_params['prism_n0']	            =	   (1.3,    1.38, 1.4)
default_params['prism_Sellmeyer_lambda0 (nm)']	=  (50,    180, 500)
default_params['prism_Sellmeyer_F0']	    =	   (-0,    .252, .5)



## Load and access the previously saved image processing parameters
echelle_parameters = {}
try:
    with open(settingsfilename) as settingsfile:
        for n, line in enumerate(settingsfile.readlines()):
            try:
                key, val = line.split('=', 1)
                echelle_parameters[key.strip()] = float(val)
            except ValueError:
                print("Warning: could not process value `{}` for key `{}` in line #{} in `{}`".format(key, val, n, settingsfilename))
except IOError:
    print("Warning: could not read `{}` in the working directory; using default values for image processing".format(settingsfilename))

def p(pname): return paramsliders[pname].val

## functions defining the geometrical transformation (x,y position on CMOS due to grating and prism, respectively)
def x_to_lambda(xx, difrorder):
    grooved     = p('Λ groove spacing (μm)')       * 1e-6
    iangle      = p('α incident angle (rad)')
    cincli      = p('ξ horizontal camera inclination (rad)')
    fdist       = p('F camera foc dist (mm)')      * 1e-3
    cmosw       = p('W camera CMOS width (mm)')    * 1e-3
    return grooved/difrorder*(np.sin(iangle)-np.sin((.5-xx)*cmosw/2/fdist - cincli))

def lambda_to_x(ll, difrorder): ## for x in (0 ... 1) numerical inversion of the function x_to_lambda 
    x = np.linspace(0, 1, 20) 
    return np.interp(ll, x_to_lambda(x, difrorder), x)

def lambda_to_y(ll):
    def sellmeyer(l):
        n0      = p('prism_n0') #1239.8e-9 / 5
        lambda0 = p('prism_Sellmeyer_lambda0 (nm)')*1e-9 #1239.8e-9 / 5
        F0      = p('prism_Sellmeyer_F0')
        n       = n0 + (F0*lambda0**-2/(lambda0**-2-l**-2))**.5
        #print('n0, F0, lambda0' , n0, F0, lambda0, l,)
        #print('n =' , n)
        return n
    def symmetricprism(l):
        #incident_vert_inclination = -.5
        prism_angle = p('prism_angle')         # (rad)
        n = sellmeyer(l)
        return 2 * (np.arcsin(n * np.sin(prism_angle/2)) - prism_angle/2)   # refraction on a dispersive prism

    cmosh =  p('W camera CMOS width (mm)') * 1e-3  * cmos_aspect_ratio 
    return (p('κ vertical camera declination (rad)') + symmetricprism(ll)) / cmosh * p('F camera foc dist (mm)')*1e-3





## Loading and pre-processing the RAW image
raw_image = Raw(filename=raw_file_name)
tt = time.time()
raw_image.options.interpolation = interpolation.linear # n.b. "linear" and "amaze" have the same effect
npimage = np.array(raw_image.raw_image(include_margin=False), dtype=float)  # returns: 2D np. array
print(time.time()-tt)


## vertical convolution to employ the multi-megapixel image and reduce noise 
#vertical_averaging_kernel = np.outer(np.e**(-np.linspace(-1,1,vertical_convolution_length_px)**2),np.array([1]))
vertical_averaging_kernel = np.outer(np.sin(-np.linspace(0,np.pi,vertical_convolution_length_px)**.5),np.array([1]))
npimage = ndimage.convolve(npimage, vertical_averaging_kernel/np.sum(vertical_averaging_kernel)) 


## optional: decimate data for faster processing
npimage = ndimage.convolve(npimage, np.ones([decimate_factor,decimate_factor])/decimate_factor**2)
npimage = npimage[::decimate_factor,::decimate_factor]

## optional: subtract constant background #TODO  should subtract known "black frame"
npimage -= np.min(npimage) 






## GUI user interaction
fig, (ax1, ax2) = plt.subplots(1,2)
fig.subplots_adjust(left=0.05, right=0.95, bottom=0.30, top=0.99, hspace=0)

def update(val): ## update plots on manual parameter tuning
    for lineindex, difrorder in enumerate(range(int(p('first_order_number')), int(p('last_order_number')+1))):
        x = np.linspace(0, 1, 20) 
        yy = lambda_to_y(x_to_lambda(x, difrorder))
        lines[lineindex].set_data(x, yy)

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
                plot_intensity.append(npimage[ypixel, xpixel])      ## TODO non-interactive spectral processnig  HERE
                plot_lambdas.append(l)
            except IndexError:
                pass
        spectral_curves[lineindex].set_data(np.array(plot_lambdas)*1e9, np.array(plot_intensity))
    fig.canvas.draw_idle()

## GUI: Known spectral peaks for neon lamp 
spectral_peaks_major   = np.array([585.249, 614.306, 640.225, 703.241]) / 1e9
spectral_peaks_midi    = np.array([
        576.4674, 588.189,594.483, 607.434, 609.616, 616.359, 626.649, 633.443,  
        638.299, 650.653, 667.828, 671.704, 692.947, 724.517]) / 1e9
spectral_peaks_minor   = np.array([
        334.148, 365.0146, 365.4833, 366.3276, 404.6563, 407.7831, 435.8328, 491.6068, 546.0735, 576.9598, 579.0640,
        581.932, 597.553, 603.000, 621.728, 630.479, 653.288, 659.895, 717.394, 743.890]) / 1e9
# TODO: experimental mismatch for λ<500 nm, why? See also http://www.astrosurf.com/buil/us/spe2/calib2/neon.dat etc.

## GUI: Generate sliders for each image-processing parameter at the bottom of the window
paramsliders = {}
sliderheight, sliderpos = .02, .025
for key,item in list(default_params.items())[::-1]:
    paramsliders[key] = matplotlib.widgets.Slider(
            plt.axes([0.15, sliderpos, 0.80, sliderheight]), 
            key, item[0], item[2], 
            valinit=echelle_parameters.get(key.strip(), item[1]))
    paramsliders[key].on_changed(update)
    sliderpos += sliderheight*1.4 if key in ('x_to_lambda_ofs','κ vertical camera declination (rad)') else sliderheight

## GUI: Option to save current parameter values
def save_values(event): 
    #for key,item in paramsliders.items(): item.save()
    with open('echelle_settings.dat', 'w') as of:
        for key,item in paramsliders.items(): 
            print(key,'=',item.val)
            of.write(key + ' '*(40-len(key)) + ' = ' + str(item.val)+'\n')
button = matplotlib.widgets.Button(plt.axes([.8, 0.02, 0.1, sliderheight]), 'Save settings', color='.7', hovercolor='.9')
button.on_clicked(save_values)



## GUI: plotting the RAW image
im = ax1.imshow(np.log10(npimage), extent=[0,1,0,1], cmap=matplotlib.cm.gist_earth_r)

## GUI: Prepare (empty) matplotlib curve objects for plotting the diffraction orders and spectra
lines, peaks_major, peaks_midi, peaks_minor, spectral_curves = ([], [], [], [], [])
for difrorder in range(int(p('first_order_number')), int(p('last_order_number')+1)):
    lines.append(ax1.plot([], [], lw=1, ls='--' if difrorder==1 else '-')[0]) 
    peaks_major.append(ax1.plot([], [], marker='D', lw=0, markersize=8, markeredgecolor='k', markerfacecolor='none')[0])
    peaks_midi.append(ax1.plot([], [], marker='D', lw=0, markersize=6, markeredgecolor='k', markerfacecolor='none',alpha=.6)[0])
    peaks_minor.append(ax1.plot([], [], marker='D', lw=0, markersize=4, markeredgecolor='k', markerfacecolor='none',alpha=.4)[0])
    spectral_curves.append(ax2.plot([], [], lw=1.5, alpha=.8)[0])
update(None)

## In the right panel: Generate artificial neon spectrum for verification
artif_x = np.linspace(300e-9, 1100e-9, 2000)
artif_y = np.zeros_like(artif_x) + 1
#for peak in spectral_peaks_major: artif_y += np.exp(-(artif_x-peak)**2 * 1e9**2)*100
#for peak in spectral_peaks_midi:  artif_y += np.exp(-(artif_x-peak)**2 * 1e9**2)*30
#for peak in spectral_peaks_minor: artif_y += np.exp(-(artif_x-peak)**2 * 1e9**2)*10
wls,intenss = np.genfromtxt('../../spectral_data/neon-nist-cropped.dat', unpack=True)
for wl,intens in zip(wls,intenss): 
    artif_y += np.exp(-(artif_x-wl/1e9)**2 * 1e9**2)*intens**3/1e10
ax2.plot(artif_x*1e9, artif_y, lw=.6, c='k', ls='--')

ax2.set_yscale('log')
ax2.grid(True)
ax2.set_xlabel('wavelength (nm)')
ax2.set_ylabel('uncalibrated intensity (a. u.)')
    
plt.show()
