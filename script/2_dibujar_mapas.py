# =====================================================================
# PASO 2 de 6: DIBUJAR LOS MAPAS (3 tipos x 2 medidas por ejemplar y por la totalidad de la tirada)
# Usa mapas_datos.gpkg y meta.json (paso 1) y exporta a la carpeta mapas/
# los PNG de los tres tipos de mapa (zonas, procedencia, procedencia por zona) en las dos
# medidas (páginas, insumos), por ejemplar y para la totalidad de la tirada; y mapas_CyR.qgz.
# Equivale a los pasos 8 a 15 de los tutoriales (colores, cortes, puntos,
# etiquetas, lámina y exportación), con las MISMAS decisiones:
#   - cortes de color en % del total del ejemplar: 2, 5, 10, 20, 35 (los mismos en todos los mapas)
#   - paleta granate (zonas) y ciruela (procedencia por zona)
#   - tamaño de los puntos: 2,2 + 3,4 x raíz del porcentaje sobre el total del ejemplar (mm)
#   - Cuba en rojo, otros países en azul, producción local (Argentina) en verde claro; sin rombos
#   - mar #c5d7e3, tierra #f6f4ef, banda de título #16324a
# Para cambiar una decisión se edita la línea marcada (buscá el color o el
# número en este archivo).
# =====================================================================
import json,os,math,sys,collections
from qgis.core import *
from qgis.PyQt.QtCore import Qt,QSizeF
from qgis.PyQt.QtGui import QColor, QFont
QgsApplication.setPrefixPath('/Applications/QGIS.app/Contents/MacOS',True)
app=QgsApplication([],False); app.initQgis()
QD=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(QD,'..')+'/'   # carpeta Mapas CyR
meta=json.load(open(os.path.join(QD,'meta.json'))); KS=meta['KS']; KEY=meta['KEY']; ORDER=meta['ORDER']; MES=meta['MES']
NUMEROS=sum(2 if '-' in e.split('/')[0] else 1 for e in ORDER)   # un ejemplar doble (2-3) cuenta como 2 números
ANIOS=sorted(int(e.split('/')[1]) for e in ORDER); PERIODO=('%d-%d'%(ANIOS[0],ANIOS[-1])) if ANIOS[0]!=ANIOS[-1] else str(ANIOS[0])
sin_zona=meta['sin_zona']; noesp=meta['noesp']; noesp_pag=meta['noesp_pag']; pct_local=meta['pct_local']
TOT={'pag':meta['tot_pag'],'n':meta['tot_n']}; PCTLOC={'pag':meta['pct_local_pag'],'n':meta['pct_local_n']}
gp=OUT+'mapas_datos.gpkg'
prj=QgsProject.instance(); prj.clear(); prj.setCrs(QgsCoordinateReferenceSystem('ESRI:54030'))
base=QgsVectorLayer(gp+'|layername=paises_base','Países (base)','ogr'); base.setSubsetString("\"name\" <> 'Antarctica'")
zon=QgsVectorLayer(gp+'|layername=zonas_geopoliticas','Zonas geopolíticas','ogr')
pun=QgsVectorLayer(gp+'|layername=procedencia_puntos','Procedencia','ogr')
ez=QgsVectorLayer(gp+'|layername=etiquetas_zonas','Etiquetas de zonas','ogr')
arg=QgsVectorLayer(gp+'|layername=paises_base','Argentina (producción local)','ogr'); arg.setSubsetString("\"name\" = 'Argentina'")   # solo Argentina, en verde
zon2=QgsVectorLayer(gp+'|layername=zonas_geopoliticas','Procedencia por zona','ogr')   # las mismas zonas, pintadas según de dónde vienen los insumos importados
ez2=QgsVectorLayer(gp+'|layername=etiquetas_zonas','Etiquetas de procedencia por zona','ogr')
for l in (ez,ez2,base,zon,zon2,pun,arg): assert l.isValid(),l.name()
prj.addMapLayers([ez,ez2,pun,arg,zon,zon2,base])
def setvar(n,v): QgsExpressionContextUtils.setProjectVariable(prj,n,v)
PALETAS={'verde':['#e3f1ee','#b9ded5','#86c7b9','#4aa395','#1f7a72','#094d50'],'violeta':['#f0e9f5','#d7c4e6','#b998d3','#9267b8','#693a96','#3d1a62'],'azul':['#e6edf5','#bfd0e5','#8dafd2','#5984b6','#2e5c98','#102f63'],'granate':['#fde8e4','#f8c4ba','#ee8f80','#d6584c','#a52a30','#5c0f1a'],'ciruela':['#f3e5f1','#e3b6d8','#cd7fbc','#b04a9a','#802472','#4a0f46'],'rosa':['#fde3ea','#f9bcce','#f08aa9','#dc4f7f','#a8245a','#5e0f36'],'naranja':['#fdf1dc','#fbd9a0','#f4b26a','#e5823f','#c9532a','#8f2d1b']}
PAL=os.environ.get('PALETA','granate'); SEQ=PALETAS[PAL]   # mapa de zonas: granate (elegido el 27/10/2026)
SEQ2=PALETAS[os.environ.get('PALETA2','ciruela')]   # mapa de procedencia por zona: ciruela (elegido el 27/10/2026)
VERDE_LOCAL='#a9d0b8'   # verde de la producción local (Argentina): más claro y suave
TERR='#f6f4ef'; MAR='#c5d7e3'; BORDE='#aea99c'; SINDATO='#efedea'
# --- base
bs=QgsFillSymbol.createSimple({'color':TERR,'outline_color':BORDE,'outline_width':'0.14'}); base.setRenderer(QgsSingleSymbolRenderer(bs))
# --- zonas (color por tramos, con variables)
expr=("CASE WHEN 100.0*coalesce(attribute($currentfeature,@campo_zona),0)/@tot_zona<=0 THEN @p0 "
      "WHEN 100.0*attribute($currentfeature,@campo_zona)/@tot_zona<=@n1 THEN @p1 WHEN 100.0*attribute($currentfeature,@campo_zona)/@tot_zona<=@n2 THEN @p2 "
      "WHEN 100.0*attribute($currentfeature,@campo_zona)/@tot_zona<=@n3 THEN @p3 WHEN 100.0*attribute($currentfeature,@campo_zona)/@tot_zona<=@n4 THEN @p4 "
      "WHEN 100.0*attribute($currentfeature,@campo_zona)/@tot_zona<=@n5 THEN @p5 ELSE @p6 END")
zs=QgsFillSymbol.createSimple({'color':'#cccccc','outline_color':'#ffffff','outline_width':'0.25'})
zs.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor,QgsProperty.fromExpression(expr))
zon.setRenderer(QgsSingleSymbolRenderer(zs)); zon.setLabelsEnabled(False)
expr2=("CASE WHEN 100.0*coalesce(attribute($currentfeature,@campo_origen),0)/@tot_origen<=0 THEN @q0 "
      "WHEN 100.0*attribute($currentfeature,@campo_origen)/@tot_origen<=@m1 THEN @q1 WHEN 100.0*attribute($currentfeature,@campo_origen)/@tot_origen<=@m2 THEN @q2 "
      "WHEN 100.0*attribute($currentfeature,@campo_origen)/@tot_origen<=@m3 THEN @q3 WHEN 100.0*attribute($currentfeature,@campo_origen)/@tot_origen<=@m4 THEN @q4 "
      "WHEN 100.0*attribute($currentfeature,@campo_origen)/@tot_origen<=@m5 THEN @q5 ELSE @q6 END")
zs2=QgsFillSymbol.createSimple({'color':'#cccccc','outline_color':'#ffffff','outline_width':'0.25'})
zs2.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor,QgsProperty.fromExpression(expr2))
def simbolo_rayado(borde='#ffffff',ancho_borde='0.25'):
    """Blanco con rayitas a 45 grados: Argentina en el mapa de procedencia por zona (nunca se mapea ahí)."""
    s=QgsFillSymbol.createSimple({'color':'#ffffff','outline_color':borde,'outline_width':ancho_borde})
    rl=QgsLinePatternFillSymbolLayer(); rl.setLineAngle(45); rl.setDistance(1.6); rl.setColor(QColor('#8c8c8c')); rl.setLineWidth(0.18)
    s.appendSymbolLayer(rl); return s
raiz2=QgsRuleBasedRenderer.Rule(None)
ra=QgsRuleBasedRenderer.Rule(zs2); ra.setLabel('Zonas'); ra.setFilterExpression("\"zona\"<>'Argentina'")
rb=QgsRuleBasedRenderer.Rule(simbolo_rayado()); rb.setLabel('Argentina (no se mapea)'); rb.setFilterExpression("\"zona\"='Argentina'")
raiz2.appendChild(ra); raiz2.appendChild(rb)
zon2.setRenderer(QgsRuleBasedRenderer(raiz2)); zon2.setLabelsEnabled(False)
# --- etiquetas de zona (capa de anclas)
def txt(size,color,bold=False,buf=0.7):
    tf=QgsTextFormat(); f=QFont('Helvetica Neue',int(round(size))); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(color))
    b=QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buf); b.setColor(QColor(255,255,255,235)); tf.setBuffer(b); return tf
def cajita(size=8):
    """Etiqueta de zona: cajita blanca con esquinas redondeadas, borde fino y sombra suave (diseño A1, elegido el 27/10/2026)."""
    tf=QgsTextFormat(); f=QFont('Helvetica Neue',int(round(size))); f.setBold(True); tf.setFont(f); tf.setSize(size); tf.setColor(QColor('#22303c'))
    bg=QgsTextBackgroundSettings(); bg.setEnabled(True); bg.setType(QgsTextBackgroundSettings.ShapeRectangle); bg.setSizeType(QgsTextBackgroundSettings.SizeBuffer)
    bg.setSize(QSizeF(1.8,1.0)); bg.setSizeUnit(QgsUnitTypes.RenderMillimeters); bg.setRadii(QSizeF(1.6,1.6)); bg.setRadiiUnit(QgsUnitTypes.RenderMillimeters)
    bg.setFillColor(QColor(255,255,255,255)); bg.setStrokeColor(QColor('#c3ccd4')); bg.setStrokeWidth(0.15); bg.setStrokeWidthUnit(QgsUnitTypes.RenderMillimeters)
    sh=tf.shadow(); sh.setEnabled(True); sh.setShadowPlacement(QgsTextShadowSettings.ShadowShape); sh.setOffsetDistance(0.5); sh.setOffsetAngle(135); sh.setBlurRadius(0.9); sh.setOpacity(0.35); sh.setColor(QColor('#000000')); tf.setShadow(sh)
    tf.setBackground(bg); return tf
lz=QgsPalLayerSettings(); lz.fieldName="CASE WHEN coalesce(attribute(get_feature('Zonas geopolíticas','zona',\"zona\"),@campo_zona),0)>0 THEN replace(\"zona\",'EEUU/ Europa','EEUU y Europa') || '\n' || format_number(100.0*attribute(get_feature('Zonas geopolíticas','zona',\"zona\"),@campo_zona)/@tot_zona,1) || ' %' END"
lz.isExpression=True; lz.setFormat(cajita()); lz.placement=Qgis.LabelPlacement.OverPoint
lz.priority=10
ez.setLabeling(QgsVectorLayerSimpleLabeling(lz)); ez.setLabelsEnabled(True)
ez.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({'size':'0','color':'0,0,0,0','outline_style':'no'})))
lz2=QgsPalLayerSettings(); lz2.fieldName="CASE WHEN coalesce(attribute(get_feature('Procedencia por zona','zona',\"zona\"),@campo_origen),0)>0 THEN replace(\"zona\",'EEUU/ Europa','EEUU y Europa') || '\n' || format_number(100.0*attribute(get_feature('Procedencia por zona','zona',\"zona\"),@campo_origen)/@tot_origen,1) || ' %' END"
lz2.isExpression=True; lz2.setFormat(cajita()); lz2.placement=Qgis.LabelPlacement.OverPoint; lz2.priority=10
ez2.setLabeling(QgsVectorLayerSimpleLabeling(lz2)); ez2.setLabelsEnabled(True)
ez2.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({'size':'0','color':'0,0,0,0','outline_style':'no'})))
# --- puntos
AZ='#1d5f8a'; CU='#b3261e'
size_expr="2.2+3.4*sqrt(100.0*attribute($currentfeature,@campo_punto)/@tot_punto)"   # diámetro (mm) según el % del total del ejemplar
def ms(shape,fill,line,w='0.45'):
    s=QgsMarkerSymbol.createSimple({'name':shape,'color':fill,'outline_color':line,'outline_width':w,'size':'4'})
    s.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertySize,QgsProperty.fromExpression(size_expr)); return s
root=QgsRuleBasedRenderer.Rule(None)
def rule(lbl,flt,sym):
    r=QgsRuleBasedRenderer.Rule(sym); r.setLabel(lbl); r.setFilterExpression(flt); return r
gt="coalesce(attribute($currentfeature,@campo_punto),0)>0"
root.appendChild(rule('Cuba',"\"origen\"='Cuba' AND "+gt,ms('circle','179,38,30,175','255,255,255,255')))
root.appendChild(rule('Otros países',"\"tipo\"='país' AND \"origen\"<>'Cuba' AND "+gt,ms('circle','29,95,138,165','255,255,255,255')))
pun.setRenderer(QgsRuleBasedRenderer(root))
lp=QgsPalLayerSettings(); lp.fieldName="CASE WHEN coalesce(attribute($currentfeature,@campo_punto),0)>=@min_etq THEN \"lugar\" END"
lp.isExpression=True; lp.setFormat(txt(7.5,'#12314a',False,0.8)); lp.placement=Qgis.LabelPlacement.AroundPoint; lp.dist=1.0; lp.distUnits=QgsUnitTypes.RenderMillimeters
lp.priority=6; lp.obstacle=False
pun.setLabeling(QgsVectorLayerSimpleLabeling(lp)); pun.setLabelsEnabled(True)
# Argentina = producción local: relleno verde y etiqueta con su porcentaje
arg.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({'color':VERDE_LOCAL,'outline_color':'#ffffff','outline_width':'0.25'})))
la=QgsPalLayerSettings(); la.fieldName="'Argentina' || '\n' || @pct_local || ' local'"; la.isExpression=True; la.setFormat(txt(8,'#14452b',True)); la.placement=Qgis.LabelPlacement.Horizontal; la.priority=8
arg.setLabeling(QgsVectorLayerSimpleLabeling(la)); arg.setLabelsEnabled(True)
# --- lámina
def mklayout(name,kind):
    lm=prj.layoutManager()
    for l in lm.layouts():
        if l.name()==name: lm.removeLayout(l)
    lay=QgsPrintLayout(prj); lay.initializeDefaults(); lay.setName(name)
    pg=lay.pageCollection().page(0); pg.setPageSize('A4',QgsLayoutItemPage.Landscape)
    pg.setPageSize('A4',QgsLayoutItemPage.Landscape)
    def label(t,x,y,w,h,size=9,bold=False,color='#2a2a2a',align=Qt.AlignLeft,valign=Qt.AlignTop,italic=False):
        it=QgsLayoutItemLabel(lay); it.setText(t); f=QFont('Helvetica Neue',int(round(size))); f.setBold(bold); f.setItalic(italic)
        it.setFont(f); it.setFontColor(QColor(color)); it.attemptMove(QgsLayoutPoint(x,y,QgsUnitTypes.LayoutMillimeters)); it.attemptResize(QgsLayoutSize(w,h,QgsUnitTypes.LayoutMillimeters))
        it.setHAlign(align); it.setVAlign(valign); it.setMarginX(0); it.setMarginY(0); lay.addLayoutItem(it); return it
    def rect(x,y,w,h,fill,line='#999999',lw='0.15',shape=QgsLayoutItemShape.Rectangle):
        r=QgsLayoutItemShape(lay); r.setShapeType(shape); r.attemptMove(QgsLayoutPoint(x,y,QgsUnitTypes.LayoutMillimeters)); r.attemptResize(QgsLayoutSize(w,h,QgsUnitTypes.LayoutMillimeters))
        r.setSymbol(QgsFillSymbol.createSimple({'color':fill,'outline_color':line,'outline_width':lw})); lay.addLayoutItem(r); return r
    # franja de título
    rect(0,0,297,21,'#16324a','#16324a','0')
    label('[% @titulo_'+kind+' %]',10,5,277,9,17,True,'#ffffff')
    label('[% @subtitulo_'+kind+' %]',10,13.2,277,6,9.5,False,'#cfe0ee')
    m=QgsLayoutItemMap(lay); m.attemptMove(QgsLayoutPoint(10,26,QgsUnitTypes.LayoutMillimeters)); m.attemptResize(QgsLayoutSize(216,150,QgsUnitTypes.LayoutMillimeters))
    ct=QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:4326'),prj.crs(),prj)
    ext=ct.transformBoundingBox(QgsRectangle(-132,-56,140,70))
    capas={'zonas':[ez,zon,base],'origenzona':[ez2,zon2,base],'procedencia':[pun,arg,base]}[kind]
    m.setCrs(prj.crs()); m.setLayers(capas); m.zoomToExtent(ext)
    m.setFrameEnabled(True); m.setFrameStrokeColor(QColor('#9fb3c2')); m.setFrameStrokeWidth(QgsLayoutMeasurement(0.3)); m.setBackgroundColor(QColor(MAR)); lay.addLayoutItem(m)
    x0=232; w=55
    if kind in ('zonas','origenzona'):
        pre='' if kind=='zonas' else 'o'
        label('[% @leyenda_titulo_'+kind+' %]',x0,27,w,6,10.5,True,'#16324a')
        label('[% @leyenda_sub_'+kind+' %]',x0,32.5,w,9,8.5,False,'#555555')
        labs=['[% @e0_'+kind+' %]']+['[% @e'+str(i)+'_'+kind+' %]' for i in range(1,7)]
        y=44
        for ci,t in enumerate(labs):
            r_=rect(x0,y,8,5.2,'#cccccc','#9a9a9a','0.15'); r_.symbol().symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor,QgsProperty.fromExpression('@%s%d'%('p' if kind=='zonas' else 'q',ci))); label(t,x0+11,y+0.5,w-11,5,8.5,False); y+=7.4
        if kind=='origenzona':   # Argentina rayada: la producción local nunca se mapea en este tipo de mapa
            r_=rect(x0,y,8,5.2,'#ffffff','#9a9a9a','0.15'); r_.setSymbol(simbolo_rayado('#9a9a9a','0.15')); label('Argentina: producción local (no se mapea)',x0+11,y+0.2,w-11,9,8.5,False); y+=11
        label('[% @pie_leyenda_'+kind+' %]',x0,y+3,w,40,7.5,False,'#666666',italic=True)
    else:
        label('Insumos importados',x0,27,w,6,10.5,True,'#16324a')
        label('[% @unidad_leyenda_punto %]',x0,32.5,w,12,8.5,False,'#555555')
        y=47
        for v,tt in ((1,'1 %'),(5,'5 %'),(10,'10 %')):
            d=2.2+3.4*math.sqrt(v)
            e=rect(x0+(12-d)/2,y,d,d,'29,95,138,165','#ffffff','0.3',QgsLayoutItemShape.Ellipse)
            label(tt,x0+16,y+d/2-2.2,30,5,8.5); y+=d+3
        y+=1
        e=rect(x0+1,y,9,9,'179,38,30,175','#ffffff','0.3',QgsLayoutItemShape.Ellipse); label('Cuba',x0+16,y+2.2,30,5,8.5); y+=13
        rect(x0,y+1,8,5.2,VERDE_LOCAL,'#ffffff','0.15'); label('Argentina: producción local ([% @pct_local %] del total)',x0+11,y+0.4,w-11,12,8,False); y+=15
        label('[% @ranking %]',x0,y,w,40,7.8,False,'#2a2a2a')
    label('[% @nota_'+kind+' %]',10,180,216,12,8.5,False,'#333333')
    label('Fuente: elaboración propia, lectura manual de los ejemplares de Cristianismo y Revolución (CeDInCI). Fronteras actuales (Natural Earth), no las de 1966-1971. Ejemplares relevados: %d (%d números).'%(len(ORDER),NUMEROS),10,196,277,9,7,False,'#7a7a7a')
    lm.addLayout(lay); return lay
LAY={'zonas':mklayout('Mapa de zonas geopolíticas','zonas'),'procedencia':mklayout('Mapa de procedencia','procedencia'),'origenzona':mklayout('Mapa de procedencia por zona','origenzona')}
def fmt(v): return ('%.1f'%v).rstrip('0').rstrip('.').replace('.',',') if v%1 else str(int(v))
def ranking(k,med):
    campo=med+'_'+k; L=[]; tot=TOT[med][k]
    for ft in pun.getFeatures():
        v=ft[campo]
        if v and v>0: L.append((v,ft['lugar']))
    L.sort(key=lambda t:-t[0]); top=L[:9]
    return 'Mayores orígenes (% de '+('las páginas' if med=='pag' else 'los insumos')+(' de la tirada)\n' if k=='acum' else ' del ejemplar)\n')+'\n'.join('%s · %s %%'%(n,('%.1f'%(100.0*v/tot)).replace('.',',')) for v,n in top)
def setpal():
    for i,c in enumerate([SINDATO]+SEQ): setvar('p%d'%i,c)
    for i,c in enumerate([SINDATO]+SEQ2): setvar('q%d'%i,c)
CORTES_PCT=[2,5,10,20,35]   # cortes (en % del total del ejemplar) del mapa de procedencia por zona
def clave(k): return 'tirada' if k=='acum' else None
def render(kind,k,med,variante='sin_local',destino=None):
    """kind: zonas | procedencia | origenzona. med: pag | n. variante (solo origenzona): sin_local | con_local."""
    setpal()
    acum=(k=='acum'); ej=None if acum else [e for e in ORDER if KEY[e]==k][0]
    nombre='los %d ejemplares relevados (%d números, %s)'%(len(ORDER),NUMEROS,PERIODO) if acum else 'ejemplar %s (%s)'%(ej.split('/')[0],MES[ej] or ej.split('/')[1])
    sufijo=' · totalidad de la tirada' if acum else ''
    medida_txt='cantidad de insumos' if med=='n' else 'páginas'
    if kind=='zonas':
        setvar('campo_zona',med+'_'+k); setvar('tot_zona',TOT[med][k])
        for i,b in enumerate(CORTES_PCT,1): setvar('c%d'%i,fmt(b)); setvar('n%d'%i,b)
        for i,b in enumerate(CORTES_PCT,1): QgsExpressionContextUtils.setProjectVariable(prj,'n%d'%i,b)
        setvar('titulo_zonas','Zona de la que hablan los insumos'+sufijo)
        setvar('subtitulo_zonas','Cristianismo y Revolución, '+nombre+'. Medida: '+medida_txt+'.')
        setvar('leyenda_titulo_zonas','% de las páginas' if med=='pag' else '% de los insumos'); setvar('leyenda_sub_zonas','dedicados a cada zona geopolítica (sobre el total '+('de la tirada' if acum else 'del ejemplar')+')')
        es=['sin insumos','hasta %d %%'%CORTES_PCT[0]]+['de %d a %d %%'%(CORTES_PCT[i-1],CORTES_PCT[i]) for i in range(1,5)]+['más de %d %%'%CORTES_PCT[4]]
        for i,e in enumerate(es): setvar('e%d_zonas'%i,e)
        setvar('pie_leyenda_zonas','Se cuentan '+('las páginas de cada pieza' if med=='pag' else 'los insumos (piezas)')+' según la zona de la que habla. "Tricontinental/ Global" no es un lugar y no se pinta.')
        tri=(sin_zona.get(k,0)/TOT['pag'][k]) if med=='pag' else (noesp_zona.get(k,0)/TOT['n'][k])
        triabs=(fmt(sin_zona.get(k,0))+' páginas') if med=='pag' else (fmt(noesp_zona.get(k,0))+' insumos')
        setvar('nota_zonas','"Tricontinental/ Global" es el %s %% de %s %s (%s); no es un lugar y no se puede mapear.'%(('%.1f'%(100*tri)).replace('.',','),'las páginas' if med=='pag' else 'los insumos',('de la tirada' if acum else 'del ejemplar'),triabs))
    elif kind=='procedencia':
        setvar('campo_punto',med+'_'+k); setvar('min_etq','1'); setvar('tot_punto',TOT[med][k])
        setvar('titulo_procedencia','Procedencia de los insumos importados'+sufijo)
        setvar('subtitulo_procedencia','Cristianismo y Revolución, '+nombre+'. Tamaño de los círculos según: '+medida_txt+'.')
        setvar('unidad_leyenda_punto','El tamaño y el porcentaje indican qué parte de '+('los insumos' if med=='n' else 'las páginas')+(' de la tirada' if acum else ' del ejemplar')+' viene de cada origen.')
        setvar('ranking',ranking(k,med)); setvar('pct_local',PCTLOC[med][k])
        setvar('nota_procedencia','Origen no determinable o que no es un lugar ("N/A", "Che Guevara"): %d insumos (%s páginas); quedan fuera del mapa.'%(noesp.get(k,0),fmt(noesp_pag.get(k,0))))
    else:
        campo={('pag','sin_local'):'opag_',('pag','con_local'):'olpag_',('n','sin_local'):'on_',('n','con_local'):'oln_'}[(med,variante)]+k
        setvar('campo_origen',campo); setvar('tot_origen',TOT[med][k])
        for i,b in enumerate(CORTES_PCT,1): setvar('m%d'%i,b)
        setvar('titulo_origenzona','Procedencia de los insumos importados, por zona'+sufijo)
        setvar('subtitulo_origenzona','Cristianismo y Revolución, '+nombre+'. Medida: '+medida_txt+'.')
        setvar('leyenda_titulo_origenzona','Procedencia por zona'); setvar('leyenda_sub_origenzona','Porcentaje de '+('las páginas' if med=='pag' else 'los insumos')+(' de la tirada' if acum else ' del ejemplar')+' que son importados de cada zona.')
        es=['sin insumos importados','hasta %d %%'%CORTES_PCT[0]]+['de %d a %d %%'%(CORTES_PCT[i-1],CORTES_PCT[i]) for i in range(1,5)]+['más de %d %%'%CORTES_PCT[4]]
        for i,e in enumerate(es): setvar('e%d_origenzona'%i,e)
        setvar('pie_leyenda_origenzona',('Los insumos de un país o de una región se suman a la zona en que está. Argentina muestra la producción local ('+PCTLOC[med][k]+' del total).') if variante=='con_local' else 'Los insumos de un país o de una región se suman a la zona en que está. La producción local no se mapea.')
        setvar('nota_origenzona','Origen no determinable o que no es un lugar ("N/A", "Che Guevara"): %d insumos (%s páginas); quedan fuera del mapa.'%(noesp.get(k,0),fmt(noesp_pag.get(k,0))))
    lay=LAY[kind]
    ex=QgsLayoutExporter(lay); st=QgsLayoutExporter.ImageExportSettings(); st.dpi=300   # nitidez de los PNG (150 alcanza para pantalla)
    d=destino or (OUT+'mapas/'); os.makedirs(d,exist_ok=True)
    nom={'zonas':'zonas','procedencia':'procedencia','origenzona':'procedencia-por-zona'}[kind]
    mm={'pag':'paginas','n':'insumos'}[med]
    fn=d+'%s_%s_%s.png'%(nom,mm,('totalidad_tirada' if acum else 'ej_'+ej.replace('/','_')))
    if kind=='origenzona' and variante=='con_local': fn=fn.replace('.png','_con_local.png')
    r=ex.exportToImage(fn,st); return fn,r
noesp_zona=meta['tricont_n']
def guardar_proyecto():
    """Guarda mapas_CyR.qgz con las mismas capas, estilos, variables, láminas y vistas (temas) con las que se dibujó todo."""
    # variables del proyecto en el estado "totalidad de la tirada, en páginas" (los 3 tipos)
    for kind in ('zonas','procedencia','origenzona'): render(kind,'acum','pag',destino=OUT+'mapas/')
    tc=prj.mapThemeCollection()
    for nombre,capas in (('Zonas',[ez,zon,base]),('Procedencia',[pun,arg,base]),('Procedencia por zona',[ez2,zon2,base])):
        rec=QgsMapThemeCollection.MapThemeRecord(); recs=[]
        for l in capas:
            r=QgsMapThemeCollection.MapThemeLayerRecord(l); r.usingCurrentStyle=True; r.currentStyle=l.styleManager().currentStyle(); recs.append(r)
        rec.setLayerRecords(recs); tc.insert(nombre,rec)
    for n in prj.layerTreeRoot().findLayers(): n.setItemVisibilityChecked(n.layer() in (ez,zon,base))   # al abrir, se ve el tema 'Zonas'
    prj.setTitle('Mapas CyR'); prj.setFilePathStorage(Qgis.FilePathType.Relative)
    ruta=os.path.join(OUT,'mapas_CyR.qgz'); print('proyecto',prj.write(ruta),ruta)

if __name__=='__main__':
    if sys.argv[1:]==['proyecto']: guardar_proyecto(); sys.exit(0)   # solo guarda mapas_CyR.qgz
    pedidos=sys.argv[1:]
    if not pedidos:   # sin argumentos: todos los mapas (3 tipos x 2 medidas x ejemplares + totalidad de la tirada)
        for k in [v for v in KEY.values()]+['acum']:
            for kind in ('zonas','procedencia','origenzona'):
                for med in ('pag','n'): pedidos.append('%s:%s:%s'%(kind,med,k))
    for w in pedidos:
        p=w.split(':'); kind,med,k=p[0],p[1],p[2]; var=p[3] if len(p)>3 else 'sin_local'; dest=p[4] if len(p)>4 else None
        print(render(kind,k,med,var,dest))
    if not sys.argv[1:]: guardar_proyecto()   # corrida completa: también se guarda el proyecto de QGIS
