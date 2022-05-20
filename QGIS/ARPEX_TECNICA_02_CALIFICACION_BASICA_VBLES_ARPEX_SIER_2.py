import os
import osr
import math
import gdal
import glob
import shutil
import processing
import numpy as np
from math import *
import pandas as pd
from qgis.gui import *
from qgis.core import *
from pathlib import Path
from sklearn import metrics
from matplotlib import pyplot as plt
from configparser import ConfigParser
from qgis.PyQt.QtCore import QVariant
from timeit import default_timer as timer
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

###--------------------CONFIGURACION ARPEX-----------------------------------
start = timer()

config=ConfigParser()
config.read(r'U:\BRASIL_DSK\BR_2103\PARAMETROS_PROYECTO\ARPEX_TECNICA_00_CONTROL_FILE.ini')
ruta=r'%s' %(config['GENERAL']['ruta_ubicacion'])
extent_proyecto = r'%s' %(config['GENERAL']['extent_proyecto'])
nom_proyecto = r'%s' %(config['GENERAL']['nom_proyecto'])
DEM_inicio = r'%s' %(config['GENERAL']['DEM'])
sistema_coord = r'%s' %(config['GENERAL']['NUM_SIST_COORD'])
excel_inicio = r'%s' %(config['GENERAL']['excel_default'])
matriz_ahp_te = r'%s' %(config['GENERAL']['matriz_ahp_te'])
matriz_ahp_pr = r'%s' %(config['GENERAL']['matriz_ahp_pr'])
matriz_ahp_am = r'%s' %(config['GENERAL']['matriz_ahp_am'])
version_proyecto = r'%s' %(config['GENERAL']['version_proyecto'])
output_temporary = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/TEMPORAL/'
salida_vbles = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/VARIABLE_R/'

###---------FUNCIONES BASICAS PARA EL MANEJO DE RASTERS Y SHAPES---------------------------------

def toRaster(shp, dem, ruta_salida, campo_a_rasterizar): 
    area= QgsRasterLayer(dem)
    ext = area.extent()

    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    coords = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
    
    vlayer_dp=area.dataProvider()
    vlayer_crs=vlayer_dp.crs()
    vlayer_crs_str=vlayer_crs.authid()
    vlayer_EPSG_int=int(vlayer_crs_str[5:])
    epgs=vlayer_crs_str[5:]
    
    #print(epgs)
    coords =coords+" [EPSG:"+epgs+"]"
    #print(coords)
    
    pixelSizeX = area.rasterUnitsPerPixelX()
    pixelSizeY = area.rasterUnitsPerPixelY()
    #print(pixelSizeX)
    
    raster=ruta_salida
    processing.run("gdal:rasterize", {'INPUT':shp,\
    'FIELD':campo_a_rasterizar,'BURN':0,'UNITS':1,\
    'WIDTH':pixelSizeX,'HEIGHT':pixelSizeY,\
    'EXTENT':coords,'NODATA':0,'OPTIONS':'',\
    'DATA_TYPE':5,'INIT':None,\
    'INVERT':False,'EXTRA':'',\
    'OUTPUT':raster})
    return raster

###---------LISTA DE VARIABLES QUE ENTRARAN AL ANALISIS ARPEX-----------------------------------
excel_default = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio)
default = excel_default.loc[excel_default['POR DEFECTO'] == 1]
ejecutables = default['VARIABLES'].tolist()

###-----------------LECTURA DE VARIABLES ACIM---------------------------------------------------------

#Las Variables ACIM se deben reclasificar en los valores de susceptibilidad 
#y se generan con los nombres presentes en el Excel Default. Varibles tomadas de la 1ra parte de ACIM

#Datos necesarios para remuestrear las variables ACIM
#-------------------------------------------
DEM = output_temporary + 'dem_clip.tif'

pixelSizeX = QgsRasterLayer(DEM).rasterUnitsPerPixelX()
pixelSizeY = QgsRasterLayer(DEM).rasterUnitsPerPixelY()

area= QgsRasterLayer(DEM)
ext = area.extent()

xmin = ext.xMinimum()
xmax = ext.xMaximum()
ymin = ext.yMinimum()
ymax = ext.yMaximum()
coords = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
#-------------------------------------------

p = Path(salida_vbles)
if 'poteinest' in ejecutables:
    for name in p.glob('*inestabilidad*'):
        if str(name).endswith('.tif'):
            a=name
            vble = r'%s' %(a)
    
    processing.run("qgis:reclassifybytable", {'INPUT_RASTER': vble,
                                            'RASTER_BAND':1,'TABLE':[-1000,0.27,1,0.27,0.34,2,0.34,0.39,3,0.39,0.71,4,0.71,10000,5],
                                            'NO_DATA': -9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                            'OUTPUT': output_temporary + 'vatesu1c' + nom_proyecto + '_PoteInest_' + version_proyecto + '.tif'})

    #remuestreamos la vble, para que tenga el mismo tamaño de pixel que las obtenidas por ARPEX
    processing.run("grass7:r.resample", {'input': output_temporary + 'vatesu1c' + nom_proyecto + '_PoteInest_' + version_proyecto + '.tif',
                                        'output': salida_vbles + 'vatesu1c_' + nom_proyecto + '_poteinest_' + version_proyecto + '.tif',
                                        'GRASS_REGION_PARAMETER':coords,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':pixelSizeX,
                                        'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

    print ("Variable poteinest creada")

if 'poteinun' in ejecutables:
    for name in p.glob('*inundabilidad*'):
        if str(name).endswith('.tif'):
            a=name
            vble = r'%s' %(a)
    processing.run("qgis:reclassifybytable", {'INPUT_RASTER': vble,
                                            'RASTER_BAND':1,'TABLE':[-1000,0.27,1,0.27,0.34,2,0.34,0.39,3,0.39,0.71,4,0.71,10000,5],
                                            'NO_DATA': -9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                            'OUTPUT': output_temporary + 'vatesu1c' + nom_proyecto + '_PoteInun_' + version_proyecto + '.tif'})

    #remuestreamos la vble, para que tenga el mismo tamaño de pixel que las obtenidas por ARPEX
    processing.run("grass7:r.resample", {'input': output_temporary + 'vatesu1c' + nom_proyecto + '_PoteInun_' + version_proyecto + '.tif',
                                        'output': salida_vbles + 'vatesu1c_' + nom_proyecto + '_poteinun_' + version_proyecto + '.tif',
                                        'GRASS_REGION_PARAMETER':coords,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':pixelSizeX,
                                        'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

    print ("Variable poteinun creada")

if 'satsuelo' in ejecutables:
    for name in p.glob('*Humedad*'):
        if str(name).endswith('Humedad' + '_' + nom_proyecto + '_' + version_proyecto + '.tif'):
            a=name
            vble = r'%s' %(a)
    processing.run("qgis:reclassifybytable", {'INPUT_RASTER': vble,
                                            'RASTER_BAND':1,'TABLE':[-1000,3.87,1,3.87,6.16,2,6.16,9.41,3,9.41,21.34,4,21.34,10000,5],
                                            'NO_DATA': -9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                            'OUTPUT': output_temporary + 'vatesu1c' + nom_proyecto + '_SatSuelo_' + version_proyecto + '.tif'})

    #remuestreamos la vble, para que tenga el mismo tamaño de pixel que las obtenidas por ARPEX
    processing.run("grass7:r.resample", {'input': output_temporary + 'vatesu1c' + nom_proyecto + '_SatSuelo_' + version_proyecto + '.tif',
                                        'output': salida_vbles + 'vatesu1c_' + nom_proyecto + '_satsuelo_' + version_proyecto + '.tif',
                                        'GRASS_REGION_PARAMETER':coords,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':pixelSizeX,
                                        'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

    print ("Variable satsuelo creada")

if 'matsuelo' in ejecutables:
    for name in p.glob('*espesor*'):
        if str(name).endswith('espesor' + '_' + nom_proyecto + '_' + version_proyecto + '.tif'):
            a=name
            vble = r'%s' %(a)
    processing.run("qgis:reclassifybytable", {'INPUT_RASTER': vble,
                                            'RASTER_BAND':1,'TABLE':[-1000,6.4,5,6.4,11.3,4,11.3,16.6,3,16.6,22.6,2,22.6,10000,1],
                                            'NO_DATA': -9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                            'OUTPUT': output_temporary + 'vatesu1c' + nom_proyecto + '_MatSuelo_' + version_proyecto + '.tif'})

    #remuestreamos la vble, para que tenga el mismo tamaño de pixel que las obtenidas por ARPEX
    processing.run("grass7:r.resample", {'input': output_temporary + 'vatesu1c' + nom_proyecto + '_MatSuelo_' + version_proyecto + '.tif',
                                        'output': salida_vbles + 'vatesu1c_' + nom_proyecto + '_matsuelo_' + version_proyecto + '.tif',
                                        'GRASS_REGION_PARAMETER':coords,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':pixelSizeX,
                                        'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

    print ("Variable matsuelo creada")

####--------------------Lectura de las Variables Tecnicas ARPEX----------------------------------
vbles_arpex = r'U:\BR_2102_2022-LE01-LT03\APP_ARPEX_RESULTADOS\Reporte_LT03_Trecho3_v0_20220218_212152\scored_variables'
# vbles_arpex = ruta + 'BDVAR/'
vbles_te = vbles_arpex
# vbles_te = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/VARIABLE_V/'

lista_vbles_te = []
lista_nom = []

#BUSCAMOS LOS SHAPES DE LAS VARIABLES DEL ASPECTO TECNICO
p = Path(vbles_te)
for name in p.glob('*Tecnico*'):
    if str(name).endswith('.shp'):
        a=name
        lista_vbles_te.append(r'%s' %(a))

#OBTENEMOS LAS VARIABLES CALIFICADAS Y EN RASTER DEL ASPECTO TECNICO
for vble_te in lista_vbles_te:
    nom_shape = ((vble_te.split('\\')[-1]).split('_')[0]).split('.')[0]
    lista_nom.append(nom_shape)
    nom_is = 'vatete1c0'
    toRaster(vble_te, DEM, output_temporary + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif', 'suscept')
    #Pasamos los nodata a 1, para poder realizar algebra de mapas de manera correcta
    processing.run("grass7:r.null", {'map': output_temporary + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif',
                                    'setnull':'','null':1,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                    'output': salida_vbles + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif',
                                    'GRASS_REGION_PARAMETER':None,
                                    'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                    'GRASS_RASTER_FORMAT_OPT':'',
                                    'GRASS_RASTER_FORMAT_META':''})
#
#    print ("Variable" + " " + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + " " + "creada")
#
####--------------------Lectura de las Variables Ambientales ARPEX----------------------------------
vbles_am = vbles_arpex
# vbles_am = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/VARIABLE_V/'

lista_vbles_am = []
lista_nom = []

#BUSCAMOS LOS SHAPES DE LAS VARIABLES DEL ASPECTO AMBIENTAL
p = Path(vbles_am)
for name in p.glob('*Ambiental*'):
    if str(name).endswith('.shp'):
        a=name
        lista_vbles_am.append(r'%s' %(a))

#OBTENEMOS LAS VARIABLES CALIFICADAS Y EN RASTER DEL ASPECTO AMBIENTAL
for vble_am in lista_vbles_am:
    nom_shape = ((vble_am.split('\\')[-1]).split('_')[0]).split('.')[0]
    lista_nom.append(nom_shape)
    nom_is = 'vaamam1c0'
    toRaster(vble_am, DEM, output_temporary + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif', 'suscept')
    #Pasamos los nodata a 1, para poder realizar algebra de mapas de manera correcta
    processing.run("grass7:r.null", {'map': output_temporary + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif',
                                    'setnull':'','null':1,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                    'output': salida_vbles + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif',
                                    'GRASS_REGION_PARAMETER':None,
                                    'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                    'GRASS_RASTER_FORMAT_OPT':'',
                                    'GRASS_RASTER_FORMAT_META':''})

####--------------------Lectura de las Variables Prediales ARPEX----------------------------------
vbles_predial = vbles_arpex
# vbles_predial = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/VARIABLE_V/'

lista_vbles_pr = []
lista_nom = []

#BUSCAMOS LOS SHAPES DE LAS VARIABLES DEL ASPECTO PREDIAL
p = Path(vbles_predial)
for name in p.glob('*Predial*'):
    if str(name).endswith('.shp'):
        a=name
        lista_vbles_pr.append(r'%s' %(a))

#OBTENEMOS LAS VARIABLES CALIFICADAS Y EN RASTER DEL ASPECTO PREDIAL
for vble_pr in lista_vbles_pr:
    nom_shape = ((vble_pr.split('\\')[-1]).split('_')[0]).split('.')[0]
    lista_nom.append(nom_shape)
    nom_is = 'vaprpr1c0'
    toRaster(vble_pr, DEM, output_temporary + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif', 'suscept')
    #Pasamos los nodata a 1, para poder realizar algebra de mapas de manera correcta
    processing.run("grass7:r.null", {'map': output_temporary + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif',
                                    'setnull':'','null':1,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                    'output': salida_vbles + nom_is[:-1] + "_" + nom_proyecto + "_" + nom_shape + "_" + version_proyecto + '.tif',
                                    'GRASS_REGION_PARAMETER':None,
                                    'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                    'GRASS_RASTER_FORMAT_OPT':'',
                                    'GRASS_RASTER_FORMAT_META':''})

###-----------------------------------------------------------

end = timer()
print(end - start,'segundos') # Time in seconds
print('Proceso terminado')