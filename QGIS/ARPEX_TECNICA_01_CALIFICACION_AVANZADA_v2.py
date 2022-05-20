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
def coordraster(raster, str_name, ruta):
    
    area=QgsRasterLayer(raster)
    vlayer_dp=area.dataProvider()
    vlayer_crs=vlayer_dp.crs()
    vlayer_crs_str=vlayer_crs.authid()
    epgs=vlayer_crs_str[5:]
    
    crs=QgsCoordinateReferenceSystem(str(vlayer_crs_str))
    if crs.isValid():
        if epgs== 3116:
            layer=raster
        else:
            layer= ruta+'/'+str_name
            processing.run("gdal:warpreproject", {'INPUT':raster,\
            'SOURCE_CRS':None,\
            'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:' + str(Numero_EPSG)),\
            'RESAMPLING':0,'NODATA':None,\
            'TARGET_RESOLUTION':None,\
            'OPTIONS':'',\
            'DATA_TYPE':0,\
            'TARGET_EXTENT':None,\
            'TARGET_EXTENT_CRS':None,\
            'MULTITHREADING':False,\
            'EXTRA':'','OUTPUT': layer})
    return layer

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

def coordshp1(shp, str_name):
    area=QgsVectorLayer(shp)
    vlayer_dp=area.dataProvider()
    vlayer_crs=vlayer_dp.crs()
    vlayer_crs_str=vlayer_crs.authid()
    epgs=vlayer_crs_str[5:]
    
    crs=QgsCoordinateReferenceSystem(str(vlayer_crs_str))
    if crs.isValid():
        layer = output_temporary + str_name
        processing.run("native:reprojectlayer", {'INPUT':shp,\
                                                'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:' + str(Numero_EPSG)),\
                                                'OUTPUT': layer})
    return layer

def ProyectRaster(raster, folder, Numero_EPSG):

    processing.run("gdal:warpreproject", {'INPUT':raster,'SOURCE_CRS':None,
                                    'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:' + str(Numero_EPSG)),'RESAMPLING':0,'NODATA':None,
                                    'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,
                                    'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'',
                                    'OUTPUT': folder + raster.split('\\')[-1].split('.')[0] + '_proy.tif'})
    
    return folder + raster.split('\\')[-1].split('.')[0] + '_proy.tif'

#---------SE OBTIENE EL EXTENT Y DEM RECORTADO Y PROYECTADO AL SISTEMA DESEADO -----------
raster = DEM_inicio
folder = output_temporary
Numero_EPSG = int(sistema_coord)

DEM1 = ProyectRaster(raster, folder, Numero_EPSG)

extent = coordshp1(extent_proyecto, 'extent.shp')

pixelSizeX = QgsRasterLayer(DEM1).rasterUnitsPerPixelX()
pixelSizeY = QgsRasterLayer(DEM1).rasterUnitsPerPixelY()

DEM = output_temporary + 'dem_clip.tif'
processing.run("gdal:cliprasterbymasklayer", {'INPUT':DEM1,\
                                             'MASK':extent,\
                                             'SOURCE_CRS':None,'TARGET_CRS':None,'NODATA':None,\
                                             'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,\
                                             'KEEP_RESOLUTION':False,'SET_RESOLUTION':False,\
                                             'X_RESOLUTION':pixelSizeX,'Y_RESOLUTION':pixelSizeY,\
                                             'MULTITHREADING':False,'OPTIONS':'','DATA_TYPE':0,\
                                             'EXTRA':'','OUTPUT':DEM})

###---------INFORMACION SECUNDARIA PARA OBTENER VBLES AVANZADAS---------------------------------
Capa_Cobertura_Vegetal = ruta + '/BDSEC/' + 'isteen1c0000_CoberturaVegetal.shp'
Excel_Cobertura_Vegetal = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + nom_proyecto + '_Veg_Alt_Tipo_' + version_proyecto + '.xlsx'
Capa_Cuerpos_Agua = ruta + '/BDSEC/01_AMBIENTAL/01_ABIOTICA/' + 'CuerposLenticos.shp'

###---------LISTA DE VARIABLES QUE ENTRARAN AL ANALISIS ARPEX-----------------------------------
excel_default = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio)
default = excel_default.loc[excel_default['POR DEFECTO'] == 1]
ejecutables = default['VARIABLES'].tolist()

###------------------DEFINICION DE VARIABLES----------------------------------------------------

def Alturasnm(DEM):
    if "alturasnm" in ejecutables:
        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': DEM,
                                                    'RASTER_BAND':1,'TABLE':[-1000,1000,1,1000,2000,2,2000,3000,3,3000,4500,4,4500,10000,5],
                                                    'NO_DATA': -9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                    'OUTPUT': salida_vbles + 'vateto1c_' + nom_proyecto + '_alturasnm' + '.tif'})

        print ("Variable alturasnm creada")

def CruceCuerposAgua(Capa_Cuerpos_Agua):
    if "crucecuerposagua" in ejecutables:
        
        #se procede a selecionar los cuerpos de agua que se encuentran en el extent:
        layer=QgsVectorLayer(Capa_Cuerpos_Agua)
        layer=QgsProject.instance().addMapLayer(layer, False)
    
        processing.run("native:selectbylocation", {'INPUT': Capa_Cuerpos_Agua,\
                                                   'PREDICATE':[0,6],\
                                                   'INTERSECT':extent,\
                                                   'METHOD':0})
        
        processing.run("native:saveselectedfeatures",{'INPUT': layer,
                                                      'OUTPUT': output_temporary + 'CuerposAgua1.shp'})

        # Este shape debe de estar en coordenadas planas, por lo cual se procede a reproyectarlo para tal fin

        processing.run("native:reprojectlayer", {'INPUT':output_temporary + 'CuerposAgua1.shp',
                                                'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:' + str(Numero_EPSG)),
                                                'OUTPUT': output_temporary + 'CuerposAgua.shp'})
        
        #Se procede a crear una nueva columna en el shape de cuerpos de agua
        
        layer = QgsVectorLayer(output_temporary + 'CuerposAgua.shp')
        
        caps = layer.dataProvider().capabilities()
        
        if caps & QgsVectorDataProvider.AddAttributes:
            layer.dataProvider().addAttributes([QgsField("Ancho_p", QVariant.Double)])
            layer.updateFields()
            fields_name = [f.name() for f in layer.fields()]
            fareaidx = fields_name.index('Ancho_p')
        
        #Se procede a llenar la columna con los valores del ancho promedio para cada cuerpo de agua
        
        features = layer.getFeatures()
        
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            for feature in features:
                attrs = {fareaidx : round(2*feature.geometry().area()/feature.geometry().length(), 3)}
                layer.dataProvider().changeAttributeValues({feature.id() : attrs})
        
        layer.endEditCommand()
        
        #print ("Ancho promedio calculado para cada Cuerpo de Agua")

        #Rasterizamos el poligono de Cuerpos de Agua.
        
        toRaster(output_temporary + 'CuerposAgua.shp', DEM, output_temporary + 'CuerposAgua.tif', 'Ancho_p')
        
        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': output_temporary + 'CuerposAgua.tif',
                                                'RASTER_BAND':1,'TABLE':[-100,100,1,100,300,2,300,700,3,700,900,4,900,1200,5,1200,100000,6],
                                                'NO_DATA':-9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                'OUTPUT': output_temporary + 'CruceCuerposAgua.tif'})
        
        processing.run("grass7:r.null", {'map': output_temporary + 'CruceCuerposAgua.tif',
                                        'setnull':'','null':1,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                        'output': salida_vbles + 'vateen1c_' + nom_proyecto + '_crucecuerposagua' + '.tif',
                                        'GRASS_REGION_PARAMETER':None,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                        'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})
                                                
        print ("Variable crucecuerposagua creada")

def DensidadAire(DEM):
    if "densidadaire" in ejecutables:

        processing.run("saga:rastercalculator", {'GRIDS':DEM,'XGRIDS':'',
                                                'FORMULA':'exp((-a/1000)/8.59)','RESAMPLING':0,'USE_NODATA':False,'TYPE':7,
                                                'RESULT': output_temporary + 'den_rel_aire.sdat'})

        #print ("Densidad Relativa del Aire Calculada")

        #Reclasificamos la variable en los rangos dados para esta
            
        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': output_temporary + 'den_rel_aire.sdat',
                                                    'RASTER_BAND':1,'TABLE':[0,0.56,5,0.56,0.79,3,0.79,10000,1],
                                                    'NO_DATA':-9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                    'OUTPUT': salida_vbles + 'vateto1c_' + nom_proyecto + '_densidadaire' + '.tif'})

        print ("Variable Densidad Relativa del Aire creada")

def PteLateral(DEM):
    if "ptelateral" in ejecutables:
        try:
            processing.run("gdal:slope", {'INPUT': DEM,'BAND':1,
                                        'SCALE':1,'AS_PERCENT':False, 'COMPUTE_EDGES':False,'ZEVENBERGEN':False,'OPTIONS':'',
                                        'OUTPUT': output_temporary + 'slope_grados.tif'})
            
            print ("pendiente en grados calculada")
        except:
            print ("pendiente en grados ya se encuentra calculada")
        
        #Luego se reclasifica el raster obtenido

        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': output_temporary + 'slope_grados.tif',
                                                    'RASTER_BAND':1,'TABLE':[0,26,1,26,90,5],
                                                    'NO_DATA':-9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                    'OUTPUT': salida_vbles + 'vateto1c_' + nom_proyecto + '_ptelateral' + '.tif'})

        print ("Variable ptelateral creada")

def PteLongitudinal(DEM):
    if "ptelongitudinal" in ejecutables:

        processing.run("gdal:slope", {'INPUT': DEM,'BAND':1,
                                    'SCALE':1,'AS_PERCENT':True, 'COMPUTE_EDGES':False,'ZEVENBERGEN':False,'OPTIONS':'',
                                    'OUTPUT': output_temporary + 'slope_porc.tif'})
        
        #print ("pendiente en porcentaje calculada")
        
        #Luego se reclasifica el raster obtenido

        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': output_temporary + 'slope_porc.tif',
                                                    'RASTER_BAND':1,'TABLE':[0,10,1,10,20,2,20,40,3,40,60,4,60,10000,5],
                                                    'NO_DATA':-9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                    'OUTPUT': salida_vbles + 'vateto1c_' + nom_proyecto + '_ptelongitudinal' + '.tif'})

        print ("Variable ptelongitudinal creada")

def PteRendConstructivo(DEM):
    if "pterendconstructivo" in ejecutables:
        try:
            processing.run("gdal:slope", {'INPUT': DEM,'BAND':1,
                                        'SCALE':1,'AS_PERCENT':False, 'COMPUTE_EDGES':False,'ZEVENBERGEN':False,'OPTIONS':'',
                                        'OUTPUT': output_temporary + 'slope_grados.tif'})
            
            print ("pendiente en grados calculada")
        except:
            print ("pendiente en grados ya se encuentra calculada")
        
        #Luego se reclasifica el raster obtenido

        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': output_temporary + 'slope_grados.tif',
                                                    'RASTER_BAND':1,'TABLE':[0,5,1,5,13,2,13,26,3,26,40,4,40,90,5],
                                                    'NO_DATA':-9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                    'OUTPUT': salida_vbles + 'vateto1c_' + nom_proyecto + '_pterendconstructivo' + '.tif'})

        print ("Variable pterendconstructivo creada")

def VegAlturaTipo(DEM, Capa_Cobertura_Vegetal, Excel_Cobertura_Vegetal):
    if "vegalturatipo" in ejecutables:
        #Luego, se procede a seleciona los shapes que se encuentran en el extent:
        layer=QgsVectorLayer(Capa_Cobertura_Vegetal)
        layer=QgsProject.instance().addMapLayer(layer, False)
    
        processing.run("native:selectbylocation", {'INPUT':Capa_Cobertura_Vegetal,\
                                                   'PREDICATE':[0,6],\
                                                   'INTERSECT':extent,\
                                                   'METHOD':0})
        
        processing.run("native:saveselectedfeatures",{'INPUT': layer,'OUTPUT': output_temporary + 'CoberturaVeg.shp'})


        #Leemos el archivo excel donde se tiene la informacion referente a las Coberturas Vegetales (tipo de cobertura)

        excel_veg_alt_tipo = pd.read_excel(Excel_Cobertura_Vegetal, sheet_name='Coberturas_vegetacion')

        #Leemos el archivo excel donde se tiene la informacion referente a las Coberturas Vegetales (relación con la Alturasnm)

        excel_alturas = pd.read_excel(Excel_Cobertura_Vegetal, sheet_name='Alturas_vegetacion')

        alturas = excel_alturas['Alturas'].tolist()

        columnas = ['Codigo', 'Cobertura', alturas[0], alturas[1], alturas[2]]
        info = excel_veg_alt_tipo[columnas]
        codigos = excel_veg_alt_tipo['Codigo'].tolist()

        #Se procede a clasificar el DEM en los rangos estipulados para las coberturas vegetales

        processing.run("qgis:reclassifybytable", {'INPUT_RASTER': DEM,'RASTER_BAND':1,
                                                    'TABLE':[-1000,alturas[0],alturas[0],
                                                    alturas[0],alturas[1],alturas[1],
                                                    alturas[1],8000,alturas[2]],
                                                    'NO_DATA':-9999,'RANGE_BOUNDARIES':1,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                    'OUTPUT': output_temporary + 'DEM_veg_reclass.tif'})
                                                
        #print ("DEM clasificado en los rangos de la Cobertura vegetal")

        #Luego se poligoniza el DEM_veg_reclass

        processing.run("gdal:polygonize", {'INPUT': output_temporary + 'DEM_veg_reclass.tif','BAND':1,
                                            'FIELD':'altura','EIGHT_CONNECTEDNESS':False,'EXTRA':'',
                                            'OUTPUT': output_temporary + 'DEM_veg_reclass.shp'})

        #print ("DEM_veg_reclass poligonizado")

        #Luego se debe de intersectar el poligono del DEM_veg_reclass con el poligono de la Cobertura Vegetal

        processing.run("saga:intersect", {'A': output_temporary + 'CoberturaVeg.shp',
                                            'B': output_temporary + 'DEM_veg_reclass.shp',
                                            'SPLIT':False,'RESULT': output_temporary + 'VegAlturaTipo.shp'})

        #print ("Interseccion realizada entre el DEM reclasificado y la cobertura Vegetal")

        #Se procede a generar columna de susceptibilidad de acuerdo al excel, a partir de las columnas altura y CODIGO (o DESCRIPCION)

        layer = QgsVectorLayer(output_temporary + 'VegAlturaTipo.shp')

        caps = layer.dataProvider().capabilities()

        ###Primero se crea la columna donde se va a introducir la susceptibilidad para cada clase

        if caps & QgsVectorDataProvider.AddAttributes:
            layer.dataProvider().addAttributes([QgsField("SCEP", QVariant.Int)])
            layer.updateFields()    
            fields_name = [f.name() for f in layer.fields()]
            idx = fields_name.index('SCEP')
        
        ###Procedemos a llenar los campos de la columna creada SCEP

        features = layer.getFeatures()

        contador = 0

        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            for feature in features:
                contador = contador + 1
                for cod in codigos:
                    if feature['COD_COB'] == cod:
                        #print (cod)
                        indice = codigos.index(cod)
                        for altura in alturas:
                            if feature['altura'] == altura:
                                scep = int(info.at[indice, altura])
                                #print (scep)
                                #Para una zona pequeña, las 2 siguientes filas deben estar alineadas con el if feature['COD_COB'] == cod
                                #Para toda colombia (zona grande), las 2 siguientes filas deben estar dentro del condicional de la altura
                                attrs = {idx : scep}
                                layer.dataProvider().changeAttributeValues({feature.id() : attrs})
                
        layer.endEditCommand()

        #print ("count features:", contador)
        #print ("Vegetacion altura tipo se encuentra clasificado")

        #QgsProject.instance().addMapLayer(layer) #Para ver poligono en QGIS

        #Se rasteriza el resultado

        toRaster(output_temporary + 'VegAlturaTipo.shp', DEM, output_temporary + 'VegAlturaTipo.tif', 'SCEP')

        processing.run("grass7:r.null", {'map': output_temporary + 'VegAlturaTipo.tif',
                                        'setnull':'','null':1,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                        'output': salida_vbles + 'vateen1c_' + nom_proyecto + '_vegalturatipo' + '.tif',
                                        'GRASS_REGION_PARAMETER':None,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                        'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

        print ("Variable vegalturatipo creada")

####----------OBTENCION VARIABLES AVANZADAS ARPEX------------------------------------------------

#Alturasnm(DEM)
#DensidadAire(DEM)
#PteLateral(DEM)
#PteLongitudinal(DEM)
## PteRendConstructivo(DEM)
## VegAlturaTipo(DEM, Capa_Cobertura_Vegetal, Excel_Cobertura_Vegetal)
#CruceCuerposAgua(Capa_Cuerpos_Agua)

###----------------FINAL OBTENCION DE VARIABLES-------------------------------------------

end = timer()
print(end - start,'segundos') # Time in seconds
print ("VARIABLES GENERADAS")
