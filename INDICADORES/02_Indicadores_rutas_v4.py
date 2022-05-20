import glob
import gdal
import time, os
from os import path
import matplotlib
import numpy as np
import pandas as pd
from pathlib import Path
from functools import reduce
from configparser import ConfigParser
from timeit import default_timer as timer
from statistics import mode
import matplotlib as mpl
mpl.use('Qt5Agg')
import matplotlib.pyplot as plt

start = timer()

# Carpeta con las rutas a sacar los indicadores
rutas = r'T:\PERU\PE_TOCE3\PE_TOCE3_v04_20211129\SALIDA\INDICADORES\RUTAS_INDICADORES'

# Carpeta donde se guarda el excel con los indicadores
folder_resultado = r'T:\PERU\PE_TOCE3\PE_TOCE3_v04_20211129\SALIDA\INDICADORES'

# Proyecto que se esta ejecutando
proyecto = folder_resultado.split('\\')[2]

direct = Path(rutas)
for name in direct.glob('*.shp'):
    ruta_arpex = str(name)
    vlayer = QgsVectorLayer(ruta_arpex)
    features=vlayer.getFeatures()
    for i in features:
        geom = i.geometry()
        longitud= geom.length()


    pixel_size = 90

    rasters = []
    x=ruta_arpex.split("\\")[-1].split(".")[0]
    folder=folder_resultado+'/'+x     # Carpeta donde estan los rasters ya recortados por las rutas
    p = Path(folder)
    


    for name in p.glob('*.tif'):
        omitir=['vaprpr1c_' + proyecto + '_infraestructura', 'vatepr2c_' + proyecto + '_centrospoblados',\
        'vateam1c_' + proyecto + '_restramb','vaprpr1c_' + proyecto + '_restramb',\
        'vaampr2c_' + proyecto + '_centrospoblados','vaamin1c_' + proyecto + '_infraestructura']
        nomb=str(name).split('\\')[-1].split('.')[0]
        if nomb not in omitir:
            rasters.append(str(name))
##########################
    dataset = gdal.Open(rasters[0])
    band = dataset.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    array = dataset.ReadAsArray()
    new_array = np.where(array ==nodata, np.nan,array)
    scep6 = np.count_nonzero(new_array == 6)
    scep5 = np.count_nonzero(new_array == 5)
    scep4 = np.count_nonzero(new_array == 4)
    scep3 = np.count_nonzero(new_array == 3)
    scep2 = np.count_nonzero(new_array == 2)
    scep1 = np.count_nonzero(new_array == 1)
    suma_pixel=(scep6+scep5+scep4+scep3+scep2+scep1)*pixel_size
    a=(pixel_size-((abs(suma_pixel-longitud))/(suma_pixel/90)))

##########################

    prueba=[]
    lista_data = []
    dic={'am':'ambiental','pr':'predial','te':'tecnico'}
    dim={'ab':'abiotico','bi':'biotico','ec':'economico',\
    'cu':'cultural','pr':'predial','in':'infraestructura','en':'elementos naturales',\
    'to':'terreno', 'su':'terreno','po':'politico', 'ac':'infraestructura', 'am':'atmosferica'}

    for raster in rasters:
        dataset = gdal.Open(raster)
        band = dataset.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        array = dataset.ReadAsArray()
        new_array = np.where(array ==nodata, np.nan,array)
        nombre = raster.split('\\')[-1].split('.')[0]
        aspecto=dic[nombre.split('_')[0][2:4]]
        dimension=dim[nombre.split('_')[0][4:6]]
        nombre_var =nombre.split('_')[3]
        print(dimension, nombre)
        scep6 = np.count_nonzero(new_array == 6)*a
        scep5 = np.count_nonzero(new_array == 5)*a
        scep4 = np.count_nonzero(new_array == 4)*a
        scep3 = np.count_nonzero(new_array == 3)*a
        scep2 = np.count_nonzero(new_array == 2)*a
        scep1 = np.count_nonzero(new_array == 1)*a
        sum=scep6+scep5+scep4+scep3+scep2+scep1
        prueba.append(sum)
        if scep6 or scep5 != 0:
            data = [aspecto, dimension, nombre_var, scep6/1000, scep5/1000, scep4, scep3, scep2, scep1] # Divido 1000 para Km
            lista_data.append(data)
        else:
            pass

    df = pd.DataFrame(lista_data, columns=['aspecto', 'dimension', 'variable', f'{x}R', f'{x}C', 'scep4','scep3', 'scep2', 'scep1'])
    df_filtro=df[['aspecto', 'dimension', 'variable', f'{x}R', f'{x}C']]

    ## Agregamos la Longitud de la alternativa al inicio del dataframe que sera exportado a excel
    top_row = pd.DataFrame({'aspecto':[''],'dimension':[''],'variable':[''], f'{x}R':[longitud/1000], f'{x}C':[longitud/1000]})
    # Concat with old DataFrame and reset the Index.
    df_filtro = pd.concat([top_row, df_filtro]).reset_index(drop = True)

    df_filtro.index.rename('ID', inplace=True)
    df_filtro.to_excel(f'{folder_resultado}/{x}.xlsx', index = True)

###--- UNION Y COMPILACION DE TODOS LOS INDICADORES DE LAS ALTERNATIVAS ANALIZADAS ---### 
data_frames = []
p = Path(folder_resultado)

for name in p.glob('*xlsx*'):
    try:
        # Se coloca en try, except porque hace todo bien, pero reporta una falla extraña al final. Esto permite continuar.
        df = pd.read_excel(name, index_col=0)
        data_frames.append(df)
    except:
        pass

# Este codigo tambien lee los data frames, pero raramente falla (funciona con la prueba en PE_RECA_v2)
# data_frames = [pd.read_excel(path.join(folder_resultado,x), index_col=0) for x in os.listdir(folder_resultado) if path.isfile(path.join(folder_resultado,x))]

df_merged = reduce(lambda  left,right: pd.merge(left,right,on=['aspecto', 'dimension','variable'],
                                            how='outer'), data_frames)

df_merged.sort_values(by=['aspecto', 'dimension', 'variable'], na_position='first', inplace=True)
df_merged.reset_index(drop = True, inplace =True)
df_merged.index.rename('ID', inplace=True)
df_merged.to_excel(folder_resultado + '/' + 'Indicadores.xlsx', index = True)


end = timer()
print(end - start,'segundos') # Time in seconds
print ("EXTRAIDAS Y EXPORTADAS")


