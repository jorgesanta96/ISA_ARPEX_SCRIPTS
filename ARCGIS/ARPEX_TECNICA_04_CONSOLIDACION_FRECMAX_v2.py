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
excel_inicio = r'%s' %(config['GENERAL']['excel_default'])
matriz_ahp_te = r'%s' %(config['GENERAL']['matriz_ahp_te'])
matriz_ahp_pr = r'%s' %(config['GENERAL']['matriz_ahp_pr'])
matriz_ahp_am = r'%s' %(config['GENERAL']['matriz_ahp_am'])
version_proyecto = r'%s' %(config['GENERAL']['version_proyecto'])
output_temporary = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/TEMPORAL/'
salida_vbles = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/VARIABLE_R/'

###----------------DEFINICION DE FUNCIONES-------------------------------------------------

def FrecPorMaximos (folder, aspecto, lista_vbles = []):
    if "MaxFrec" in ejecutables:
        
        raster_cons_0 = arcpy.sa.CellStatistics(lista_vbles, "MAXIMUM", "DATA")
        raster_cons_0.save(output_temporary + 'MaxFrec_max_%s.tif' %(aspecto))
        raster_cons = arcpy.sa.ExtractByMask(output_temporary + 'MaxFrec_max_%s.tif' %(aspecto), extent)
        raster_cons.save(output_temporary + 'MaxFrec_maxR_%s.tif' %(aspecto))
        raster_consolidado = arcpy.sa.Int(output_temporary + 'MaxFrec_maxR_%s.tif' %(aspecto))
                    
        frequency = arcpy.sa.EqualToFrequency(raster_consolidado, lista_vbles) 
        frequency.save(output_temporary + 'frequency_%s.tif' %(aspecto))

        arcpy.sa.ZonalStatisticsAsTable(raster_consolidado, "Value", frequency, 
                                        output_temporary + 'Max_frec_%s' %(aspecto), 
                                        "DATA", "MAXIMUM", "CURRENT_SLICE")
        
        arcpy.management.Sort('Max_frec_%s' %(aspecto), output_temporary + 'Max_frecuencia_%s' %(aspecto), "VALUE ASCENDING", "UR")

        arcpy.conversion.TableToTable(output_temporary + 'Max_frecuencia_%s' %(aspecto), output_temporary, "Max_Frecuencia_%s.csv" %(aspecto)) 
        #arcpy.TableToTable_conversion(r"D:\CAPAS\capas_pr2\Max_frecuencia", r"D:\CAPAS\capas_pr2", "Max_Frecuencia.csv")
        
        #Se calcula el umbral inferior para cada criticidad
        max_frecuencia = pd.read_csv(output_temporary + "Max_Frecuencia_%s.csv" %(aspecto))
        #print(max_frecuencia.columns)

        ### --- COLOCAR LAS RESTRICCIONES DE 6 COMO 20 --- ###
        max_frecuencia['VALUE'] = max_frecuencia['VALUE'].replace(6,20)
        ####

        n = max_frecuencia['VALUE'].count()
        #print (n)

        ######Calculo del raster de umbral inferior para el calculo de la reclasificacion.

        lista_remap =[]
        max_frec=[]
        m = 0

        while m <= (len(range(n))-1):
            #print (m)
            if m == 0:
                max_frec.append(max_frecuencia['VALUE'][m])
            elif m == 1:
                max_frec.append((max_frec[m-1] + max_frecuencia['VALUE'][m-1] * max_frecuencia['MAX'][m-1]))
            else:
                max_frec.append((max_frec[m-1] + max_frecuencia['VALUE'][m-1] * max_frecuencia['MAX'][m-1])+1)
            
            lista_remap.append([max_frecuencia['VALUE'][m], max_frec[m]])
            m = m + 1
        
        ### --- CAMBIOS DE 6 POR 20 ---###
        raster_consolidado_1 = Reclassify(raster_consolidado, "Value", RemapValue([[6,20]]))
        ####

        umbral_inf_raster = Reclassify (raster_consolidado_1, "Value", RemapValue(lista_remap))
        
        umbral_inf_raster.save (output_temporary + 'umbral_inf_raster_%s.tif' %(aspecto))

        ##raster para calculo de la reclasificacion

        max_por_freq_raster = arcpy.sa.RasterCalculator([raster_consolidado_1, frequency],
                                            ["x", "y"], "x * y")
        max_por_freq_raster.save (output_temporary + 'max_por_freq_raster_%s.tif' %(aspecto))

        #calculamos frecuencia por maximos
        FrecporMaximos = arcpy.sa.RasterCalculator([umbral_inf_raster, max_por_freq_raster],
                                            ["x", "y"], "x + y")

        FrecporMaximos.save (output_temporary + nom_proyecto + '_MaxFrec_%s' %(aspecto) + '.tif')

        #Reclasificamos los valores que corresponden a las restricciones (con el valor maximo que se calcule en FrecporMaximos)
        
        max_umbral = arcpy.management.GetRasterProperties(umbral_inf_raster, "MAXIMUM") #Corresponde al valor del umbral de las restricciones
        max_umbral_num = max_umbral.getOutput(0)

        max_value = arcpy.management.GetRasterProperties(FrecporMaximos, "MAXIMUM") #Corresponde al maximo valor encontrado por FrecporMaximos
        max_value_num = max_value.getOutput(0)

        FrecMax = arcpy.sa.Reclassify(FrecporMaximos, "Value", max_umbral_num + ' ' + max_value_num + ' ' + max_value_num, "DATA")
        FrecMax.save(folder + nom_proyecto + '_MaxFrec_%s' %(aspecto) + '.tif')

        print ("Maximo por Frecuencias Calculado")

###----------------EJECUCION DEL PROGRAMA (MAX POR FRECUENCIAS)-------------------------------

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

folder = ruta + nom_proyecto + '/' + nom_proyecto + '_' + version_proyecto + '/SALIDA/CONSOLIDADA/'

extent = output_temporary + 'extent.shp'

###-----------------MAXFREC PARA EL ASPECTO TECNICO---------------------------

#BUSCAMOS LOS RASTERS DE LAS VARIABLES DEL ASPECTO TECNICO
lista_vbles_te = []
p = Path(salida_vbles)
for name in p.glob('*vate*'):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles_te.append(r'%s' %(a))

if 'Tecnica' in superficies_selecc:
    FrecPorMaximos (folder, 'te', lista_vbles_te)

###-----------------MAXFREC PARA EL ASPECTO PREDIAL---------------------------

#BUSCAMOS LOS RASTERS DE LAS VARIABLES DEL ASPECTO PREDIAL
lista_vbles_pr = []
p = Path(salida_vbles)
for name in p.glob('*vapr*'):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles_pr.append(r'%s' %(a))

if 'Predial' in superficies_selecc:
    FrecPorMaximos (folder, 'pr', lista_vbles_pr)

###-----------------MAXFREC PARA EL ASPECTO AMBIENTAL---------------------------

#BUSCAMOS LOS RASTERS DE LAS VARIABLES DEL ASPECTO AMBIENTAL
lista_vbles_am = []
p = Path(salida_vbles)
for name in p.glob('*vaam*'):
    if str(name).endswith('.tif'):
        a=name
        lista_vbles_am.append(r'%s' %(a))

if 'Ambiental' in superficies_selecc:
    FrecPorMaximos (folder, 'am', lista_vbles_am)

###-----------------MAXFREC PARA CONSOLIDADA (TODOS LOS ASPECTOS)---------------------------

#BUSCAMOS LOS RASTERS DE TODAS LAS VARIABLES

lista_vbles_cons = lista_vbles_te + lista_vbles_pr + lista_vbles_am

if 'Consolidada' in superficies_selecc:
    FrecPorMaximos (folder, 'cons', lista_vbles_cons)

end = timer()
print(end - start,'segundos') # Time in seconds
print ("SUPERFICIES MaxFrec CALCULADAS")
