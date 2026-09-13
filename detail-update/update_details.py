"""Apply close-up Childroom door and basement guard corrections to latest model."""
import bpy,math,json,ast,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P.parent
G=json.loads((P/'detail_geometry.json').read_text());COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
for node in ast.parse((OUT/'build_house.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['move','mat','meshobj','prism','box','beam','camera']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(OUT/'build_house.py'),'exec'))
brick=bpy.data.materials['Brick | photo-matched terracotta'];plaster=bpy.data.materials['Warm interior plaster'];metal=bpy.data.materials['Dark powder-coated frames'];glass=bpy.data.materials['Smoky glazing'];stone=bpy.data.materials['Warm stone floors']
def signature(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world),[m.name for m in o.data.materials])).encode()).hexdigest()
prefixes=[f'MAIN {i:02d} |' for i in [9,32,10]]
targets=[o for o in bpy.data.objects if any(o.name.startswith(p) for p in prefixes) or 'low stair enclosure' in o.name]
assert len([o for o in targets if 'low stair enclosure' in o.name])==2
unchanged={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o not in targets}
removed=[o.name for o in targets]
for o in targets:bpy.data.objects.remove(o,do_unlink=True)
# Dedicated finishes prevent changes to any unrelated windows or roof hardware.
metal=mat('Detail | black door and railing finish',(.008,.010,.012),.38,.15)
glass=mat('Detail | clear door glazing',(.80,.88,.90),.075,0)
glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=1.0
glass.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.45
start_objects=set(bpy.data.objects.keys());r=G['opening'];x0,y0,x1,y1=r['bounds'];width=x1-x0;cy=(y0+y1)/2+.025;sill=r['sill_m'];head=r['head_m'];f=r['frame_face_m'];name='DETAIL | Childroom to Terrace 1'
prism(name+' | lintel',r['geometry'],head,3,brick,'01')
prism(name+' | stone threshold',r['geometry'],-.025,sill,stone,'02')
def part(label,xa,xb,za,zb,depth,ma,offset=0):
 return box(name+' | '+label,((xa+xb)/2,cy+offset,(za+zb)/2),(xb-xa,depth,zb-za),ma,'03')
cuts=[x0]+[x0+width*v for v in r['panel_splits']]+[x1]
for i,x in enumerate(cuts):
 a=x0 if i==0 else x1-f if i==3 else x-.0325
 b=x0+f if i==0 else x1 if i==3 else x+.0325
 part('vertical frame '+str(i),a,b,sill,head,.09,metal)
for z in [sill,head-f]:part('horizontal outer frame',x0,x1,z,z+f,.09,metal)
# Fine tracks along the floor and header, with no horizontal transom.
for off in [-.045,.045]:part('sliding threshold track',x0+f,x1-f,sill+.005,sill+.016,.012,metal,off)
screenmat=mat('Detail | charcoal pleated insect screen',(.035,.040,.041),.82)
curtainmat=mat('Detail | warm off-white sheers',(.67,.65,.57),.95)
curtainmat.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value=.25
# Closed thin corrugated sheet: editable mesh with real pleat depth.
def folded_sheet(label,a,b,zlo,zhi,offset,pitch,amplitude,material):
 count=max(4,math.ceil((b-a)/pitch)*2);verts=[]
 for side in [0,.001]:
  for z in [zlo,zhi]:
   for i in range(count+1):
    x=a+(b-a)*i/count;wave=amplitude*(1 if i%2 else -1)
    verts.append((x,cy+offset+wave+side,z))
 n=count+1;faces=[]
 for side in range(2):
  base=2*n*side
  for i in range(count):faces.append((base+i,base+i+1,base+n+i+1,base+n+i))
 for level in range(2):
  base=level*n
  for i in range(count):faces.append((base+i,base+2*n+i,base+2*n+i+1,base+i+1))
 faces.extend([(0,n,3*n,2*n),(n-1,2*n-1,4*n-1,3*n-1)])
 ob=meshobj(name+' | '+label,verts,faces,material,'03')
 import bmesh
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 return ob
for k,(a,b) in enumerate(zip(cuts,cuts[1:])):
 aa=a+(f if k==0 else .0325);bb=b-(f if k==2 else .0325);low=sill+f;high=head-f
 if k in [0,2]:
  part('full-height side glass '+str(k),aa,bb,low,high,.018,glass,-.012)
  folded_sheet('sheer behind side glass '+str(k),aa+.018,bb-.018,low+.025,high-.02,-.095,.055,.012,curtainmat)
 else:
  # The centre is the dark, vertically pleated screen seen in the reference.
  for x in [aa,bb-.025]:part('screen sash stile',x,x+.025,low,high,.055,metal,.021)
  for z in [low,high-.023]:part('screen sash rail',aa,bb,z,z+.023,.055,metal,.021)
  folded_sheet('centre pleated insect screen',aa+.025,bb-.025,low+.023,high-.023,.016,r['pleat_pitch_m'],.007,screenmat)
  part('screen pull handle',bb-.044,bb-.025,1.03,1.21,.026,metal,.061)
for n in set(bpy.data.objects.keys())-start_objects:
 ob=bpy.data.objects[n];ob['owner_room']='Childroom';ob['connects_to']='Terrace 1';ob['reference']='detail-update/reference/childroom-door.png';ob['survey_records']='9,32,10';ob['basis']=r['basis']
# Horizontal guards on both sides of the stair void; neither access end is closed.
rails=G['railings'];created_rails=[]
for run in rails['runs']:
 before=set(bpy.data.objects.keys());a=Vector((*run['start'],0));b=Vector((*run['end'],0));length=(b-a).length;direction=(b-a).normalized();prefix='DETAIL | Basement railing | '+run['name'];post=.045
 postcount=math.ceil(length/1.6)
 for i in range(postcount+1):
  v=a+(b-a)*i/postcount
  box(prefix+' | post',(*v.xy,.475),(.045,.045,.95),metal,'04')
  box(prefix+' | base plate',(*v.xy,.004),(.085,.085,.008),metal,'04')
 # Rectangular rails, unlike round tubing; same matte black finish as posts.
 for label,z,h in [('top handrail',.925,.05),('bottom rail',.075,.035)]:
  ob=box(prefix+' | '+label,((a.x+b.x)/2,(a.y+b.y)/2,z),(length+.045,.045,h),metal,'04');ob.rotation_euler.z=math.atan2(direction.y,direction.x)
 for bay in range(postcount):
  left=bay*length/postcount+post/2;right=(bay+1)*length/postcount-post/2
  n=max(1,math.ceil((right-left)/rails['maximum_bar_pitch_m'])-1)
  for k in range(1,n+1):
   d=left+(right-left)*k/(n+1);v=a+direction*d
   box(prefix+' | vertical iron bar',(*v.xy,(.0925+.90)/2),(.019,.019,.90-.0925),metal,'04')
 for n in set(bpy.data.objects.keys())-before:
  ob=bpy.data.objects[n];ob['reference']='detail-update/reference/basement-railing.png';ob['replaces']='low brick guard records 25 and 26';ob['basis']=rails['basis'];created_rails.append(n)
assert all(name in bpy.data.objects and signature(bpy.data.objects[name])==sig for name,sig in unchanged.items())
# Inspection views; all shared model collections remain present.
base=bpy.data.scenes['01 Exterior']
views=[('12 Childroom terrace door','childroom-door',(-1.55,7.25,1.80),(-1.55,3.67,1.50),3.45),('13 Basement railings','basement-railings',(-10.5,15.5,4.0),(-4.9,9.75,.0),8.7)]
for title,key,pos,target,scale in views:
 sc=bpy.data.scenes.new(title)
 for col in base.collection.children:sc.collection.children.link(col)
 bpy.context.window.scene=sc;bpy.context.view_layer.update();sc.camera=camera('Camera detail '+key,pos,target,scale)
 if key=='childroom-door':sc.camera.data.type='PERSP';sc.camera.data.lens=34
 sc.world=base.world;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True
 sc.render.resolution_x=1300;sc.render.resolution_y=1300 if key=='childroom-door' else 1000;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 for c in sc.view_layers[0].layer_collection.children:c.exclude=c.name[:2]=='08'
 # A soft light confined to this inspection scene reveals shaded terrace details.
 ld=bpy.data.lights.new('Detail fill '+key,'AREA');ld.energy=100 if key=='childroom-door' else 220;ld.shape='DISK';ld.size=3
 light=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
 sc.render.filepath=str(P/(key+'.png'))
notes='''CLOSE-UP CORRECTIONS — CHILDROOM DOOR AND BASEMENT RAILINGS

Childroom to Terrace 1: survey records 9, 32 and 10 form one 2.340m-wide
opening. Raised side-window sills and the narrow solid door are replaced by
full-height side glazing and a central pleated insect screen, black framing,
and a low threshold. Opening head is estimated 2.50m from the reference photo;
viewed from Terrace 1, panels are approximately 29% / 38% / 33% of the
measured opening width. No transom.

Both 0.95m-high brick guards beside the basement stairs are replaced by
black iron railings with square posts, top/bottom rails and straight vertical
bars. Their runs follow the original guard footprints; stair treads and the
open access ends remain unchanged. Rail sections and spacing are estimates.

All unrelated meshes, including room layouts, roof heights/slopes and other
windows, are preserved. Scenes 12 and 13 provide close inspection views.
'''
bpy.data.texts.new('DETAIL UPDATE - door and railings').write(notes);(P/'DETAIL_NOTES.txt').write_text(notes)
bpy.context.window.scene=base;bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_rotation=bpy.data.objects['Camera drone'].rotation_euler.to_quaternion();area.spaces.active.region_3d.view_location=(0,1,1);area.spaces.active.region_3d.view_distance=34
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Roof_Updated.blend'))
report={'removed_objects':removed,'unchanged_mesh_signatures':unchanged,'new_object_names':[o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('DETAIL |')],'railing_objects':created_rails,'door_width_m':width,'door_head_m':head,'door_sill_m':sill,'railing_height_m':.95,'scene_count':len(bpy.data.scenes)}
(P/'build_validation.json').write_text(json.dumps(report,indent=2)+'\n')
for title,key,*_ in views:bpy.ops.render.render(write_still=True,scene=title)
base.render.filepath=str(P/'exterior.png');bpy.ops.render.render(write_still=True,scene=base.name)
print('DETAIL_UPDATE_COMPLETE',len(unchanged),'unrelated meshes preserved')
