matplotlib.rc('font', size=12, family='serif')
#for          x,  y,  n,              param,  label,  xlabel,  ylabel,  color in \
#         zip(xs, ys, range(len(xs)), params, labels, xlabels, ylabels, colors):
    # x, y = x[~np.isnan(y)], y[~np.isnan(y)]        ## filter-out NaN points
    # convol = 2**-np.linspace(-2,2,25)**2; y = np.convolve(y,convol/np.sum(convol), mode='same') ## simple smoothing

 #   ax.plot(x, y, label="%s" % (label), color=color)
    #ax.plot(x, y, label="%s" % (label.split('.dat')[0]), color=colors[c%10], ls=['-','--'][int(c/10)]) 
for xx,yy in zip(xs[0],ys[0]):
  ax.plot((xx,xx), (0,np.log10(yy)), lw=yy/3000, alpha=.8, c='r')
ax.set_xlabel('wavelength (nm)')
ax.set_ylabel('log of relative intensity')

plot_title = sharedlabels[-4:] ## last few labels that are shared among all curves make a perfect title
#plot_title = sharedlabels[sharedlabels.index('LASTUNWANTEDLABEL')+1:] ## optionally, use all labels after this 

ax.set_title(' '.join(plot_title)) 
ax.legend(loc='best', prop={'size':10})

#np.savetxt('output.dat', np.vstack([x,ys[0],ys[1]]).T, fmt="%.4f")
#tosave.append('_'.join(plot_title)+'.png') ## whole graph will be saved as PNG
#tosave.append('_'.join(plot_title)+'.pdf') ## whole graph will be saved as PDF
