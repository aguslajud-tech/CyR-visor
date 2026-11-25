#!/bin/bash
# Doble clic para regenerar todo desde los CSV de Insumos/.
cd "$(dirname "$0")"
Q=/Applications/QGIS.app/Contents
export QGIS_PREFIX_PATH=$Q/MacOS
export PYTHONPATH=$Q/Resources/python:$Q/Resources/python3.11/site-packages
export PROJ_LIB=$Q/Resources/qgis/proj
export QT_QPA_PLATFORM=offscreen
PY=$Q/MacOS/python
if [ ! -x "$PY" ]; then echo "No encuentro QGIS en /Applications/QGIS.app"; read -p "Enter para cerrar"; exit 1; fi
echo "1/6 Preparando datos..."; $PY 1_preparar_datos.py 2>&1 | grep -v "Warn\|Deprec" || exit 1
echo "2/6 Dibujando todos los mapas (tarda varios minutos)..."; $PY 2_dibujar_mapas.py 2>&1 | grep -v "Warn\|Deprec\|ERROR 6\|it.set"
echo "3/6 Cifras del visor..."; $PY datos_visor.py
echo "4/6 Mapa interactivo del visor..."; $PY datos_mapa.py 2>&1 | grep -v Warn
echo "5/6 Visor en un solo archivo..."; $PY 4_visor_unico.py 2>&1 | grep -v Warn
echo "6/6 PDF con todos los mapas..."; $PY 5_pdf_mapas.py 2>&1 | grep -v Warn
echo; echo "Terminado. Los mapas están en la carpeta mapas/."
read -p "Apretá Enter para cerrar."
