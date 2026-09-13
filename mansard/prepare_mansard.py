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
x0,x1,xr=-.15,8.58,3.95;y0,y1=-6.95,4.65
H=5.0;peak=F+H;ridge_surface=peak-.04;eave=F+.06
dy0,dy1=-5.297,1.647  # Preserve the approved south room dimensions and location.
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
# The east stair follows the owner's green L-shaped outline. Tread count is
# sized to the actual 3.25064m rise; the sketch does not prescribe individual steps.
width=1.10;lower_count=9;winder_count=4;upper_count=5
riser_count=lower_count+winder_count+upper_count+1
riser=F/riser_count;upper_going=.25;lower_going=.26
cx=xr-width/2;cy=-7.95-upper_count*upper_going
start_x=cx-lower_count*lower_going
steps=[]
def tread(poly):
 steps.append({'index':len(steps)+1,'geometry':geometry(Polygon(poly)),'top_m':(len(steps)+1)*riser})
for i in range(lower_count):
 a=start_x+i*lower_going;b=a+lower_going
 tread([(a,cy-width),(b,cy-width),(b,cy),(a,cy)])
for i in range(winder_count):
 a=-math.pi/2+i*math.pi/(2*winder_count);b=a+math.pi/(2*winder_count)
 arc=[(cx+width*math.cos(t),cy+width*math.sin(t)) for t in np.linspace(a,b,9)]
 tread([(cx,cy)]+arc)
for i in range(upper_count):
 a=cy+i*upper_going;b=a+upper_going
 tread([(cx,a),(cx+width,a),(cx+width,b),(cx,b)])
# Handrails follow both flights and the outside of the turning treads.
outer_path=[[start_x,cy-width,0],[cx,cy-width,lower_count*riser]]
for i in range(1,17):
 t=-math.pi/2+i*math.pi/32
 outer_path.append([cx+width*math.cos(t),cy+width*math.sin(t),(lower_count+i*winder_count/16)*riser])
outer_path.append([cx+width,-7.95,F])
inner_path=[[start_x,cy,0],[cx,cy,lower_count*riser],[cx,cy,(lower_count+winder_count)*riser],[cx,-7.95,F]]
stair={'width_m':width,'riser_count':riser_count,'riser_m':riser,'lower_going_m':lower_going,'upper_going_m':upper_going,'lower_treads':lower_count,'winder_treads':winder_count,'upper_treads':upper_count,'turn_center_xy':[cx,cy],'start_x':start_x,'top_y':-7.95,'floor_start_m':0,'floor_end_m':F,'steps':steps,'outer_rail_path':outer_path,'inner_rail_path':inner_path,'rail_height_m':1.10,'basis':'Owner green outline: approach along Terrace 2, quarter-turn winders, then ascend westwards to the east upper terrace. Concept dimensions; 19 risers resolve the actual floor rise.'}
# Keep guards on the terrace; remove the entire north run and the west run
# beside the extended roof, and leave a clear stair mouth in the east run.
guard_ring=list(deck.buffer(-.075,join_style=2).exterior.coords);segments=[]
for a,b in zip(guard_ring,guard_ring[1:]):
 if abs(a[0]-(x1-.075))<1e-6 and abs(b[0]-(x1-.075))<1e-6:continue
 if abs(a[1]-(y1-.075))<1e-6 and abs(b[1]-(y1-.075))<1e-6:
  segments.append([list(a),[x0-.03,a[1]]]);continue
 if abs(a[1]+7.875)<1e-6 and abs(b[1]+7.875)<1e-6:
  lo,hi=sorted([a[0],b[0]])
  segments.extend([[[lo,a[1]],[cx-.06,a[1]]],[[cx+width+.06,a[1]],[hi,a[1]]]])
 else:segments.append([list(a),list(b)])
# One-piece, triangulated gable section with a genuine floor-level door opening.
gable=Polygon([(x0,F),(x1,F),(xr,ridge_surface-.06)])
door_cut=Polygon([(xr-1.6,F-1),(xr+1.6,F-1),(xr+1.6,F+2.2),(xr-1.6,F+2.2)])
gable_opening=geometry(gable.difference(door_cut))
report={'floor_level_m':F,'ridge_height_above_floor_m':H,'ridge_top_m':peak,'ridge_sheet_m':ridge_surface,'eave_sheet_m':eave,'roof_bounds_xy':[x0,y0,x1,y1],'ridge_x':xr,'roof_planes':planes,'roof_footprint':geometry(roof_footprint),'terrace_geometry':geometry(terrace),'terrace_area_m2':terrace.area,'floor_area_m2':deck.area,'railing_segments':segments,'railing_height_m':1.10,'east_setback_m':y0-deck.bounds[1],'gable_geometry':gable_opening,'gable_doors':{'center_x':xr,'group_width_m':3.20,'door_width_m':1.0,'door_height_m':2.20,'east_y':y0,'west_y':y1},'east_stair':stair,'south_room':{'bounds_xy':[front,dy0,back,dy1],'front_roof_z':front_z,'back_roof_z':back_z,'area_m2':notch.area,'door_width_m':1.0,'door_height_m':2.20,'glazing_group_width_m':3.20,'front_height_m':2.54},'references':['reference/roof-plan.png','reference/south-dormer.png','reference/roof-plan-stair.png'],'plan_trace_basis':'Owner revision extends the north eave and west gable to the wooden-floor edges, leaves 1m on the east and retains the blue ridge at local X=3.95m. Ridge crest exactly 5m above the floor.','room_basis':'Approved south shed dormer retained; matching glazed doors added to east and west gables. Room size, cladding and glazing layout are concept choices.'}
(P/'mansard_geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print('Mansard bounds',report['roof_bounds_xy'],'ridge top',peak,'terrace',terrace.area,'room',notch.area,'stair riser',riser)
