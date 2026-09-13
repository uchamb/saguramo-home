"""Executed in build_mansard.py's Blender context; geometry from the marked plan."""
st=G['east_stair'];cx,cy=st['turn_center_xy'];w=st['width_m'];rh=st['rail_height_m'];rise=st['riser_m']
timber=bpy.data.materials['Second-floor concept | natural oak boards']
# Individual closed wood treads on a black steel frame; turn has fan-shaped treads.
for step in st['steps']:
 o=prism('EAST STAIR | tread %02d'%step['index'],step['geometry'],step['top_m']-.055,step['top_m'],timber,'13');solid_names.append(o.name);o['step_number']=step['index'];o['top_m']=step['top_m']
# The side stringers and handrails share the same continuous ascent line.
# At the tight inner turn a single full-height newel supports the fan treads.
for label,path in [('outer',st['outer_rail_path']),('inner',st['inner_rail_path'])]:
 for a,b in zip(path,path[1:]):
  if math.dist(a[:2],b[:2])<.001:continue
  beam('EAST STAIR | '+label+' steel stringer',(a[0],a[1],max(.06,a[2]-.07)),(b[0],b[1],b[2]-.07),.11,black,'13')
  beam('EAST STAIR | '+label+' handrail',(a[0],a[1],a[2]+rh),(b[0],b[1],b[2]+rh),.045,black,'13')
  count=max(1,math.ceil(math.dist(a[:2],b[:2])/.12))
  for j in range(count):
   t=j/count;p=[a[k]+(b[k]-a[k])*t for k in range(3)]
   box('EAST STAIR | '+label+' vertical guard',(p[0],p[1],p[2]+rh/2),(.018,.018,rh),black,'13')
 for j in [0,len(path)-1]:
  p=path[j];box('EAST STAIR | '+label+' end post',(p[0],p[1],p[2]+rh/2),(.055,.055,rh),black,'13')
# Inner newel stands on Terrace 2; radial steel bearers support the winding steps.
newel_top=(st['lower_treads']+st['winder_treads'])*rise+rh
box('EAST STAIR | turn newel support',(cx,cy,newel_top/2),(.09,.09,newel_top),black,'13')
box('EAST STAIR | turn support base plate',(cx,cy,.008),(.20,.20,.016),black,'13')
for i in range(st['winder_treads']):
 angle=-math.pi/2+(i+.5)*math.pi/(2*st['winder_treads']);z=(st['lower_treads']+i+1)*rise-.105
 beam('EAST STAIR | winder radial bearer',(cx,cy,z),(cx+w*math.cos(angle),cy+w*math.sin(angle),z),.08,black,'13')
# Welded connection to upper-deck railing posts leaves the full stair mouth open.
for x,endpoint in [(cx,cx-.06),(cx+w,cx+w+.06)]:
 beam('EAST STAIR | landing guard connection',(x,st['top_y'],F+rh-.025),(endpoint,st['top_y']+.075,F+rh-.025),.045,black,'13')
for y in [cy-w,cy]:box('EAST STAIR | foot plate',(st['start_x']+.04,y,.009),(.22,.15,.018),black,'13')
