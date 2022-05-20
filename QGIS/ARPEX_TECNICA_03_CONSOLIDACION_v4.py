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

###--------------------CONFIGURACION INICIAL-----------------------------------

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

###--------------------FUNCIONES PARA EL ALGEBRA DE MAPAS----------------------------

def toArray(ruta_variable):
    dataset = gdal.Open(ruta_variable)
    band = dataset.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    array = dataset.ReadAsArray()
    new_array = np.where(array ==nodata, np.nan,array)
    return new_array

def toTiff(new_array, dem, output_ruta):
    dataset=gdal.Open(dem)

    band = dataset.GetRasterBand(1)
    geotransform = dataset.GetGeoTransform()
    wkt = dataset.GetProjection()

    # Create gtif file
    driver = gdal.GetDriverByName("GTiff")
    output_file = output_ruta
    dst_ds = driver.Create(output_file,band.XSize,band.YSize,1, gdal.GDT_Float32)
    #writting output raster
    dst_ds.GetRasterBand(1).WriteArray( new_array )
    #setting nodata value
    dst_ds.GetRasterBand(1).SetNoDataValue(np.nan)
    #setting extension of output raster
    # top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
    dst_ds.SetGeoTransform(geotransform)
    # setting spatial reference of output raster
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    dst_ds.SetProjection( srs.ExportToWkt() )
    #Close output raster dataset
    dataset = None
    dst_ds = None
    return output_file

###--------------------CONSOLIDACION (ALGEBRA DE MAPAS)-----------------------------------------

def MaxSimple (folder, aspecto, lista_vbles = []):
    if "MaxSimple" in ejecutables:
        output_cons = output_temporary + 'MaxSimple_%s.tif' %(aspecto)
        
        processing.run("grass7:r.series", {'input': lista_vbles,
                                                '-n':False,'method':[6],'quantile':'','weights':'','range':[np.nan,np.nan],
                                                'output': output_temporary + 'MaxSimple0_%s.tif' %(aspecto),'GRASS_REGION_PARAMETER':None,
                                                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                                'GRASS_RASTER_FORMAT_META':''})
        
        processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + 'MaxSimple0_%s.tif' %(aspecto),
                                                    'MASK': extent,
                                                    'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                    'NODATA':-999999999,'ALPHA_BAND':False,
                                                    'CROP_TO_CUTLINE':False,
                                                    'KEEP_RESOLUTION':True,
                                                    'SET_RESOLUTION':False,
                                                    'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                    'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':1, 'EXTRA':'',
                                                    'OUTPUT':output_cons})
        
        #Calcular MaxSimple sin modificar clase 6 - restrictiva
        if 'Sin modificar' in restriccion:
            shutil.copy (output_cons, folder)
            os.rename (folder + 'MaxSimple_%s.tif' %(aspecto), folder + nom_proyecto + '_MaxSimple_%s' %(aspecto) + '.tif')
        
        #Calcular MaxSimple modificando clase 6 - restrictiva al valor deseado (valor por defecto: 20)
        if valor_restr in restriccion:
            processing.run("native:reclassifybytable", {'INPUT_RASTER': output_cons,
                                                        'RASTER_BAND':1,'TABLE':[5.5,10,valor_restr],'NO_DATA':241,
                                                        'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':0,
                                                        'OUTPUT': folder + nom_proyecto + '_MaxSimpleR' + str(valor_restr) + '_%s' %(aspecto) + '.tif'})

        #Calcular MaxSimple modificando clase 6 - restrictiva al valor deseado (valor por defecto: 1000)
        if valor_restr2 in restriccion:
            processing.run("native:reclassifybytable", {'INPUT_RASTER':output_cons,
                                                        'RASTER_BAND':1,'TABLE':[5.5,10,valor_restr2],'NO_DATA':241,
                                                        'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':0,
                                                        'OUTPUT': folder + nom_proyecto + '_MaxSimpleR' + str(valor_restr2) + '_%s' %(aspecto) + '.tif'})

        #Calcular MaxSimple modificando clase 6 - restrictiva a NODATA
        if 'NODATA' in restriccion:
            processing.run("grass7:r.null", {'map': output_cons,
                                            'setnull':'6, 241','null':'','-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                            'output': folder + nom_proyecto + '_MaxSimpleND_%s' %(aspecto) + '.tif',
                                            'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                            'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})
        
        print ("Maximo Simple Calculado")

def MaxPond (folder, aspecto, lista_vbles = []):
    if "MaxPond" in ejecutables:

        vbles_maxpond = output_temporary + 'MAXPOND'
        os.makedirs(vbles_maxpond, exist_ok=True)

        if aspecto != 'cons':
            if aspecto == 'te':
                excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio,
                                        sheet_name = 'MaxPond_te')
            if aspecto == 'pr':
                excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio,
                                        sheet_name = 'MaxPond_pr')

            if aspecto == 'am':
                excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio,
                                        sheet_name = 'MaxPond_am')
        
            ponderacion = excel_pond.loc[excel_pond['POR DEFECTO'] == 1]
            lista_pond = ponderacion['FACTOR VARIABLE'].tolist() ##Esta lista es la de los pesos ponderados de las variables 
                                                                    ##incluidas en el analisis (en orden alfabetico).

            #TOMAMOS LAS VARIABLES QUE ENTRARAN AL ANALISIS
            lista_vbles_RMP = []
            p = Path(salida_vbles)

            if aspecto == 'te':
                for name in p.glob('*vate*'):
                    if str(name).endswith('.tif'):
                        a=name
                        lista_vbles_RMP.append(r'%s' %(a))

            if aspecto == 'pr':
                for name in p.glob('*vaprpr*'):
                    if str(name).endswith('.tif'):
                        a=name
                        lista_vbles_RMP.append(r'%s' %(a))

            if aspecto == 'am':
                for name in p.glob('*vaam*'):
                    if str(name).endswith('.tif'):
                        a=name
                        lista_vbles_RMP.append(r'%s' %(a))
            
            df_previo = pd.DataFrame({'VARIABLE': lista_vbles_RMP, 'NOMBRE': lista_nom})
            df = df_previo.sort_values('NOMBRE')
            df ['FACTOR'] = lista_pond

            #PONDERAMOS LAS VARIABLES
            lista_array = []

            for vble in df['VARIABLE']:
                indice = (df['VARIABLE'].tolist()).index(vble)
                # print (vble)
                vble_array = toArray(vble)
                # print(df.iloc[indice]['FACTOR'])
                # print (df.iloc[indice]['NOMBRE'])
                vble_array_pond = vble_array*(df.iloc[indice]['FACTOR'])
                lista_array.append (vble_array_pond)
                toTiff(vble_array_pond, DEM, vbles_maxpond + '/' + str(df.iloc[indice]['NOMBRE']) + '_RMP_%s.tif' %(aspecto))

        #TOMAMOS LAS VARIABLES PONDERADAS
        os.chdir(vbles_maxpond)
        lista_vbles2 = [os.path.abspath(x) for x in os.listdir(vbles_maxpond)]
        lista_vbles_maxpond = []

        if aspecto == 'te':
            for name in lista_vbles2:
                if str(name).endswith('RMP_te.tif'):
                    lista_vbles_maxpond.append(name)

        if aspecto == 'pr':
            for name in lista_vbles2:
                if str(name).endswith('RMP_pr.tif'):
                    lista_vbles_maxpond.append(name)

        if aspecto == 'am':
            for name in lista_vbles2:
                if str(name).endswith('RMP_am.tif'):
                    lista_vbles_maxpond.append(name)

        if aspecto == 'cons':
            p = Path(vbles_maxpond)
            for name in p.glob('*RMP*'):
                if str(name).endswith('.tif'):
                    a=name
                    lista_vbles_maxpond.append(r'%s' %(a))

        #CALCULAMOS EL MAXIMO CON LAS VARIABLES YA PONDERADAS
        output_cons = output_temporary + 'MaxPond_%s.tif' %(aspecto)

        processing.run("grass7:r.series", {'input': lista_vbles_maxpond,
                                        '-n': True,'method':[6],'quantile':'','weights':'','range':[np.nan,np.nan],
                                        'output': output_temporary + 'MaxPond0_%s.tif' %(aspecto),'GRASS_REGION_PARAMETER':None,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

        processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + 'MaxPond0_%s.tif' %(aspecto),
                                                    'MASK': extent,
                                                    'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                    'NODATA':-999999999,'ALPHA_BAND':False,
                                                    'CROP_TO_CUTLINE':False,
                                                    'KEEP_RESOLUTION':True,
                                                    'SET_RESOLUTION':False,
                                                    'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                    'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                    'OUTPUT':output_cons})

        #Calcular MaxPond sin modificar clase 6 - restrictiva
        if 'Sin modificar' in restriccion:
            shutil.copy (output_cons, folder)
            os.rename (folder + 'MaxPond_%s.tif' %(aspecto), folder + nom_proyecto + '_MaxPond_%s' %(aspecto) + '.tif')
        
        #Calcular MaxPond modificando clase 6 - restrictiva al valor deseado (valor por defecto: 20)
        if valor_restr in restriccion:
            processing.run("native:reclassifybytable", {'INPUT_RASTER': output_cons,
                                                        'RASTER_BAND':1,'TABLE':[5.5,10,valor_restr],'NO_DATA':-9999,
                                                        'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                        'OUTPUT': folder + nom_proyecto + '_MaxPondR' + str(valor_restr) + '_%s' %(aspecto) + '.tif'})

        #Calcular MaxPond modificando clase 6 - restrictiva al valor deseado (valor por defecto: 1000)
        if valor_restr2 in restriccion:
            processing.run("native:reclassifybytable", {'INPUT_RASTER':output_cons,
                                                        'RASTER_BAND':1,'TABLE':[5.5,10,valor_restr2],'NO_DATA':-9999,
                                                        'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                        'OUTPUT': folder + nom_proyecto + '_MaxPondR' + str(valor_restr2) + '_%s' %(aspecto) + '.tif'})

        #Calcular MaxPond modificando clase 6 - restrictiva a NODATA
        if 'NODATA' in restriccion:
            processing.run("grass7:r.null", {'map': output_cons,
                                            'setnull':6,'null':'','-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                            'output': folder + nom_proyecto + '_MaxPondND_%s' %(aspecto) + '.tif',
                                            'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                            'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})

        print ("Maximo Ponderado Calculado")

def PromSimple (folder, aspecto, lista_vbles = []):
    if "PromSimple" in ejecutables:
        vbles_RPS = salida_vbles + 'R_PROMSIMPLE'
        os.makedirs(vbles_RPS, exist_ok=True)

        if aspecto != 'cons':
            #colocamos los 6 en null, para que la clase restrictiva no entre en la operacion del promedio
            for vble in lista_vbles:
                processing.run("grass7:r.null", {'map': vble,
                                                'setnull':6,'null':'','-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                                'output': vbles_RPS + '/' + (vble.split('\\')[-1]).split('.')[0] + '_RPS_%s.tif' %(aspecto),
                                                'GRASS_REGION_PARAMETER':None,
                                                'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                                'GRASS_RASTER_FORMAT_OPT':'',
                                                'GRASS_RASTER_FORMAT_META':''})
        
        #TOMAMOS LAS VARIABLES QUE ENTRARAN AL ANALISIS
        os.chdir(vbles_RPS)
        lista_vbles2 = [os.path.abspath(x) for x in os.listdir(vbles_RPS)]
        lista_vbles_RPS = []

        if aspecto == 'te':
            for name in lista_vbles2:
                if str(name).endswith('RPS_te.tif'):
                    lista_vbles_RPS.append(name)

        if aspecto == 'pr':
            for name in lista_vbles2:
                if str(name).endswith('RPS_pr.tif'):
                    lista_vbles_RPS.append(name)

        if aspecto == 'am':
            for name in lista_vbles2:
                if str(name).endswith('RPS_am.tif'):
                    lista_vbles_RPS.append(name)

        if aspecto == 'cons':
            p = Path(vbles_RPS)
            for name in p.glob('*RPS*'):
                if str(name).endswith('.tif'):
                    a=name
                    lista_vbles_RPS.append(r'%s' %(a))

        #CALCULAMOS EL PROMEDIO CON LAS VARIABLES SELECCIONADAS

        processing.run("grass7:r.series", {'input': lista_vbles_RPS,
                                            '-n': True,'method':[0],'quantile':'','weights':'','range':[np.nan,np.nan],
                                            'output': output_temporary + 'PromSimple0_%s.tif' %(aspecto),'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})

        #Calcular PromSimple sin modificar clase 6 - restrictiva
        if 'Sin modificar' in restriccion:
            processing.run("grass7:r.null", {'map': output_temporary + 'PromSimple0_%s.tif' %(aspecto),
                                            'setnull':'','null':6,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                            'output': output_temporary + 'PromSimple_%s.tif' %(aspecto),
                                            'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                            'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})
            
            processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + 'PromSimple_%s.tif' %(aspecto),
                                                        'MASK': extent,
                                                        'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                        'NODATA':-999999999,'ALPHA_BAND':False,
                                                        'CROP_TO_CUTLINE':False,
                                                        'KEEP_RESOLUTION':True,
                                                        'SET_RESOLUTION':False,
                                                        'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                        'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                        'OUTPUT': folder + nom_proyecto + '_PromSimple_%s' %(aspecto) + '.tif'})
        
        #Calcular PromSimple modificando clase 6 - restrictiva al valor deseado (valor por defecto 20)
        if valor_restr in restriccion:
            processing.run("grass7:r.null", {'map': output_temporary + 'PromSimple0_%s.tif' %(aspecto),
                                            'setnull':'','null':valor_restr,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                            'output': output_temporary + '_PromSimpleR' + str(valor_restr) + '_%s' %(aspecto)+ '.tif',
                                            'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                            'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})

            processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + '_PromSimpleR' + str(valor_restr) + '_%s' %(aspecto)+ '.tif',
                                                        'MASK': extent,
                                                        'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                        'NODATA':-999999999,'ALPHA_BAND':False,
                                                        'CROP_TO_CUTLINE':False,
                                                        'KEEP_RESOLUTION':True,
                                                        'SET_RESOLUTION':False,
                                                        'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                        'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                        'OUTPUT': folder + nom_proyecto + '_PromSimpleR' + str(valor_restr) + '_%s' %(aspecto) + '.tif'})

        #Calcular PromSimple modificando clase 6 - restrictiva al valor deseado (valor por defecto 1000)
        if valor_restr2 in restriccion:
            processing.run("grass7:r.null", {'map': output_temporary + 'PromSimple0_%s.tif' %(aspecto),
                                            'setnull':'','null':valor_restr,'-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                            'output': output_temporary + '_PromSimpleR' + str(valor_restr2) + '_%s' %(aspecto)+ '.tif',
                                            'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                            'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})

            processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + '_PromSimpleR' + str(valor_restr2) + '_%s' %(aspecto)+ '.tif',
                                                        'MASK': extent,
                                                        'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                        'NODATA':-999999999,'ALPHA_BAND':False,
                                                        'CROP_TO_CUTLINE':False,
                                                        'KEEP_RESOLUTION':True,
                                                        'SET_RESOLUTION':False,
                                                        'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                        'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                        'OUTPUT': folder + nom_proyecto + '_PromSimpleR' + str(valor_restr2) + '_%s' %(aspecto) + '.tif'})
        
        #Calcular PromSimple modificando clase 6 - restrictiva a NODATA
        if 'NODATA' in restriccion:
            processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + 'PromSimple0_%s.tif' %(aspecto),
                                                        'MASK': extent,
                                                        'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                        'NODATA':-999999999,'ALPHA_BAND':False,
                                                        'CROP_TO_CUTLINE':False,
                                                        'KEEP_RESOLUTION':True,
                                                        'SET_RESOLUTION':False,
                                                        'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                        'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                        'OUTPUT': folder + nom_proyecto + '_PromSimpleND_%s' %(aspecto) + '.tif'})

        print ("Promedio Simple Calculado")

def PromPond (folder, aspecto, lista_vbles = []):
    if "PromPond" in ejecutables:

        vbles_prompond = output_temporary + 'PROMPOND'
        os.makedirs(vbles_prompond, exist_ok=True)

        if aspecto != 'cons':
            if aspecto == 'te':
                excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + matriz_ahp_te,
                                        sheet_name = 'PromPond_te')

            if aspecto == 'pr':
                excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + matriz_ahp_pr,
                                        sheet_name = 'PromPond_pr')

            if aspecto == 'am':
                excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + matriz_ahp_am,
                                        sheet_name = 'PromPond_am')

            ponderacion = excel_pond.loc[excel_pond['POR DEFECTO'] == 1]
            lista_pond = ponderacion['FACTOR AHP'].tolist() ##Esta lista es la de los pesos ponderados de las variables 
                                                                    ##incluidas en el analisis (en orden alfabetico).
                        
            #TOMAMOS LAS VARIABLES QUE ENTRARAN AL ANALISIS
            lista_vbles_RPP = []
            p = Path(salida_vbles)

            if aspecto == 'te':
                for name in p.glob('*vate*'):
                    if str(name).endswith('.tif'):
                        a=name
                        lista_vbles_RPP.append(r'%s' %(a))

            if aspecto == 'pr':
                for name in p.glob('*vaprpr*'):
                    if str(name).endswith('.tif'):
                        a=name
                        lista_vbles_RPP.append(r'%s' %(a))

            if aspecto == 'am':
                for name in p.glob('*vaam*'):
                    if str(name).endswith('.tif'):
                        a=name
                        lista_vbles_RPP.append(r'%s' %(a))
            
            df_previo = pd.DataFrame({'VARIABLE': lista_vbles_RPP, 'NOMBRE': lista_nom})
            df = df_previo.sort_values('NOMBRE')
            df ['FACTOR'] = lista_pond

            #PONDERAMOS LAS VARIABLES
            lista_array = []

            for vble in df['VARIABLE']:
                indice = (df['VARIABLE'].tolist()).index(vble)
                # print (vble)
                vble_array = toArray(vble)
                # print(df.iloc[indice]['FACTOR'])
                # print (df.iloc[indice]['NOMBRE'])
                vble_array_pond = vble_array*(df.iloc[indice]['FACTOR'])
                lista_array.append (vble_array_pond)
                toTiff(vble_array_pond, DEM, vbles_prompond + '/' + str(df.iloc[indice]['NOMBRE']) + '_RPP_%s.tif' %(aspecto))

        #TOMAMOS LAS VARIABLES PONDERADAS
        os.chdir(vbles_prompond)
        lista_vbles2 = [os.path.abspath(x) for x in os.listdir(vbles_prompond)]
        lista_vbles_prompond = []

        if aspecto == 'te':
            for name in lista_vbles2:
                if str(name).endswith('RPP_te.tif'):
                    lista_vbles_prompond.append(name)

        if aspecto == 'pr':
            for name in lista_vbles2:
                if str(name).endswith('RPP_pr.tif'):
                    lista_vbles_prompond.append(name)

        if aspecto == 'am':
            for name in lista_vbles2:
                if str(name).endswith('RPP_am.tif'):
                    lista_vbles_prompond.append(name)

        if aspecto == 'cons':
            p = Path(vbles_prompond)
            for name in p.glob('*RPP*'):
                if str(name).endswith('.tif'):
                    a=name
                    lista_vbles_prompond.append(r'%s' %(a))

        #CALCULAMOS EL PROMEDIO CON LAS VARIABLES YA PONDERADAS
        output_cons = output_temporary + 'PromPond_%s.tif' %(aspecto)

        processing.run("grass7:r.series", {'input': lista_vbles_prompond,
                                        '-n': True,'method':[0],'quantile':'','weights':'','range':[np.nan,np.nan],
                                        'output': output_temporary + 'PromPond0_%s.tif' %(aspecto),'GRASS_REGION_PARAMETER':None,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

        processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + 'PromPond0_%s.tif' %(aspecto),
                                                    'MASK': extent,
                                                    'SOURCE_CRS':None, 'TARGET_CRS':None,
                                                    'NODATA':-999999999,'ALPHA_BAND':False,
                                                    'CROP_TO_CUTLINE':False,
                                                    'KEEP_RESOLUTION':True,
                                                    'SET_RESOLUTION':False,
                                                    'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                    'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                    'OUTPUT':output_cons})

        #Calcular PromPond sin modificar clase 6 - restrictiva
        if 'Sin modificar' in restriccion:
            shutil.copy (output_cons, folder)
            os.rename (folder + 'PromPond_%s.tif' %(aspecto), folder + nom_proyecto + '_PromPond_%s' %(aspecto) + '.tif')
        
        #Calcular PromPond modificando clase 6 - restrictiva al valor deseado (valor por defecto: 20)
        if valor_restr in restriccion:
            processing.run("native:reclassifybytable", {'INPUT_RASTER': output_cons,
                                                        'RASTER_BAND':1,'TABLE':[5.5,10,valor_restr],'NO_DATA':-9999,
                                                        'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                        'OUTPUT': folder + nom_proyecto + '_PromPondR' + str(valor_restr) + '_%s' %(aspecto) + '.tif'})

        #Calcular PromPond modificando clase 6 - restrictiva al valor deseado (valor por defecto: 1000)
        if valor_restr2 in restriccion:
            processing.run("native:reclassifybytable", {'INPUT_RASTER':output_cons,
                                                        'RASTER_BAND':1,'TABLE':[5.5,10,valor_restr2],'NO_DATA':-9999,
                                                        'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':3,
                                                        'OUTPUT': folder + nom_proyecto + '_PromPondR' + str(valor_restr2) + '_%s' %(aspecto) + '.tif'})

        #Calcular PromPond modificando clase 6 - restrictiva a NODATA
        if 'NODATA' in restriccion:
            processing.run("grass7:r.null", {'map': output_cons,
                                            'setnull':6,'null':'','-f':False,'-i':False,'-n':False,'-c':False,'-r':False,
                                            'output': folder + nom_proyecto + '_PromPondND_%s' %(aspecto) + '.tif',
                                            'GRASS_REGION_PARAMETER':None,
                                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                                            'GRASS_RASTER_FORMAT_OPT':'',
                                            'GRASS_RASTER_FORMAT_META':''})
                            
        print ("Promedio Ponderado Calculado")

def SumPond (folder, aspecto, lista_vbles = []):
    if "SumPond" in ejecutables:

        vbles_sumpond = output_temporary + 'SUMPOND'
        os.makedirs(vbles_sumpond, exist_ok=True)

        if aspecto == 'cons':
            excel_pond = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio,
                                        sheet_name = 'SumPond')

        ponderacion = excel_pond.loc[excel_pond['POR DEFECTO'] == 1]
        lista_pond = ponderacion['FACTOR VARIABLE'].tolist() ##Esta lista es la de los pesos ponderados de las variables 
                                                                ##incluidas en el analisis (en orden alfabetico).
        lista_nom = ponderacion['VARIABLES'].tolist()

        #TOMAMOS LAS VARIABLES QUE ENTRARAN AL ANALISIS
        lista_vbles_RSP = []
        p = Path(salida_vbles)

        for name in p.glob('*va*'):
            if str(name).endswith('.tif'):
                a=name
                lista_vbles_RSP.append(r'%s' %(a))
       
        df = pd.DataFrame({'VARIABLE': lista_vbles_RSP}) #, 'NOMBRE': lista_nom})
        # df = df_previo.sort_values('NOMBRE')
        df ['FACTOR'] = lista_pond
        df ['NOMBRE'] = lista_nom
        # df.to_excel (r'd:\ambiente\escritorio\excel_df.xlsx')

        #PONDERAMOS LAS VARIABLES
        lista_array = []

        for vble in df['VARIABLE']:
            indice = (df['VARIABLE'].tolist()).index(vble)
            # print (vble)
            vble_array = toArray(vble)
            # print(df.iloc[indice]['FACTOR'])
            # print (df.iloc[indice]['NOMBRE'])
            vble_array_pond = vble_array*(df.iloc[indice]['FACTOR'])
            lista_array.append (vble_array_pond)
            toTiff(vble_array_pond, DEM, vbles_sumpond + '/' + str(df.iloc[indice]['NOMBRE']) + '_RSP_%s.tif' %(aspecto))

        #TOMAMOS LAS VARIABLES PONDERADAS
        os.chdir(vbles_sumpond)
        lista_vbles_sumpond = []

        if aspecto == 'cons':
            p = Path(vbles_sumpond)
            for name in p.glob('*RSP*'):
                if str(name).endswith('.tif'):
                    a=name
                    lista_vbles_sumpond.append(r'%s' %(a))

        #CALCULAMOS LA SUMA CON LAS VARIABLES YA PONDERADAS
        output_cons = output_temporary + 'SumPond_%s.tif' %(aspecto)

        processing.run("grass7:r.series", {'input': lista_vbles_sumpond,
                                        '-n': True,'method':[10],'quantile':'','weights':'','range':[np.nan,np.nan],
                                        'output': output_temporary + 'SumPond0_%s.tif' %(aspecto),'GRASS_REGION_PARAMETER':None,
                                        'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                        'GRASS_RASTER_FORMAT_META':''})

        processing.run("gdal:cliprasterbymasklayer", {'INPUT': output_temporary + 'SumPond0_%s.tif' %(aspecto),
                                                    'MASK': extent,
                                                    'SOURCE_CRS':None,
                                                    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:' + sistema_coord),
                                                    'NODATA':-999999999,'ALPHA_BAND':False,
                                                    'CROP_TO_CUTLINE':False,
                                                    'KEEP_RESOLUTION':True,
                                                    'SET_RESOLUTION':False,
                                                    'X_RESOLUTION':None,'Y_RESOLUTION':None,
                                                    'MULTITHREADING':False, 'OPTIONS':'', 'DATA_TYPE':0, 'EXTRA':'',
                                                    'OUTPUT':output_cons})

        #Calcular SumPond sin modificar clase 6 - restrictiva
        shutil.copy (output_cons, folder)
        os.rename (folder + 'SumPond_%s.tif' %(aspecto), folder + nom_proyecto + '_SumPond_%s' %(aspecto) + '.tif')
        
        print ("Suma Ponderada Calculado")

####--------------CONFIGURACION DEL ARPEX-------------------------------------------

excel_default = pd.read_excel(ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/PARAMETRO/' + excel_inicio)
#Para obtener los metodos y variables que se ejecutan del excel de default:
default = excel_default.loc[excel_default['POR DEFECTO'] == 1]
ejecutables = default['VARIABLES'].tolist()
#Para obtener el valor de reclasificacion de la clase restrictiva (clase 6):
restrictiva = excel_default.loc[excel_default['ACTIVAR'] == 1]
restriccion = restrictiva['VALOR'].tolist()
valor_restr = excel_default['VALOR'][1]
valor_restr2 = excel_default['VALOR'][2]
#Para obtener cuales superficies consolidadas se quieren calcular:
superficies_posibles = excel_default.loc[excel_default['VALOR'] == 1]
superficies_selecc = superficies_posibles['VALOR RESTRICCIONES'].tolist()

folder = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/CONSOLIDADA/'

DEM = output_temporary + 'dem_clip.tif'
extent = output_temporary + 'extent.shp'

###-------------EJECUCION PROGRAMA (ALGEBRA DE MAPAS) AMBIENTAL----------------------

###------------OBTENCION VARIABLE RESTRICCION INFRAESTRUCTURA--------------------------

# Esta variable se obtiene con el fin de incluir en todas las superficies consolidadas,
# la infraestructura de la zona del proyecto, ademas de los centros poblados.

lista_vbles_inf = []
lista_nom = []
p = Path(salida_vbles)
for name in p.glob('*vatein*'):
   if str(name).endswith('.tif'):
       a=name
       lista_vbles_inf.append(r'%s' %(a))
       nom_vble = (((r'%s' %(a)).split('\\')[-1]).split('.')[0]).split('_')[3]
       lista_nom.append(nom_vble)

if 'infraestructura' in ejecutables:
   processing.run("grass7:r.series", {'input': lista_vbles_inf,
                                      '-n':False,'method':[6],'quantile':'','weights':'','range':[np.nan,np.nan],
                                      'output': output_temporary + 'vatein1c_' + nom_proyecto + '_infraestructura' + '.tif',
                                      'GRASS_REGION_PARAMETER':None,
                                      'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                      'GRASS_RASTER_FORMAT_META':''})
   
   shutil.copy (output_temporary + 'vatein1c_' + nom_proyecto + '_infraestructura' + '.tif', salida_vbles)
   os.rename (salida_vbles + 'vatein1c_' + nom_proyecto + '_infraestructura' + '.tif', salida_vbles + 'vaamin1c_' + nom_proyecto + '_infraestructura' + '.tif')

   shutil.copy (output_temporary + 'vatein1c_' + nom_proyecto + '_infraestructura' + '.tif', salida_vbles)
   os.rename (salida_vbles + 'vatein1c_' + nom_proyecto + '_infraestructura' + '.tif', salida_vbles + 'vaprpr1c_' + nom_proyecto + '_infraestructura' + '.tif')

#Centros Poblados

p = Path(salida_vbles)
if 'centrospoblados' in ejecutables:
    for name in p.glob('*centrospoblados*'):
        if str(name).endswith('.tif'):
            a=name
            centros_poblados = r'%s' %(a)

    shutil.copy (centros_poblados, output_temporary)
    os.rename (output_temporary + 'vaprpr2c_' + nom_proyecto + '_centrospoblados' + '.tif', output_temporary + 'vatepr2c_' + nom_proyecto + '_centrospoblados' + '.tif')
    shutil.copy (output_temporary + 'vatepr2c_' + nom_proyecto + '_centrospoblados' + '.tif', salida_vbles)

    shutil.copy (centros_poblados, output_temporary)
    os.rename (output_temporary + 'vaprpr2c_' + nom_proyecto + '_centrospoblados' + '.tif', output_temporary + 'vaampr2c_' + nom_proyecto + '_centrospoblados' + '.tif')
    shutil.copy (output_temporary + 'vaampr2c_' + nom_proyecto + '_centrospoblados' + '.tif', salida_vbles)

###--------LISTA OBTENCION INFRAESTRUCTURA Y CENTROS POBLADOS-------------###


#TOMAMOS LAS VARIABLES AMBIENTALES PARA CALCULAR LA SUPERFICIE CONSOLIDADA AMBIENTAL
lista_vbles_am2 = []
lista_nom = []
p = Path(salida_vbles)
for name in p.glob('*vaam*'):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles_am2.append(r'%s' %(a))
        nom_vble = (((r'%s' %(a)).split('\\')[-1]).split('.')[0]).split('_')[3]
        lista_nom.append(nom_vble)

if 'Ambiental' in superficies_selecc:
    MaxSimple (folder, 'am', lista_vbles_am2)
    MaxPond (folder, 'am', lista_vbles_am2)
    PromSimple (folder, 'am', lista_vbles_am2)
    PromPond (folder, 'am', lista_vbles_am2)
    SumPond (folder, 'am', lista_vbles_am2)

    print ("SUPERFICIES CONSOLIDADAS (ASPECTO AMBIENTAL) GENERADAS")

###------------OBTENCION VARIABLE RESTRICCION AMBIENTAL--------------------------

# Esta variable se obtiene luego de realizar la consolidacion ambiental,
# tomando solamente las zonas calificadas como 5 (criticidad alta) y 6 (restrictivas).

if 'restramb' in ejecutables:
   processing.run("grass7:r.series", {'input': lista_vbles_am2,
                                       '-n':False,'method':[6],'quantile':'','weights':'','range':[np.nan,np.nan],
                                       'output': output_temporary + 'vateam1c_' + nom_proyecto + '_restramb' + '.tif',
                                       'GRASS_REGION_PARAMETER':None,
                                       'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
                                       'GRASS_RASTER_FORMAT_META':''})
   
   processing.run("native:reclassifybytable", {'INPUT_RASTER': output_temporary + 'vateam1c_' + nom_proyecto + '_restramb' + '.tif',
                                               'RASTER_BAND':1,
                                               'TABLE':[0,4.9,1],
                                               'NO_DATA':-9999,
                                               'RANGE_BOUNDARIES':0,
                                               'NODATA_FOR_MISSING':False,
                                               'DATA_TYPE':0,
                                               'OUTPUT': salida_vbles + 'vateam1c_' + nom_proyecto + '_restramb' + '.tif'})

   processing.run("native:reclassifybytable", {'INPUT_RASTER': output_temporary + 'vateam1c_' + nom_proyecto + '_restramb' + '.tif',
                                               'RASTER_BAND':1,
                                               'TABLE':[0,4.9,1],
                                               'NO_DATA':-9999,
                                               'RANGE_BOUNDARIES':0,
                                               'NODATA_FOR_MISSING':False,
                                               'DATA_TYPE':0,
                                               'OUTPUT': salida_vbles + 'vaprpr1c_' + nom_proyecto + '_restramb' + '.tif'})

####----------EJECUCION DEL PROGRAMA (ALGEBRA DE MAPAS) TECNICA---------------------------------

#TOMAMOS LAS VARIABLES TECNICAS PARA CALCULAR LA SUPERFICIE CONSOLIDADA TECNICA
lista_vbles_te = []
lista_nom = []
p = Path(salida_vbles)
for name in p.glob('*vate*'):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles_te.append(r'%s' %(a))
        nom_vble = (((r'%s' %(a)).split('\\')[-1]).split('.')[0]).split('_')[3]
        lista_nom.append(nom_vble)

if 'Tecnica' in superficies_selecc:
    MaxSimple (folder, 'te', lista_vbles_te)
    MaxPond (folder, 'te', lista_vbles_te)
    PromSimple (folder, 'te', lista_vbles_te)
    PromPond (folder, 'te', lista_vbles_te)
    SumPond (folder, 'te', lista_vbles_te)

    print ("SUPERFICIES CONSOLIDADAS (ASPECTO TECNICO) GENERADAS")

###-------------EJECUCION PROGRAMA (ALGEBRA DE MAPAS) PREDIAL----------------------

#TOMAMOS LAS VARIABLES PREDIALES PARA CALCULAR LA SUPERFICIE CONSOLIDADA PREDIAL
lista_vbles_pr2 = []
lista_nom = []
p = Path(salida_vbles)
for name in p.glob('*prpr*'):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles_pr2.append(r'%s' %(a))
        nom_vble = (((r'%s' %(a)).split('\\')[-1]).split('.')[0]).split('_')[3]
        lista_nom.append(nom_vble)

if 'Predial' in superficies_selecc:
    MaxSimple (folder, 'pr', lista_vbles_pr2)
    MaxPond (folder, 'pr', lista_vbles_pr2)
    PromSimple (folder, 'pr', lista_vbles_pr2)
    PromPond (folder, 'pr', lista_vbles_pr2)
    SumPond (folder, 'pr', lista_vbles_pr2)

    print ("SUPERFICIES CONSOLIDADAS (ASPECTO PREDIAL) GENERADAS")

####----------EJECUCION DEL PROGRAMA (ALGEBRA DE MAPAS) CONSOLIDADA------------------------------------

lista_vbles_cons = lista_vbles_te + lista_vbles_pr2 + lista_vbles_am2

folder = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/CONSOLIDADA/'

DEM = output_temporary + 'dem_clip.tif'

if 'Consolidada' in superficies_selecc:
    MaxSimple (folder, 'cons', lista_vbles_cons)
    MaxPond (folder, 'cons', lista_vbles_cons)
    PromSimple (folder, 'cons', lista_vbles_cons)
    PromPond (folder, 'cons', lista_vbles_cons)
    SumPond (folder, 'cons', lista_vbles_cons)

    print ("SUPERFICIES CONSOLIDADAS (CONSOLIDADA) GENERADAS")

###-----------------------------------------------------------

end = timer()
print(end - start,'segundos') # Time in seconds
print('Proceso terminado')