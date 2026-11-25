# Arma "Mapas CyR importados QGIS.pdf": solo los mapas, cada uno con su tabla (sin portada) (producción local contra importada),
# en un PDF que se puede mandar por WhatsApp o mail y se abre en cualquier celular.
# Usa Google Chrome (sin abrirlo) para convertir la pagina a PDF. Se corre con el Python de QGIS
# (para reducir las imagenes) despues de los pasos 1 a 3.
import os,json,base64,html,subprocess,sys
from qgis.core import *
from qgis.PyQt.QtGui import QImage
from qgis.PyQt.QtCore import Qt,QBuffer,QByteArray,QIODevice
QgsApplication.setPrefixPath('/Applications/QGIS.app/Contents/MacOS',True)
app=QgsApplication([],False); app.initQgis()
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
s=open(os.path.join(R,'datos_visor.js'),encoding='utf-8').read(); D=json.loads(s[s.index('{'):s.rindex('}')+1])
NOM={v:l for v,c,l in D['_lista']}   # misma lista que el visor
def pct(x,t): return ('%.1f'%(100.0*x/t)).replace('.',',')+' %' if t>0 else '–'
def num(x): return str(round(x*100)/100).replace('.',',').replace(',0','') if False else ('%g'%round(x,2)).replace('.',',')
def img(f):
    im=QImage(os.path.join(R,'mapas',f)).scaled(1600,1130,Qt.KeepAspectRatio,Qt.SmoothTransformation)
    ba=QByteArray(); b=QBuffer(ba); b.open(QIODevice.WriteOnly); im.save(b,'JPG',85)
    return 'data:image/jpeg;base64,'+base64.b64encode(bytes(ba)).decode()
def tabla_zonas(d):
    tn,tp=d['total']; h='<table><tr><th>Zona</th><th>Piezas</th><th>% piezas</th><th>Páginas</th><th>% páginas</th></tr>'
    for z,p,n in d['zonas']: h+='<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(html.escape(z+(' (no se dibuja)' if z.startswith('Tricontinental') else '')),n,pct(n,tn),num(p),pct(p,tp))
    return h+'<tr class="t"><td>Total del ejemplar</td><td>%d</td><td>100 %%</td><td>%s</td><td>100 %%</td></tr></table><p class="b">Base: todas las piezas del ejemplar. "Tricontinental/ Global" cuenta en el total pero no se dibuja.</p>'%(tn,num(tp))
def tabla_proc(d):
    tn,tp=d['total']; imp=d['importado']; loc=d['local']; nd=d['indeterminado']
    h='<table><tr><th>Origen</th><th>Piezas</th><th>% del total</th><th>% de lo importado</th><th>Páginas</th><th>% páginas</th></tr>'
    h+='<tr class="g"><td>PRODUCCIÓN LOCAL</td><td>%d</td><td>%s</td><td></td><td>%s</td><td>%s</td></tr>'%(loc[0],pct(loc[0],tn),num(loc[1]),pct(loc[1],tp))
    h+='<tr class="h"><td colspan="6">Insumos importados</td></tr>'
    for o,l,t,p,n in d['proc']: h+='<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(html.escape(l.replace(' (solo región)',' (región)')),n,pct(n,tn),pct(n,imp[0]),num(p),pct(p,tp))
    if nd[0]>0: h+='<tr class="i"><td>Origen indeterminado (no se dibuja)</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(nd[0],pct(nd[0],tn),pct(nd[0],imp[0]),num(nd[1]),pct(nd[1],tp))
    h+='<tr class="s"><td>Subtotal importado</td><td>%d</td><td>%s</td><td>100 %%</td><td>%s</td><td>%s</td></tr>'%(imp[0],pct(imp[0],tn),num(imp[1]),pct(imp[1],tp))
    return h+'<tr class="t"><td>Total del ejemplar</td><td>%d</td><td>100 %%</td><td></td><td>%s</td><td>100 %%</td></tr></table><p class="b">Es "importado" lo marcado como "Insumo Transnacional directo" en Procedencia de Autoría; el resto cuenta como producción local. Los de origen indeterminado entran en la tabla y el total, nunca en el mapa.</p>'%(tn,num(tp))
def tabla_origenzona(d):
    tn,tp=d['total']; imp=d['importado']; h='<table><tr><th>Zona de origen</th><th>Insumos importados</th><th>% de las piezas</th><th>Páginas</th><th>% páginas</th></tr>'
    for z,p,n in d['origenzona']: h+='<tr><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(html.escape(z),n,pct(n,tn),num(p),pct(p,tp))
    h+='<tr class="s"><td>Subtotal importado</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(imp[0],pct(imp[0],tn),num(imp[1]),pct(imp[1],tp))
    return h+'<tr class="t"><td>Total del ejemplar</td><td>%d</td><td>100 %%</td><td>%s</td><td>100 %%</td></tr></table><p class="b">Cada insumo importado se suma a la zona del país o de la región de donde viene. La producción local no entra. Los importados de origen indeterminado no se mapean pero están en el subtotal.</p>'%(tn,num(tp))
TIPOS=(('zonas','Zona de la que hablan los insumos','zonas',tabla_zonas),('proc','Procedencia de los insumos importados','procedencia',tabla_proc),('origenzona','Procedencia de los insumos importados, por zona','procedencia-por-zona',tabla_origenzona))
MEDIDAS=(('paginas','según páginas'),('insumos','según cantidad de insumos'))
pages=''
for k,nom in NOM.items():
    d=D[k]
    for tipo,titulo,pref,fn in TIPOS:
        for mm,mtxt in MEDIDAS:
            pages+='<section><h2>%s · %s · %s</h2><div class="r"><img src="%s"><div class="tb">%s</div></div></section>'%(nom,titulo,mtxt,img('%s_%s_%s.png'%(pref,mm,k)),fn(d))
css='''@page{size:A4 landscape;margin:8mm} body{font-family:-apple-system,Helvetica,Arial,sans-serif;color:#16324a;margin:0}
section{page-break-after:always} h2{font-size:13pt;margin:0 0 4mm} .r{display:flex;gap:5mm;align-items:flex-start} .r img{width:63%;border:1px solid #d3dbe2} .tb{width:37%}
table{border-collapse:collapse;width:100%;font-size:7.4pt} th,td{padding:1.3mm 1.6mm;border-bottom:.2mm solid #d3dbe2;text-align:right} th:first-child,td:first-child{text-align:left} th{color:#5a6b7a;font-size:6.6pt}
tr.t td{font-weight:700;border-top:.5mm solid #16324a} tr.s td{font-weight:600} tr.g td{background:#dff0e6;font-weight:700} tr.h td{background:#eef3f7;font-weight:700;text-align:left} tr.i td{color:#5a6b7a;font-style:italic} p.b{font-size:6.6pt;color:#5a6b7a;margin:2mm 0 0}'''
out_html=os.path.join(R,'Scripts (opcional)','_mapas_pdf.html')
open(out_html,'w',encoding='utf-8').write('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Mapas CyR</title><style>%s</style></head><body>%s</body></html>'%(css,pages))
pdf=os.path.join(R,'Mapas CyR importados QGIS.pdf')
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--no-pdf-header-footer','--print-to-pdf='+pdf,'file://'+out_html],capture_output=True,timeout=120)
os.remove(out_html); print('ok',round(os.path.getsize(pdf)/1e6,1),'MB')
