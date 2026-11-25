# Genera datos_visor.js (los números que muestra el visor) a partir de los CSV de Insumos/.
# Uso:  python3 datos_visor.py   (desde la carpeta "Scripts (opcional)")
import csv,json,os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
I=os.path.join(R,'Insumos')
Z=list(csv.DictReader(open(os.path.join(I,'resumen_zonas.csv'),encoding='utf-8')))
P=list(csv.DictReader(open(os.path.join(I,'procedencia_para_qgis.csv'),encoding='utf-8')))
E={r['id_ejemplar']:r for r in csv.DictReader(open(os.path.join(I,'resumen_ejemplares.csv'),encoding='utf-8'))}
# Los ejemplares del visor salen de SIG ejemplares: los que tienen completo = 1 (igual que los mapas).
# valor de la lista del visor -> clave de columna en los CSV
LISTA=[]; CLAVES={'totalidad_tirada':'acum'}
for r in csv.DictReader(open(os.path.join(I,'resumen_ejemplares.csv'),encoding='utf-8')):
    if r['id_ejemplar']=='acum' or r['completo']!='1': continue
    n,anio=r['ejemplar'].split('/'); v='ej_'+r['ejemplar'].replace('/','_'); mes=r['mes_año'] or anio
    CLAVES[v]=r['id_ejemplar']; LISTA.append([v,n+' · '+mes,'Ejemplar '+n+' · '+mes])
LISTA.insert(0,['totalidad_tirada','Totalidad de la tirada (%d ejemplares)'%len(LISTA),'Totalidad de la tirada (%d ejemplares)'%len(LISTA)])
PZR=list(csv.DictReader(open(os.path.join(I,'resumen_procedencia_zonas.csv'),encoding='utf-8')))   # procedencia sumada por zona (pestaña SIG procedencia-zona)
def f(x): return float(x or 0)
def pg(k): return 'paginas_'+('acumuladas' if k=='acum' else k)   # columna de páginas
def ar(k): return 'articulos_'+('acumulados' if k=='acum' else k)   # columna de artículos
D={}
for v,k in CLAVES.items():
    zonas=[[r['zona'],round(f(r[pg(k)]),2),int(f(r[ar(k)]))] for r in Z if f(r[ar(k)])>0 or f(r[pg(k)])>0]
    proc=[[r['origen'],r['lugar'],r['tipo'],round(f(r[pg(k)]),2),int(f(r[ar(k)]))] for r in P if f(r[ar(k)])>0]
    origenzona=sorted([[r['zona'],round(f(r[pg(k)]),2),int(f(r[ar(k)]))] for r in PZR if f(r[pg(k)])>0 or f(r[ar(k)])>0],key=lambda t:-t[1])
    zonas.sort(key=lambda t:-t[1]); proc.sort(key=lambda t:(-t[4],-t[3]))
    e=E[k]
    D[v]={'zonas':zonas,'proc':proc,'origenzona':origenzona,
      'total':[int(f(e['articulos_total'])),round(f(e['paginas_total']),2)],
      'importado':[int(f(e['articulos_importados'])),round(f(e['paginas_importadas']),2)],
      'local':[int(f(e['articulos_locales'])),round(f(e['paginas_locales']),2)],
      'indeterminado':[int(f(e['articulos_sin_origen'])),round(f(e['paginas_sin_origen']),2)]}
D['_lista']=LISTA
open(os.path.join(R,'datos_visor.js'),'w',encoding='utf-8').write('// Generado desde los CSV de Insumos/. No editar a mano.\nwindow.DATOS='+json.dumps(D,ensure_ascii=False)+';\n')
print('ok',len(D))
