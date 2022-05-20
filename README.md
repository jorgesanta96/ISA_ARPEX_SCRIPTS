# ISA_ARPEX_SCRIPTS

Este repositorio contiene los codigos correspondientes a la automatización y optimización de los procesos geograficos que se requieren para el análisis de nuevos proyectos de expansión de líneas de transmisión de energía.

Dentro de este, se van a encontrar los codigos divididos en el tipo de SIG que se debe de ejecutar el script, ya sea QGIS o ArcGIS, y otros elementos como los codigos de los indicadores tecnicos que se calculan a las líneas obtenidas de los análisis. Adicionalmente, se encuentra el archivo de iniciación de los codigos, alojado en la carpeta BASE.

Todos los scripts que se alojan en este repositorio, se encuentran desarrollados en lenguaje Python, debido a que QGIS y ArcGIS trabajan en dicho lenguaje. Se encontraran codigos correspondientes a los procesos de obtención de variables técnicas, transformación de otro tipo de variables y los procesos de consolidación realizados con dichas variables, con el fin de encontrar una superficie que dictamine el curso del proyecto. Adicionalmente, con esta superficie o superficies se calculan las diferentes alternativas de rutas y corredores, con el fin de calcular posteriormente los indicadores técnicos de tales alternativas y determinar cual alternativa es la más probable de realizar.

Estos scripts de Python trabajan con archivos alojados localmente y en un orden especifico, y se deben ejecutar dentro de las consolas de Python de los SIG en cuestión. Para el caso de los scripts de QGIS, se utiliza la libreria llamada PyQGIS que permite el llamar a las funciones y herramientas de QGIS ya construidas. Para los scripts de ArcGIS se utiliza ArcPy.
