# Arma "Visor de mapas (archivo unico).html": UN SOLO archivo con todo adentro
# (cifras, mapa interactivo e imagenes reducidas), para mandarlo por mail o WhatsApp
# y que funcione en cualquier dispositivo. Corre despues de los pasos 1 a 3.
import os,re,base64,sys
from qgis.core import *
from qgis.PyQt.QtGui import QImage
from qgis.PyQt.QtCore import Qt,QBuffer,QByteArray,QIODevice
QgsApplication.setPrefixPath('/Applications/QGIS.app/Contents/MacOS',True)
app=QgsApplication([],False); app.initQgis()
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
h=open(os.path.join(R,'Visor de mapas.html'),encoding='utf-8').read()
def inline(src):
    t=open(os.path.join(R,src),encoding='utf-8').read()
    return '<script>\n'+t+'\n</script>'
h=h.replace('<script src="datos_visor.js"></script>',inline('datos_visor.js')).replace('<script src="datos_mapa.js"></script>',inline('datos_mapa.js'))
imgs={}
d=os.path.join(R,'mapas')
for f in sorted(os.listdir(d)):
    if not f.endswith('.png'): continue
    im=QImage(os.path.join(d,f)).scaled(1500,1060,Qt.KeepAspectRatio,Qt.SmoothTransformation)
    ba=QByteArray(); b=QBuffer(ba); b.open(QIODevice.WriteOnly); im.save(b,'JPG',82)
    imgs[f]='data:image/jpeg;base64,'+base64.b64encode(bytes(ba)).decode()
import json
h=h.replace('<script>\n(function(){','<script>window.IMGS='+json.dumps(imgs)+';</script>\n<script>\n(function(){',1)
out=os.path.join(R,'Visor de mapas (archivo unico).html')
open(out,'w',encoding='utf-8').write(h)
print('ok',round(os.path.getsize(out)/1e6,1),'MB',len(imgs),'imagenes')
