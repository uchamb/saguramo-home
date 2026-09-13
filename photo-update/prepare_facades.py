from pathlib import Path
import json
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
OUT=Path(__file__).resolve().parent;D=json.loads((OUT.parent/'survey_geometry.json').read_text());R=D['levels']['main']
def geom(r):
 g=r['geometry'];return Polygon(g['rings'][0],g['rings'][1:])
rooms=unary_union([geom(r) for r in R if r['type']=='iataki'])
def pack(g):
 if g.geom_type!='Polygon':return {'parts':[pack(p) for p in g.geoms if p.area>1e-9]}
 rings=[list(g.exterior.coords)]+[list(r.coords) for r in g.interiors]
 return {'rings':rings,'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms],'area':g.area,'interior_midpoints': [[(a[0]+b[0])/2,(a[1]+b[1])/2] for ring in rings for a,b in zip(ring,ring[1:]) if rooms.distance(Point((a[0]+b[0])/2,(a[1]+b[1])/2))<.005]}
updates=[]
def add(name,ids,sill,head,panels,facade,transom=None,frosted=False,g=None):
 if g is None:
  g=unary_union([geom(R[i]) for i in ids]);g=g.buffer(.0002,join_style=2).buffer(-.0002,join_style=2)
 xmin,ymin,xmax,ymax=g.bounds;alongx=xmax-xmin>ymax-ymin
 rec={'name':name,'source_records':ids,'sill':sill,'head':head,'panels':panels,'facade':facade,'transom':transom,'frosted':frosted,'bounds':g.bounds,'center':list(g.centroid.coords)[0],'geometry':pack(g),'width':max(xmax-xmin,ymax-ymin),'height_basis':'Estimated from facade photograph; width follows survey unless marked new opening'}
 updates.append(rec)
add('East glazed doorway',[4,39,5],.035,2.40,[.336,.681],'east')
add('East tall window 1',[6],.10,2.40,[],'east',{'height':2.03,'panels':[0]})
add('East tall window 2',[7],.10,2.40,[],'east',{'height':2.03,'panels':[0]})
add('East three-panel window',[8],.58,2.25,[1/3,2/3],'east')
add('West four-panel glazing',[12,38,13],.035,2.65,[1.4/5.42,.5,1-1.4/5.42],'west')
add('West high frosted window',[11],1.35,2.10,[],'west',{'height':1.96,'panels':[0]},True)
add('South recessed veranda window',[3],.80,2.25,[.55],'south',{'height':1.98,'panels':[0]})
# The source wall has no opening on this face. Place the photographed opening
# centrally in the small room's outer wall, retaining its measured wall footprint.
wall=geom(R[17]);newcut=box(-6.60,-6.417,-5.95,-4.507);opening=wall.intersection(newcut);remaining=wall.difference(newcut)
assert opening.geom_type=='Polygon' and opening.area>.5
add('South missing three-panel window',[],.60,2.25,[1/3,2/3],'south',g=opening)
updates[-1]['height_basis']='Opening width 1.91m and centred placement estimated from south photo; exterior wall dimensions unchanged'
assert abs(remaining.area+opening.area-wall.area)<1e-8
result={'sources':{'east':'IMG_2621.HEIC','south':'IMG_2622.HEIC','west':'IMG_2623.HEIC'},'updates':updates,'south_wall':{'record':17,'geometry':pack(remaining),'original_area':wall.area},'main_area_unchanged':sum(r['survey_area'] for r in R if r['type'] in ['iataki','veranda','terasa'])}
(OUT/'facade_adjustments.json').write_text(json.dumps(result,indent=2))
for r in updates: print(r['name'],'width',round(r['width'],3),'sill/head',r['sill'],r['head'])
