import pandas as pd
import glob
import shutil
import os
import numpy as np
import pandas as pd
import time, arcpy, os
from arcpy.sa import *
from pathlib import Path
from configparser import ConfigParser
from timeit import default_timer as timer

start = timer()

# Carpeta donde estan las variables en rasters, de donde se obtendran los datos para los indicadores
folder_rasters = r'T:\PERU\PE_CEPI\PE_CEPI_v04_20211129\SALIDA\VARIABLE_R'

# Carpeta donde se guardan las carpetas creadas para los rasters recortados por la alternativa
folder_resultado = r'T:\PERU\PE_CEPI\PE_CEPI_v04_20211129\SALIDA\INDICADORES'

# Carpeta donde se guardan las alternativas a sacar los indicadores
folder_rutas = r'T:\PERU\PE_CEPI\PE_CEPI_v04_20211129\SALIDA\INDICADORES\RUTAS_INDICADORES'

# Direccion de la alternativa a analizar
ruta_arpex = r'T:\PERU\PE_CEPI\PE_CEPI_v04_20211129\SALIDA\RUTACOR\SIMPLIFY\PE_CEPI_MaxFrec_am_RutaSM.shp'

# Version ruta ARPEX (Version de la superficie ARPEX, de donde se requieren sacar los indicadores)
version_ruta = 'S04'
proyecto_ruta = 'CEPI'

### Creamos las carpetas y copiamos las rutas que se les sacara los indicadores (con los cambios de nombres requeridos)
## Normalmente se trabaja con las rutas obtenidas de las superficies consolidadas

try:
    if ruta_arpex.split('\\')[-1].split('.')[0].split('_')[2] == 'MaxSimpleR20':
        if ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'cons':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMS_CO'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
        elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'am':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMS_AM'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
        elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'pr':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMS_PR'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
        elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'te':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMS_TE'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
    elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[2] == 'MaxFrec':
        if ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'cons':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMF_CO'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
        elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'am':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMF_AM'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
        elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'pr':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMF_PR'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
        elif ruta_arpex.split('\\')[-1].split('.')[0].split('_')[3] == 'te':
            nom_ruta_ind = version_ruta + '_' + proyecto_ruta + '_ARPMF_TE'
            arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
    else:
        nom_ruta_ind = version_ruta + '_' + ruta_arpex.split('\\')[-1].split('.')[0]        
        arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')
except:
    nom_ruta_ind = version_ruta + '_' + ruta_arpex.split('\\')[-1].split('.')[0]
    arcpy.conversion.FeatureClassToFeatureClass(ruta_arpex, folder_rutas, nom_ruta_ind, '', '')

folder_raster_ruta = folder_resultado + '\\' + nom_ruta_ind
os.makedirs(folder_raster_ruta, exist_ok=True)

###--- INICIO PROCESO INDICADORES ---###
lista_vbles = []
p = Path(folder_rasters)
proyecto_rasters = '*' + proyecto_ruta + '*'

for name in p.glob(proyecto_rasters):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles.append(r'%s' %(a))

for vble in lista_vbles:

    extract_pixel = arcpy.sa.ExtractByMask(vble, ruta_arpex) 
    extract_pixel.save(folder_raster_ruta + '/' + (vble.split('\\')[-1]).split('.')[0] + '.tif')
   
    print ((vble.split('\\')[-1]).split('.')[0])

end = timer()
print(end - start,'segundos') # Time in seconds
print ("EXTRAIDAS Y EXPORTADAS")
