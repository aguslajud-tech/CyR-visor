# Genera datos_mapa.js: los países dibujados en proyección Robinson (para el mapa interactivo del visor).
# Necesita el Python de QGIS. Uso (en Terminal):
#   /Applications/QGIS.app/Contents/MacOS/python datos_mapa.py
import csv,json,os,sys
sys.path.append('/Applications/QGIS.app/Contents/Resources/python')
from qgis.core import *
QgsApplication.setPrefixPath('/Applications/QGIS.app/Contents/MacOS',True)
app=QgsApplication([],False); app.initQgis()
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); I=os.path.join(R,'Insumos')
ne=QgsVectorLayer(os.path.join(I,'paises_naturalearth.gpkg')+'|layername=paises_base','p','ogr')
zona={r['pais']:r['zona'] for r in csv.DictReader(open(os.path.join(I,'paises_zonas.csv'),encoding='utf-8'))}
crs=QgsCoordinateReferenceSystem('ESRI:54030'); ct=QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:4326'),crs,QgsProject.instance())
K=1e-4  # 1 unidad del dibujo = 10 km
def P(x,y): return '%.1f %.1f'%(x*K,-y*K)
def pt(lon,lat):
    p=ct.transform(QgsPointXY(lon,lat)); return [round(p.x()*K,1),round(-p.y()*K,1)]
paises=[]
for f in ne.getFeatures():
    n=f['NAME']
    if n=='Antarctica': continue
    g=QgsGeometry(f.geometry()); g.transform(ct)
    polys=g.asMultiPolygon() if g.isMultipart() else [g.asPolygon()]
    d=''
    for poly in polys:
        for ring in poly:
            d+='M'+'L'.join(P(p.x(),p.y()) for p in ring)+'Z'
    paises.append({'n':n,'z':zona.get(n,''),'d':d})
lugares={}
for r in csv.DictReader(open(os.path.join(I,'procedencia_para_qgis.csv'),encoding='utf-8')):
    lugares[r['lugar']]=pt(float(r['longitud']),float(r['latitud']))
lugares['Argentina (producción local)']=pt(-58.4325,-34.6107)  # Buenos Aires (Natural Earth)
etq={r['zona']:pt(float(r['longitud']),float(r['latitud'])) for r in csv.DictReader(open(os.path.join(I,'etiquetas_zonas.csv'),encoding='utf-8'))}
xmin,ymin,xmax,ymax=-12470245,-8254211,13226017,9590416
M={'viewBox':[round(xmin*K,1),round(-ymax*K,1),round((xmax-xmin)*K,1),round((ymax-ymin)*K,1)],'paises':paises,'lugares':lugares,'etiquetas':etq}
open(os.path.join(R,'datos_mapa.js'),'w',encoding='utf-8').write('// Generado desde Insumos/. No editar a mano.\nwindow.MAPA='+json.dumps(M,ensure_ascii=False,separators=(',',':'))+';\n')
print('ok',len(paises),'paises')
