#Copyright (C) 2012  Chris Marsh

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import gdal
import ogr
from gdalconst import *
import matplotlib.pyplot as plt
import copy
gdal.UseExceptions() #enable exception handling

class raster(object):
    """Defines the base characteristics of a land"""

    def __init__(self):
        """Constructor"""
        self._raster = None
        self._is_open = False
        self._file = ''

    def copy(self):
        copy.deepcopy(self)
        
    
    def show(self,figure_handle):
        
        r = self._raster

        h=figure_handle.imshow(r)
        
        
    def open(self,fname):
        gdalr = gdal.Open(fname)
        tmp = gdalr.GetRasterBand(1).ReadAsArray() 
        self._no_data = gdalr.GetRasterBand(1).GetNoDataValue();
        self._raster = np.ma.masked_where(tmp == self._no_data, tmp)     
        
        self._is_open = True
        self._fname = fname
        
        self._xsize = gdalr.RasterXSize
        self._ysize = gdalr.RasterYSize
        geotransform = gdalr.GetGeoTransform()
        self._resolution = [geotransform[1],geotransform[5]]
    
    def get_no_data(self):
        return self._no_data
    
    def get_resolution(self):
        return self._resolution
    
    #Returns the x size
    def xsize(self):
        return self._xsize
    #Returns the y size
    def ysize(self):
        return self._ysize       
    def size(self):
        return [self.ysize, self.xsize]    
    #Returns True is a raster has been loaded
    def is_open(self):
        if self._raster is None:
            return False
        else:
            return True
      
    
    def get_raster(self):
        return self._raster
    
    def get_path(self):
        return self._fname
        
    def save_to_file(self,fname):
          
        driver = gdal.GetDriverByName('GTiff')
 
        ds = driver.Create(fname, self.xsize() , self.ysize() , 1, GDT_Float32)

        band = ds.GetRasterBand(1)
        band.WriteArray(self._raster, 0, 0)


    def save_to_vector(self, fname):
        #create a temporary gdal raster to read from
        mem_driver = gdal.GetDriverByName('MEM')
        mem_ds = mem_driver.Create('', self.xsize() , self.ysize() , 1, GDT_Float32)
        
        src_band = mem_ds.GetRasterBand(1)
        src_band.WriteArray(self._raster, 0, 0)
        
        #convert to vector
        driver = ogr.GetDriverByName('ESRI Shapefile')
        dst_ds = driver.CreateDataSource( fname )
        
        #file already exists
        if dst_ds is None:
            raise IOError('File already exists. Please select another file.')
        
        dst_layer = dst_ds.CreateLayer('HRUs')
        
        fd = ogr.FieldDefn( 'DN', ogr.OFTInteger )
        dst_layer.CreateField( fd )
        dst_field = 0        
        
        prog_func = gdal.TermProgress
        options=[]
        #result = gdal.Polygonize( src_band, None, dst_layer, 0 )
        result = gdal.Polygonize( src_band, None, dst_layer, dst_field, options,callback = prog_func )        


    def __call__(self,row,col):
        return self._raster[x,y]
    