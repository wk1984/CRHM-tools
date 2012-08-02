from osgeo import gdal
gdal.UseExceptions() #enable exception handling

import numpy as np
from landclass import *

from math import *
import matplotlib.pyplot as plt
import itertools as it


class basin(object):
    """Describes a CRHM basin"""
    def __init__(self):
        self._landclass = {}
        self._hrus={} #holds the bin edges for each raster
        self._final_hrus={}

    def get_num_landclass(self):
        return len(self._landclass)
    
    def add_landclass(self,lc):
        self._landclass[lc._name] = lc
        
    def get_num_hrus(self):
        return self._num_hrus
    
    def create_hrus(self):
        comb = []
        size = None
        for c in self._landclass:
            a=range(1,self._landclass[c].get_nclasses()+1)
            comb.append(a)
            
            if size == None:
                size = self._landclass[c].size()
            elif size != self._landclass[c].size():
                raise Exception('Rasters are of a different size')
            
        hrus = list(it.product(*comb))
        self._num_hrus = len(hrus)
        stack = np.dstack(([r.get_classraster() for r in self._landclass.values()]))

        #do the classification
        out = (np.array([np.array(h)[...,:] == stack for h in hrus]).all(axis = -1) *
                 (2 + np.arange(len(hrus)))[:, None, None]).max(axis=0) - 1       

    
        return out
        
    
    def show(self):
        
        nclasses = len(self._landclass)
        gs=plt.GridSpec(nclasses, 2)
        
        row = 0
        fig=plt.figure()
        for c in self._landclass:
            ax=fig.add_subplot(gs[row,0], title=c)
            im=ax.imshow(self._landclass[c].get_raster())
            
            from mpl_toolkits.axes_grid1 import make_axes_locatable
            divider = make_axes_locatable(plt.gca())
            cax = divider.append_axes("right", "5%", pad="3%")            
            cb=fig.colorbar(im,cax=cax)
            
            ax=fig.add_subplot(gs[row,1],title='Classified '+c)
            im=ax.imshow(self._landclass[c].get_classraster())
            
            
            divider = make_axes_locatable(plt.gca())
            cax = divider.append_axes("right", "5%", pad="3%")            
            cb=fig.colorbar(im,cax=cax)
            
            cb.set_ticks( list(range(1,self._landclass[c].get_nclasses()+1)))
            cb.set_ticklabels(self._landclass[c].get_classes_str())            

            row +=1
        
        fig.tight_layout()
        #plt.show()

    def __call__(self,name):
        return self._landclass[name]
   
    #def create_from_DEM(self,attr):
        #if attr == "slope":
            #lol = generic_3x3_window(self._landclass['dem'].get_raster(), lambda x: atan(sqrt((x[3]-x[5])**2 + (x[7]-x[1])**2)/2) * (180/3.14159))
            
    def remove_landclass(self,name):
        del self._landclass[name]
