import glob
import numpy as np
import pandas as pd
import time, arcpy, os
from arcpy.sa import *
from pathlib import Path
from configparser import ConfigParser
from timeit import default_timer as timer

config=ConfigParser()
config.read(r'U:\BRASIL_DSK\BR_2101\PARAMETROS_PROYECTO\ARPEX_TECNICA_00_CONTROL_FILE.ini')
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

def RutaCorredor(folder, raster_cons, pto_inicial, pto_final):
    raster = raster_cons
    metodo = ((raster.split('\\')[-1]).split('.')[0]).split('_')[2] + "_" + ((raster.split('\\')[-1]).split('.')[0]).split('_')[3]

    #raster = Reclassify (raster, "Value", RemapValue([[1,1],[2,2],[3,3],[4,4],[5,5],[10000000,6]]))
    #raster.save ('D:/BRASIL/Lt02_v7_t02/raster_Lt02_v7_t02.tif')

    CostDist1 = CostDistance(pto_inicial, raster)
    #CostDist1.save ('D:/BRASIL/Lt02_v7_t02/CostDist1_Lt02_v7_t02.tif')
    CostDist2 = CostDistance(pto_final, raster)
    #CostDist2.save ('D:/BRASIL/Lt02_v7_t02/CostDist2_Lt02_v7_t02.tif')

    BackLink = CostBackLink(pto_inicial, raster)

    #--------Generacion de la ruta-----------------------------
    if "Ruta" in ejecutables:
        #outCostPath = CostPath(pto_final, CostDist1, BackLink)
        #outCostPath.save (folder + metodo + 'Ruta_r.tif')
        
        CostPathAsPolyline(pto_final, CostDist1, BackLink, folder + nom_proyecto + '_' + metodo + '_Ruta' + '.shp')

        print ("Ruta Generada")

    #--------Generacion del Corredor---------------------------
    if "Corredor" in ejecutables:
        outCorridor = Corridor(CostDist1, CostDist2)
        #outCorridor.save('D:/BRASIL/Lt02_v7_t02/outCorridor_Lt02_v7_t02.tif')

        outSlice = Slice(outCorridor, 100, "EQUAL_INTERVAL")
        #outSlice.save ('D:/BRASIL/Lt02_v7_t02/outSlice_Lt02_v7_t02.tif')

        arcpy.RasterToPolygon_conversion(outSlice, output_temporary + 'outSlice_poly.tif', "SIMPLIFY", "Value", "MULTIPLE_OUTER_PART", None)

        outSlice_poly = arcpy.management.SelectLayerByAttribute("outSlice_poly", "NEW_SELECTION", "gridcode > 0 And gridcode <= 10", None)

        arcpy.CopyFeatures_management (outSlice_poly, folder + nom_proyecto + '_' + metodo + '_Corredor' + '.shp')

        print ("Corredor Generado")

###----------------EJECUCION DEL PROGRAMA (RUTA Y CORREDOR)-------------------------------

start = timer()

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

extent = output_temporary + 'extent.shp'

folder = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/RUTACOR/'
folder_cons = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/CONSOLIDADA/'
pto_inicial = r'%s' %(config['CORREDOR']['pto_inicial'])
pto_final = r'%s' %(config['CORREDOR']['pto_final'])

###------------------OBTENER RASTERS CONSOLIDADOS---------------

lista_cons = []
p = Path(folder_cons)
if 'MaxSimple' in ejecutables:
    for name in p.glob('*MaxSimple*'):
        if str(name).endswith('.tif'):
            a=name
            lista_cons.append(r'%s' %(a))

if 'PromSimple' in ejecutables:
    for name in p.glob('*PromSimple*'):
        if str(name).endswith('.tif'):
            a=name
            lista_cons.append(r'%s' %(a))

if 'MaxPond' in ejecutables:
    for name in p.glob('*MaxPond*'):
        if str(name).endswith('.tif'):
            a=name
            lista_cons.append(r'%s' %(a))

if 'PromPond' in ejecutables:
    for name in p.glob('*PromPond*'):
        if str(name).endswith('.tif'):
            a=name
            lista_cons.append(r'%s' %(a))

if 'MaxFrec' in ejecutables:
    for name in p.glob('*MaxFrec*'):
        if str(name).endswith('.tif'):
            a=name
            lista_cons.append(r'%s' %(a))

if 'SumPond' in ejecutables:
    for name in p.glob('*SumPond*'):
        if str(name).endswith('.tif'):
            a=name
            lista_cons.append(r'%s' %(a))

###-------SE OBTIENE EL CORREDOR Y LA RUTA PARA CADA SUPERFICIE CONSOLIDADA---------
for raster_cons in lista_cons:
    print ((raster_cons.split('\\')[-1]).split('.')[0])
    RutaCorredor(folder, raster_cons, pto_inicial, pto_final)

###------------------OBTENER RUTAS SIMPLIFICADAS---------------

rutas_simplify = folder + 'SIMPLIFY'
os.makedirs(rutas_simplify, exist_ok=True)

lista_rutas= []
p = Path(folder)

for name in p.glob('*Ruta*'):
    if str(name).endswith('.shp'):
        a=name
        lista_rutas.append(r'%s' %(a))

for ruta in lista_rutas:
    nom_ruta = ruta.split('\\')[-1]
    nom_ruta_s = nom_ruta.replace('Ruta', 'RutaSM')
    arcpy.cartography.SimplifyLine(ruta, rutas_simplify + '/' + nom_ruta_s, 
                                    "POINT_REMOVE", "400 Meters", "RESOLVE_ERRORS", "KEEP_COLLAPSED_POINTS", "CHECK", None)
    ###-----------------OBTENER LONGITUD Y NUMERO DE VERTICES DE LA RUTA-------------------
    arcpy.management.AddFields(rutas_simplify + '/' + nom_ruta_s, "longitud DOUBLE # # # #;num_vertix LONG # # # #")
    arcpy.management.CalculateGeometryAttributes(rutas_simplify + '/' + nom_ruta_s, "longitud LENGTH;num_vertix POINT_COUNT", "KILOMETERS", '', None, "SAME_AS_INPUT")

###-----------------------------------------------------------------------------

end = timer()
print(end - start,'segundos') # Time in seconds
print ("RUTAS y/o CORREDORES CALCULADOS")
##verificar cuantos Slice se requieren
