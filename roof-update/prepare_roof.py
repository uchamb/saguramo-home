from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
OUT=Path(__file__).resolve().parent
faces=[]
E=3.125;H=4.625 # roof surface includes 125mm estimated build-up above owner 3m wall
# Local metres: +X north along the plan, +Y west. Calibrated to the building
# survey and overhead DJI_0667, with eaves/ridges checked in oblique views.
A=(-4.59,-7.95,E);B=(8.58,-7.95,E);C=(8.58,4.65,E);D=(-4.59,4.65,E)
R1=(1.48,-1.78,H);R2=(2.50,-1.78,H)
t=(-5.48-A[1])/(R1[1]-A[1]);Q=tuple(A[i]+t*(R1[i]-A[i]) for i in range(3))
P=(-4.20,-5.48,Q[2]);EA=(-6.85,-7.95,E);EB=(-6.85,-3.01,E);EC=(-4.59,-3.01,E)
def add(name,pts,material,axis,structural=True,ribs=True):
 pts=[list(p) for p in pts];g=Polygon([p[:2] for p in pts]);assert g.is_valid and g.area>.001,name
 plane=np.linalg.lstsq(np.array([[p[0],p[1],1] for p in pts]),np.array([p[2] for p in pts]),rcond=None)[0]
 residual=max(abs(np.dot(plane,[p[0],p[1],1])-p[2]) for p in pts);assert residual<1e-7,(name,residual)
 lines=[]
 if ribs:
  # axis X: ribs run down X, repeat across Y. axis Y: the reverse.
  cross=1 if axis=='X' else 0
  mn=g.bounds[cross];mx=g.bounds[cross+2];spacing=.18 if material!='charcoal' else .21
  val=math.ceil(mn/spacing)*spacing
  safe=g.buffer(-.018,join_style=2)
  while val<mx:
   line=LineString([(-30,val),(30,val)]) if cross==1 else LineString([(val,-30),(val,30)])
   hit=line.intersection(safe)
   for part in getattr(hit,'geoms',[hit]):
    if part.geom_type=='LineString' and part.length>.04:lines.append([list(part.coords[0]),list(part.coords[-1])])
   val+=spacing
 faces.append({'name':name,'vertices':pts,'material':material,'axis':axis,'plane':plane.tolist(),'structural':structural,'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms],'ribs':lines,'area':g.area})
 return faces[-1]
add('Main east hip',[A,B,R2,R1],'silver','Y')
add('Main north hip',[B,C,R2],'silver','X')
west=add('Main west hip',[C,D,R1,R2],'silver','Y')
add('Main south hip with extension valley',[EC,D,R1,Q],'silver','X')
add('Red corner front hip',[EA,EB,P],'red','X')
east_ext=add('Corner east extension',[EA,P,Q,A],'silver','Y')
west_ext=add('Corner west extension',[EB,EC,Q,P],'silver','Y')
def z(face,x,y,offset=0):a,b,c=face['plane'];return a*x+b*y+c+offset
# Distinct red patches are coplanar sheet areas, not extra roof ridges.
redxy=[(-6.85,-7.95),(-4.20,-5.48),(-2.74,-5.48),(-2.74,-7.95)]
add('Red east corner sheets',[(x,y,z(east_ext,x,y,.008)) for x,y in redxy],'red','Y',False)
redxy=[(-6.85,-3.01),(-4.59,-3.01),(-4.59,-4.92),(-4.20,-5.48)]
add('Red west corner sheets',[(x,y,z(west_ext,x,y,.008)) for x,y in redxy],'red','Y',False)
redxy=[(-.82,-7.95),(4.75,-7.95),(1.94,-4.93)]
add('Red triangular east patch',[(x,y,z(faces[0],x,y,.008)) for x,y in redxy],'red','Y',False)
# West roof has an annex projection in its perimeter, clearly visible overhead.
westxy=[(-4.59,4.65),(8.58,4.65),(8.58,9.60),(.45,9.60),(.45,11.28),(-4.59,11.28)]
add('Dark west roof and annex',[(x,y,E-.06*(y-4.65)) for x,y in westxy],'charcoal','Y')
canopyxy=[(-7.38,-3.01),(-4.59,-3.01),(-4.59,11.38),(-7.38,11.38)]
add('Dark south veranda canopy',[(x,y,E+.02*(x+4.59)) for x,y in canopyxy],'charcoal','X')
# A small gable projects above the west hip. Its front face is solid red metal.
G0=(2.10,-1.16,z(west,2.10,-1.16)+.025)
GL=(.65,2.28,z(west,.65,2.28)+.025);GR=(3.39,2.28,z(west,3.39,2.28)+.025);GC=(2.10,2.28,G0[2])
add('Raised gable south slope',[G0,GC,GL],'silver','X',False)
add('Raised gable north slope',[G0,GR,GC],'silver','X',False)
# User finish instruction: retain the new black roof; recolor every older roof reddish.
faces=[f for f in faces if f['name'] not in ['Red east corner sheets','Red west corner sheets','Red triangular east patch']]
for f in faces:
 f['observed_material']=f['material']
 if f['material']=='silver':f['material']='red'
# Reference outline plot and full coordinate specification.
seams=[('Main ridge',R1,R2,'silver'),('North-east hip',B,R2,'silver'),('North-west hip',C,R2,'silver'),('South-west hip',D,R1,'silver'),('South-east hip',Q,R1,'silver'),('Corner ridge',P,Q,'red'),('Corner east hip',EA,P,'red'),('Corner west hip',EB,P,'red'),('Extension valley',EC,Q,'red'),('Raised gable ridge',G0,GC,'red'),('Raised gable left trim',GL,GC,'red'),('Raised gable right trim',GR,GC,'red')]
report={'sources':[f'DJI_{i:04d}.JPG' for i in range(659,668)],'finish_instruction':'Keep later-added dark sections black; make every older roof reddish','black_slopes':{'south_fall_m_per_m':.02,'west_fall_m_per_m':.06,'common_high_edge_z_m':E,'wall_height_high_m':3.0,'roof_build_up_m':.125},'main_eave_m':E,'ridge_m':H,'roof_faces':faces,'seams':[(n,a,b,'red' if m=='silver' else m) for n,a,b,m in seams],'gable_front':[GL,GR,GC],'gable_bottom':[G0,GL,GR],'assumptions':'Photo-traced roof shape; survey-aligned footprint. Owner wall height 3m; black slopes south 2% and west 6%. Roof build-up 125mm, red-roof pitch, overhangs and sheet profiles estimated.'}
outline=unary_union([Polygon([v[:2] for v in f['vertices']]) for f in faces if f['structural']]).buffer(.00001,join_style=2).buffer(-.00001,join_style=2)
report['outline']=[list(p.exterior.coords) for p in getattr(outline,'geoms',[outline])]
# Retain roof-plane breakpoints even where the union removes collinear vertices.
# A single fascia must never bridge both a hip plane and a black roof plane.
for ri,ring in enumerate(report['outline']):
 split=[]
 for a,b in zip(ring,ring[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];ll=dx*dx+dy*dy
  points={0:tuple(a)}
  if ll>1e-12:
   for f in faces:
    if not f['structural']:continue
    for v in f['vertices']:
     t=((v[0]-a[0])*dx+(v[1]-a[1])*dy)/ll
     if 1e-6<t<1-1e-6 and abs((v[0]-a[0])*dy-(v[1]-a[1])*dx)/math.sqrt(ll)<1e-5:points[t]=(a[0]+t*dx,a[1]+t*dy)
  split.extend(p for t,p in sorted(points.items()))
 report['outline'][ri]=split+[split[0]]

(OUT/'roof_geometry.json').write_text(json.dumps(report,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(10,10))
for f in faces:
 p=f['vertices'];ax.fill([v[1] for v in p],[v[0] for v in p],color={'silver':'#bcc5c0','red':'#8a4148','charcoal':'#41494b'}[f['material']],edgecolor='white',lw=1)
ax.invert_yaxis();ax.set_aspect('equal');ax.set_xlabel('Local Y / west (m)');ax.set_ylabel('Local X / north (m)');ax.set_title('Roof outline aligned to overhead drone view')
fig.savefig(OUT/'reference/roof-layout.png',dpi=160,bbox_inches='tight')
print('Prepared',len(faces),'roof surfaces;',sum(len(f['ribs']) for f in faces),'corrugation ribs')
