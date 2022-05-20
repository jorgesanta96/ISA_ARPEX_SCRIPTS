import glob
import time, os
from os import path
import numpy as np
import pandas as pd
from functools import reduce
from pathlib import Path
from configparser import ConfigParser
from timeit import default_timer as timer

start = timer()

# Carpeta con los excel a sacar el resumen de los indicadores
folder_resultado = r'T:\PERU\PE_CEPI\PE_CEPI_v0_20211116\SALIDA\INDICADORES'

# # Leemos los archivos de indicadores individuales generados para cada alternativa

# lista_excel = []
# p = Path(folder_resultado)

# for name in p.glob('*xlsx*'):
#     a=name
#     lista_excel.append(r'%s' %(a))

# # Leemos la informacion de cada uno de los archivos de indicadores

# lista_vbles = []
# lista_vbles_total = []

# for archivo in lista_excel:
#     excel_ind = pd.read_excel(archivo, index_col=0)
#     lista_vbles = excel_ind['variable']
#     for vble in lista_vbles:
#         if vble not in lista_vbles_total:
#             lista_vbles_total.append(vble)
    
# necesito hacer un join donde se conserven todos  los registros y columnas de los dos dataframe

# df_0 = pd.read_excel('T:\\PERU\\PE_RECA\\PE_RECA_v2_20211102\\SALIDA\\INDICADORES\\PE_RECA_MaxFrec_cons_folder_resultadoM.xlsx', index_col=0)
# df_1 = pd.read_excel('T:\\PERU\\PE_RECA\\PE_RECA_v2_20211102\\SALIDA\\INDICADORES\\PE_RECA_MaxSimpleR20_am_folder_resultadoM.xlsx', index_col=0)
# df = pd.merge(df_0, df_1,  how='outer', left_on=['aspecto', 'dimension','variable'], right_on = ['aspecto', 'dimension','variable'])
# df.sort_values(by=['aspecto', 'dimension', 'variable'], na_position='first', inplace=True)
# df.reset_index(drop = True, inplace =True)
# df.index.rename('ID', inplace=True)
# df.to_excel('T:\\PERU\\PE_RECA\\PE_RECA_v2_20211102\\SALIDA\\INDICADORES\\excel_df.xlsx', index = True)

##############
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
print ("INDICADORES OBTENIDOS")