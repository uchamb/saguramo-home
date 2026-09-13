import json,math
from pathlib import Path
import shapefile
from shapely.geometry import shape,mapping,Polygon,Point,box
from shapely import constrained_delaunay_triangles
from shapely.ops import transform,triangulate,unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
origin=(479384.0,4638555.0)
# Plan X follows the east-facing dimension line; plan Y points toward rear of drawing.
v=(-0.14084,0.99003);norm=math.hypot(*v);u=(v[0]/norm,v[1]/norm);w=(-u[1],u[0])
def local(x,y,z=None):
 dx=x-origin[0];dy=y-origin[1];return dx*u[0]+dy*u[1],dx*w[0]+dy*w[1]
def pack(g):
 if g.geom_type=='Polygon':
  return {'rings':[list(g.exterior.coords)]+[list(r.coords) for r in g.interiors], 'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms], 'area':g.area}
 return {'parts':[pack(p) for p in g.geoms if p.geom_type=='Polygon']}
data={'origin_utm':origin,'local_x_utm':u,'local_y_utm':w,'crs':'EPSG:32638','levels':{},'site':{}}
colors={'kedeli':'#ab623e','fanjara':'#3eabc4','karebi':'#e4b447','iataki':'#ede6d7','veranda':'#a6b9a0','terasa':'#b6ada4','kibe':'#c7c5c0','kibis baqani':'#c7c5c0'}
fig,axs=plt.subplots(1,2,figsize=(17,10))
for ax,(key,folder) in zip(axs,[('main','shp sartuli'),('basement','shp sardafi')]):
 records=[];gs=[]
 for i,s in enumerate(shapefile.Reader(str(ROOT/folder/'unit_polygon.shp')).iterShapeRecords()):
  a=s.record.as_dict();g=transform(local,shape(s.shape.__geo_interface__));assert g.is_valid
  rec={'id':i,'type':a['SUB_TYPE'],'height':a['HEIGHT'],'survey_area':a['Shape_Area'],'geometry':pack(g),'bounds':g.bounds,'center':list(g.centroid.coords)[0]}
  records.append(rec);gs.append(g)
  xx,yy=g.exterior.xy;ax.fill(xx,yy,color=colors.get(rec['type'],'pink'),edgecolor='#555555',linewidth=.5)
  c=g.representative_point();ax.text(c.x,c.y,str(i)+ ('\n%.2f'%g.area if rec['type'] in ['iataki','veranda','terasa'] else ''),ha='center',va='center',fontsize=7)
 rooms=unary_union([g for g,r in zip(gs,records) if r['type']=='iataki'])
 for r,g in zip(records,gs):
  r['geometry']['interior_midpoints']=[[(a[0]+b[0])/2,(a[1]+b[1])/2] for ring in r['geometry']['rings'] for a,b in zip(ring,ring[1:]) if rooms.distance(Point((a[0]+b[0])/2,(a[1]+b[1])/2))<.005]
  if key=='main' and r['id'] in [25,26]:
   guard=g.intersection(box(-20,8.827,-2.808,20));full=g.difference(guard)
   r['guard_geometry']=pack(guard);r['full_height_geometry']=pack(full)
 data['levels'][key]=records
 ax.set_aspect('equal');ax.set_title(key);ax.grid(alpha=.2)
 for r in records: print(key,r['id'],r['type'],'bounds',*[round(v,3) for v in r['bounds']])
 # Close submillimetre survey gaps before making a continuous slab.
 slab=unary_union([g for g,r in zip(gs,records) if r['type'] not in ['kibe','kibis baqani']]).buffer(.002,join_style=2).buffer(-.002,join_style=2)
 data['levels'][key+'_slab']=pack(slab)
for name in ['nakveti','shenoba','valdebuleba']:
 g=transform(local,shape(shapefile.Reader(str(ROOT/'shp'/f'{name}.shp')).shape(0).__geo_interface__))
 data['site'][name]=pack(g)
# Open the assumed ground above the stairwell so grade does not cut through steps.
parcel=transform(local,shape(shapefile.Reader(str(ROOT/'shp/nakveti.shp')).shape(0).__geo_interface__))
stairwell=unary_union([Polygon(r['geometry']['rings'][0]) for r in data['levels']['basement']])
data['site']['terrain']=pack(parcel.difference(stairwell.buffer(.03,join_style=2)))
fig.tight_layout();fig.savefig(OUT/'reference/geometry-map.png',dpi=150)
(OUT/'survey_geometry.json').write_text(json.dumps(data,indent=2))
