from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
P=Path(__file__).resolve().parent;OUT=P.parent
floor=json.loads((OUT/'second-floor/floor_geometry.json').read_text());validation=json.loads((OUT/'second-floor/verification.json').read_text());F=validation['flat_floor_top_m']
# Aligned to surveyed room-wall lines on the marked plan. +X north, +Y west.
# The red rectangle and blue ridge are approximate hand-drawn boundaries.
x0,x1,xr=-.15,7.90,3.95;y0,y1=-7.25,3.60
H=5.0;peak=F+H;ridge_surface=peak-.04;eave=F+.06
ys=(y0+y1)/2;room_width=(y1-y0)*.64;dy0,dy1=ys-room_width/2,ys+room_width/2
front=x0;back=x0+(xr-x0)*.64
roof_footprint=Polygon([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
deck=Polygon(floor['geometry']['rings'][0]);terrace=deck.difference(roof_footprint)
def geometry(g):
 if g.is_empty:return None
 if g.geom_type=='MultiPolygon':return {'parts':[geometry(x) for x in g.geoms]}
 return {'rings':[list(g.exterior.coords)]+[list(r.coords) for r in g.interiors],'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms],'area':g.area}
planes=[]
def add(name,shape,plane,axis):
 ribs=[];lo=shape.bounds[1] if axis=='X' else shape.bounds[0];hi=shape.bounds[3] if axis=='X' else shape.bounds[2];v=math.ceil(lo/.22)*.22
 while v<hi:
  line=LineString([(-30,v),(30,v)]) if axis=='X' else LineString([(v,-30),(v,30)])
  cut=line.intersection(shape.buffer(-.015,join_style=2))
  for p in getattr(cut,'geoms',[cut]):
   if p.geom_type=='LineString' and p.length>.03:ribs.append([list(p.coords[0]),list(p.coords[-1])])
  v+=.22
 planes.append({'name':name,'geometry':geometry(shape),'plane':plane,'rib_lines':ribs})
south_slope=(ridge_surface-eave)/(xr-x0);north_slope=(ridge_surface-eave)/(x1-xr)
south_plane=[south_slope,0,eave-south_slope*x0];north_plane=[-north_slope,0,eave+north_slope*x1]
main_south=Polygon([(x0,y0),(xr,y0),(xr,y1),(x0,y1)])
# Main south sheet is cut around the dormer, providing an actual room opening.
notch=Polygon([(front,dy0),(back,dy0),(back,dy1),(front,dy1)])
add('Main south slope with dormer opening',main_south.difference(notch),south_plane,'X')
add('Main north slope',Polygon([(xr,y0),(x1,y0),(x1,y1),(xr,y1)]),north_plane,'X')
back_z=south_slope*back+south_plane[2];front_z=F+2.60
dormer_slope=(back_z-front_z)/(back-front);dormer_plane=[dormer_slope,0,front_z-dormer_slope*front]
add('South shed dormer roof',notch,dormer_plane,'X')
# Railing follows all outer edges of the uncovered wooden deck. The adjacent
# black roofs are lower non-terrace surfaces, so those deck edges are guarded too.
guard_ring=deck.buffer(-.075,join_style=2).exterior.coords
report={'floor_level_m':F,'ridge_height_above_floor_m':H,'ridge_top_m':peak,'ridge_sheet_m':ridge_surface,'eave_sheet_m':eave,'roof_bounds_xy':[x0,y0,x1,y1],'ridge_x':xr,'roof_planes':planes,'roof_footprint':geometry(roof_footprint),'terrace_geometry':geometry(terrace),'terrace_area_m2':terrace.area,'floor_area_m2':deck.area,'railing_ring':list(guard_ring),'railing_height_m':1.10,'south_room':{'bounds_xy':[front,dy0,back,dy1],'front_roof_z':front_z,'back_roof_z':back_z,'area_m2':notch.area,'door_width_m':1.0,'door_height_m':2.20,'glazing_group_width_m':3.20,'front_height_m':2.54},'references':['reference/roof-plan.png','reference/south-dormer.png'],'plan_trace_basis':'Hand-marked red limits aligned to source room walls, approximately 8.05m x 10.85m; blue ridge at local X=3.95m. Eaves lie at wooden-floor level. Ridge crest exactly 5m above the floor per owner.','room_basis':'Broad shed dormer on south slope, as owner reference; room size, cladding and glazing layout are concept choices.'}
(P/'mansard_geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print('Mansard bounds',report['roof_bounds_xy'],'ridge top',peak,'terrace',terrace.area,'room',notch.area)
