import glob
import gdal
import numpy as np
import pandas as pd
import time, os
from pathlib import Path
from configparser import ConfigParser
from timeit import default_timer as timer

folder_vbles = r'T:\PERU\PE_RECA\PE_RECA_v2_20211102\SALIDA\VARIABLE_V' + '/'
folder_temp = r'T:\PERU\PE_RECA\PE_RECA_v2_20211102\SALIDA\TEMPORAL' + '/'
folder_vbles_corr = r'T:\PERU\PE_RECA\PE_RECA_v2_20211102\SALIDA\TEMPORAL\CORREGIDAS' + '/'
folder_vbles_sel = r'T:\PERU\PE_RECA\PE_RECA_v2_20211102\SALIDA\TEMPORAL\SELECCIONADAS' + '/'
folder_resultado = r'T:\PERU\PE_RECA\PE_RECA_v2_20211102\SALIDA\INDICADORES\INDICADORES_POLIGONOS' + '/'

start = timer()

#---SE LEE LA RUTA A ANALIZAR---#

ruta_arpex = r'T:\PERU\PE_RECA\PE_RECA_v2_20211102\SALIDA\INDICADORES\RUTAS_INDICADORES\PE_RECA_MaxFrec_cons_RutaSM.shp'

# folder_ruta = r'K:\INDICADORES_CODIGO\INDICADOR_INTERSECCION_POLIGONOS\RUTA' + '/'

# lista_rutas = []
# p = Path(folder_ruta)

# for name in p.glob('*.shp'):
#     a=name
#     lista_rutas.append(r'%s' %(a))

#----SE SELECCIONAN LOS POLIGONOS QUE SE CRUZAN CON LA RUTA----#

lista_vbles = []
p = Path(folder_vbles)

for name in p.glob('*.shp'):
    a=name
    lista_vbles.append(r'%s' %(a))

for variable in lista_vbles:
    layer_vble = QgsVectorLayer(variable)
    layer_vble = QgsProject.instance().addMapLayer(layer_vble, False)

    processing.run("native:selectbylocation", {'INPUT': variable,
                                                'PREDICATE':[0,6],
                                                'INTERSECT': ruta_arpex,
                                                'METHOD':0})
    
    processing.run("qgis:selectbyexpression", {'INPUT': variable,
                                                'EXPRESSION': 'scep >= 5',
                                                'METHOD':3})
    
    processing.run("native:saveselectedfeatures", {'INPUT': layer_vble,
                                                    'OUTPUT': folder_vbles_sel + (variable.split('\\')[-1]).split('.')[0] + '.shp'})

#----SE CORRIGEN LOS SHP GENERADOS A PARTIR DE LA SELECCION----#

lista_vbles = []
p = Path(folder_vbles_sel)

for name in p.glob('*.shp'):
    a=name
    lista_vbles.append(r'%s' %(a))

for variable in lista_vbles:
    processing.run("native:fixgeometries", {'INPUT': variable,
                                            'OUTPUT': folder_vbles_corr + (variable.split('\\')[-1]).split('.')[0] + '.shp'})

#----SE LEEN LAS VBLES A INTERSECTAR----#

lista_vbles_corr = []
p = Path(folder_vbles_corr)

for name in p.glob('*.shp'):
    a=name
    lista_vbles_corr.append(r'%s' %(a))

#---INTERSECCION DE LAS VBLES CON LA RUTA---#

for vble in lista_vbles_corr:
    processing.run("native:intersection", {'INPUT': ruta_arpex,
                                            'OVERLAY': vble,
                                            'INPUT_FIELDS':[],
                                            'OVERLAY_FIELDS':[],
                                            'OVERLAY_FIELDS_PREFIX':'',
                                            'OUTPUT': folder_temp + 'intersect' + '_' + (vble.split('\\')[-1]).split('.')[0] + '.shp'})

    #---CALCULO DE LA LONGITUD INTERSECTADA---#

    #Se procede a crear una nueva columna en el shape

    layer = QgsVectorLayer(folder_temp + 'intersect' + '_' + (vble.split('\\')[-1]).split('.')[0] + '.shp')

    caps = layer.dataProvider().capabilities()

    if caps & QgsVectorDataProvider.AddAttributes:
        layer.dataProvider().addAttributes([QgsField("long_int", QVariant.Double)])
        layer.updateFields()
        fields_name = [f.name() for f in layer.fields()]
        idx = fields_name.index('long_int')

    #Se procede a llenar la columna con los valores de la long_int para la vble

    features = layer.getFeatures()

    if caps & QgsVectorDataProvider.ChangeAttributeValues:
        for feature in features:
            long_int = {idx : feature.geometry().length()/1000} #longitud en Km.
            layer.dataProvider().changeAttributeValues({feature.id() : long_int})

    #---SELECCION DE LOS TRAMOS DONDE SU SCEP >= 5---#

    layer.selectByExpression('"scep" >= 5')
    selection = layer.selectedFeatures()

    if len(selection) != 0:
        columns = layer.fields().names() 
        df = pd.DataFrame(selection)
        df.columns = columns
        df.to_excel(folder_resultado + (vble.split('\\')[-1]).split('.')[0] + '.xlsx', index = False)
    else:
        pass

end = timer()
print(end - start,'segundos') # Time in seconds
print ("EXTRAIDAS Y EXPORTADAS")


