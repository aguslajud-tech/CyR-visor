# =====================================================================
# PASO 1 de 4: PREPARAR LOS DATOS
# Lee los CSV de la carpeta Insumos/ (los que bajás del Sheets) y arma:
#   - mapas_datos.gpkg : los países fusionados por zona, con las páginas y
#     piezas de cada ejemplar, y los puntos de procedencia (equivale a los
#     pasos 5 a 7 del Tutorial parte 1: join + Dissolve + join).
#   - meta.json : los textos y totales que van en las notas de los mapas.
# Solo cuentan los ejemplares con completo = 1 en SIG ejemplares.
# No cambia ningún dato: solo suma lo que ya está en los CSV.
# =====================================================================
import csv,json,os
from qgis.core import *
from qgis.PyQt.QtCore import QVariant
QgsApplication.setPrefixPath('/Applications/QGIS.app/Contents/MacOS',True)
app=QgsApplication([],False); app.initQgis()
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'   # carpeta Mapas CyR
I=R+'Insumos/'
ne=QgsVectorLayer(I+'paises_naturalearth.gpkg|layername=paises_base','p','ogr')
pz={r['pais']:r['zona'] for r in csv.DictReader(open(I+'paises_zonas.csv',encoding='utf-8'))}
Z=list(csv.DictReader(open(I+'resumen_zonas.csv',encoding='utf-8')))
P=list(csv.DictReader(open(I+'procedencia_para_qgis.csv',encoding='utf-8')))
E=list(csv.DictReader(open(I+'resumen_ejemplares.csv',encoding='utf-8')))
PZR=list(csv.DictReader(open(I+'resumen_procedencia_zonas.csv',encoding='utf-8')))   # procedencia sumada por zona (pestaña SIG procedencia-zona)
done=[e for e in E if e['id_ejemplar']!='acum' and e['completo']=='1']
KEY={e['ejemplar']:'e%02d'%i for i,e in enumerate(done,1)}  # '1/1966' -> e01
SRC={e['ejemplar']:e['id_ejemplar'] for e in done}              # '1/1966' -> e1
ORDER=[e['ejemplar'] for e in done]; MES={e['ejemplar']:e['mes_año'] for e in done}
KS=['acum']+list(KEY.values())
print(ORDER,KEY)
acum=[e for e in E if e['id_ejemplar']=='acum'][0]
TOT_PAG={KEY[e['ejemplar']]:float(e['paginas_total']) for e in done}; TOT_PAG['acum']=float(acum['paginas_total'])
TOT_N={KEY[e['ejemplar']]:float(e['articulos_total']) for e in done}; TOT_N['acum']=float(acum['articulos_total'])
LOC_PAG={KEY[e['ejemplar']]:float(e['paginas_locales']) for e in done}; LOC_PAG['acum']=float(acum['paginas_locales'])
LOC_N={KEY[e['ejemplar']]:float(e['articulos_locales']) for e in done}; LOC_N['acum']=float(acum['articulos_locales'])
geoms={}
for f in ne.getFeatures():
    z=pz.get(f['NAME'],'')
    if z: geoms.setdefault(z,[]).append(f.geometry())
ZONAS=[z['zona'] for z in Z if z['zona']!='Tricontinental/ Global']
# Zona de cada lugar de origen: viene de la columna zona_origen de SIG procedencia; las sumas por zona, de la pestaña SIG procedencia-zona.
if 'zona_origen' not in P[0]:
    raise SystemExit('Falta la columna zona_origen en procedencia_para_qgis.csv (se agrega en la pestaña SIG procedencia del Sheets; ver Tutorial parte 0).')
ZONA_ORIGEN={row['origen']:row['zona_origen'] for row in P}
PZ={r['zona']:r for r in PZR}
print('zona de origen:',ZONA_ORIGEN)
gp=R+'mapas_datos.gpkg'
if os.path.exists(gp): os.remove(gp)
def save(layer,name,first):
    o=QgsVectorFileWriter.SaveVectorOptions(); o.driverName='GPKG'; o.layerName=name
    o.actionOnExistingFile=QgsVectorFileWriter.CreateOrOverwriteFile if first else QgsVectorFileWriter.CreateOrOverwriteLayer
    print(name,QgsVectorFileWriter.writeAsVectorFormatV3(layer,gp,QgsProject.instance().transformContext(),o)[0])
save(ne,'paises_base',True)
def val(row,pre,ej):
    p,a={'pag_':('paginas_','acumuladas'),'n_':('articulos_','acumulados')}[pre]   # nombres de columna de los CSV
    c=p+(a if ej=='acum' else SRC[ej]); return float(row[c] or 0)
zl=QgsVectorLayer('MultiPolygon?crs=EPSG:4326','zonas','memory'); pr=zl.dataProvider()
pr.addAttributes([QgsField('zona',QVariant.String)]+[QgsField('pag_'+k,QVariant.Double) for k in KS]+[QgsField('n_'+k,QVariant.Int) for k in KS]
  +[QgsField(pre+k,QVariant.Double) for pre in ('opag_','on_','olpag_','oln_') for k in KS]); zl.updateFields()
fs=[]
for row in Z:
    z=row['zona']
    if z not in geoms: continue
    f=QgsFeature(zl.fields()); f.setGeometry(QgsGeometry.unaryUnion(geoms[z])); f['zona']=z
    for k in KS:
        ej='acum' if k=='acum' else [e for e,kk in KEY.items() if kk==k][0]
        f['pag_'+k]=round(val(row,'pag_',ej),2); f['n_'+k]=int(val(row,'n_',ej))
        # procedencia por zona: lo importado cuyo origen cae en esta zona (o, en la variante 'l', sumando la producción local a Argentina)
        op=val(PZ[z],'pag_',ej) if z in PZ else 0; on=val(PZ[z],'n_',ej) if z in PZ else 0
        lp_,ln_=(LOC_PAG[k],LOC_N[k]) if z=='Argentina' else (0,0)
        f['opag_'+k]=round(op,2); f['on_'+k]=round(on,2); f['olpag_'+k]=round(op+lp_,2); f['oln_'+k]=round(on+ln_,2)
    fs.append(f)
pr.addFeatures(fs); save(zl,'zonas_geopoliticas',False)
pl=QgsVectorLayer('Point?crs=EPSG:4326','pr','memory'); pp=pl.dataProvider()
pp.addAttributes([QgsField('origen',QVariant.String),QgsField('lugar',QVariant.String),QgsField('tipo',QVariant.String)]+[QgsField('pag_'+k,QVariant.Double) for k in KS]+[QgsField('n_'+k,QVariant.Int) for k in KS]); pl.updateFields()
fs=[]
for row in P:
    if row['tipo']!='país': continue   # los orígenes que solo dicen la región no llevan punto
    f=QgsFeature(pl.fields()); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(row['longitud']),float(row['latitud']))))
    f['origen']=row['origen']; f['lugar']=row['lugar']; f['tipo']=row['tipo']
    for k in KS:
        ej='acum' if k=='acum' else [e for e,kk in KEY.items() if kk==k][0]
        f['pag_'+k]=round(val(row,'pag_',ej),2); f['n_'+k]=int(val(row,'n_',ej))
    fs.append(f)
pp.addFeatures(fs); save(pl,'procedencia_puntos',False)
el=QgsVectorLayer('Point?crs=EPSG:4326&field=zona:string','e','memory')
fs=[]
for r in csv.DictReader(open(I+'etiquetas_zonas.csv',encoding='utf-8')):
    f=QgsFeature(el.fields()); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(r['longitud']),float(r['latitud'])))); f['zona']=r['zona']; fs.append(f)
el.dataProvider().addFeatures(fs); save(el,'etiquetas_zonas',False)
sin_zona={KEY[e['ejemplar']]:float(e['paginas_sin_zona']) for e in done}; sin_zona['acum']=float(acum['paginas_sin_zona'])
noesp={KEY[e['ejemplar']]:int(float(e['articulos_sin_origen'])) for e in done}; noesp['acum']=int(float(acum['articulos_sin_origen']))
noesp_pag={KEY[e['ejemplar']]:float(e['paginas_sin_origen']) for e in done}; noesp_pag['acum']=float(acum['paginas_sin_origen'])
def pct(n,t): return ('%.1f'%(100.0*n/t)).replace('.',',')+' %' if t else ''
pct_local={KEY[e['ejemplar']]:pct(float(e['articulos_locales']),float(e['articulos_total'])) for e in done}; pct_local['acum']=pct(float(acum['articulos_locales']),float(acum['articulos_total']))   # % de piezas locales
pct_local_pag={k:pct(LOC_PAG[k],TOT_PAG[k]) for k in KS}; pct_local_n={k:pct(LOC_N[k],TOT_N[k]) for k in KS}
TRI=[r for r in Z if r['zona']=='Tricontinental/ Global'][0]
tricont_n={k:int(val(TRI,'n_','acum' if k=='acum' else [e for e,kk in KEY.items() if kk==k][0])) for k in KS}
json.dump(dict(zona_origen=ZONA_ORIGEN,tricont_n=tricont_n,tot_pag=TOT_PAG,tot_n=TOT_N,pct_local_pag=pct_local_pag,pct_local_n=pct_local_n,sin_zona=sin_zona,noesp=noesp,noesp_pag=noesp_pag,pct_local=pct_local,KS=KS,KEY=KEY,ORDER=ORDER,MES=MES),open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'meta.json'),'w'),ensure_ascii=False)
print(sin_zona,noesp)
