"""blender --background ../Saguramo_House.blend --python update_facades.py"""
import bpy,math,json,ast,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;OUT=HERE.parent
A=json.loads((HERE/'facade_adjustments.json').read_text())
COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
# Reuse mesh primitives without executing the scene-resetting original builder.
source=(OUT/'build_house.py').read_text();tree=ast.parse(source)
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['move','mat','meshobj','prism','box','beam','camera']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(OUT/'build_house.py'),'exec'))
brick=bpy.data.materials['Brick | photo-matched terracotta'];plaster=bpy.data.materials['Warm interior plaster'];metal=bpy.data.materials['Dark powder-coated frames'];glass=bpy.data.materials['Smoky glazing'];floor=bpy.data.materials['Warm stone floors']
frost=mat('Photo update | frosted glass',(.55,.59,.59),.34);frost.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.30
sheer=mat('Photo update | sheer curtain',(.65,.63,.56),.9);sheer.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.25

def signature(o):
 if o.type!='MESH':return None
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world),[m.name for m in o.data.materials])).encode()).hexdigest()
ids={i for r in A['updates'] for i in r['source_records']};prefixes=[f'MAIN {i:02d} |' for i in ids]+['MAIN 17 | kedeli']
targets=[o for o in bpy.data.objects if any(o.name.startswith(p) for p in prefixes)]
untouched={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o not in targets}
removed=[o.name for o in targets]
for o in targets:bpy.data.objects.remove(o,do_unlink=True)
# Fill only the surviving parts of the original south wall. Opening + residual
# wall is exactly the original measured wall footprint.
wall=prism('MAIN 17 | kedeli | south window correction',A['south_wall']['geometry'],0,2.9,brick,'01')
for ob in (wall if isinstance(wall,list) else [wall]):
 ob['source']='shp sartuli/unit_polygon.shp, record 17; opening added from IMG_2622.HEIC';ob['original_wall_area_m2']=A['south_wall']['original_area'];ob['photo_override']=True
for r in A['updates']:
 name='PHOTO | '+r['name'];g=r['geometry'];sill=r['sill'];head=r['head'];w=r['width'];cx,cy=r['center'];x0,y0,x1,y1=r['bounds'];alongx=x1-x0>y1-y0
 before=set(bpy.data.objects.keys())
 if sill>0:prism(name+' sill wall',g,0,sill,brick,'01')
 prism(name+' lintel',g,head,2.9,brick,'01')
 prism(name+' threshold',g,-.025,.005,floor,'02')
 def part(suffix,a0,a1,z0,z1,depth,material,offset=0):
  pos=(cx+(a0+a1)/2,cy+offset,(z0+z1)/2) if alongx else (cx+offset,cy+(a0+a1)/2,(z0+z1)/2)
  size=(a1-a0,depth,z1-z0) if alongx else (depth,a1-a0,z1-z0)
  ob=box(name+' | '+suffix,pos,size,material,'03');return ob
 f=.055;cuts=[-w/2]+[-w/2+w*p for p in r['panels']]+[w/2]
 for idx,a in enumerate(cuts):
  thick=f if idx in [0,len(cuts)-1] else .065
  a0=max(-w/2,a-thick/2);a1=min(w/2,a+thick/2)
  # Full 55mm outer jambs, no duplicate frame at old survey subdivisions.
  if idx==0:a0=-w/2;a1=-w/2+f
  if idx==len(cuts)-1:a0=w/2-f;a1=w/2
  part(f'frame vertical {idx}',a0,a1,sill,head,.09,metal)
 for z in [sill+f/2,head-f/2]:part('outer horizontal',-w/2,w/2,z-f/2,z+f/2,.09,metal)
 # Model each glazing panel separately, including the small top lights.
 for k,(a,b) in enumerate(zip(cuts,cuts[1:])):
  low=sill+f;high=head-f;aa=a+(f if k==0 else .0325);bb=b-(f if k==len(cuts)-2 else .0325)
  trans=r['transom'];split=trans and k in trans['panels']
  zones=[(low,trans['height']-.0225),(trans['height']+.0225,high)] if split else [(low,high)]
  if split:part(f'top-light transom {k}',aa,bb,trans['height']-.0225,trans['height']+.0225,.085,metal)
  for j,(zlo,zhi) in enumerate(zones):part(f'glass panel {k}.{j}',aa,bb,zlo,zhi,.018,frost if r['frosted'] else glass)
  # Secondary sash outline for central casement and sliding sections.
  if len(cuts)==4 and k==1 or r['facade']=='west' and len(cuts)==5 and k in [1,2]:
   border=.021
   for x in [aa+border/2,bb-border/2]:part(f'sash stile {k}',x-border/2,x+border/2,low,high,.065,metal)
   for z in [low+border/2,high-border/2]:part(f'sash rail {k}',aa,bb,z-border/2,z+border/2,.065,metal)
  # Window hardware is approximate; openings and divisions follow the photo.
  if (len(cuts)==2 and not r['frosted']) or k==1:
   hw=aa+.09;hz=max(low+.25,min(1.15,high-.2));offset=-.056 if r['facade']=='east' else .056
   part(f'handle {k}',hw-.015,hw+.015,hz-.075,hz+.075,.035,metal,offset)
  # Recessed sheers reproduce observed light glazing without replacing glass.
  curtain=(r['name'].startswith('East tall') or r['name']=='West four-panel glazing' or r['name']=='East glazed doorway' and k!=1)
  if curtain:
   offset=.12 if r['facade']=='east' else -.12
   part(f'curtain {k} | appearance estimate',aa+.015,bb-.015,low+.02,high-.02,.004,sheer,offset)
 # Outer sill cap is visible on raised windows only.
 if sill>.3:part('projecting sill',-w/2-.035,w/2+.035,sill-.025,sill,.22,metal)
 for name2 in set(bpy.data.objects.keys())-before:
  ob=bpy.data.objects[name2];ob['photo_source']=A['sources'][r['facade']];ob['facade']=r['facade'];ob['opening']=r['name'];ob['sill_m']=sill;ob['head_m']=head;ob['basis']=r['height_basis'];ob['survey_records']=str(r['source_records'])
 # Verify the presence of real empty opening space between solid sill/lintel.
 assert head>sill and head<=2.9
# The whole rest of the original model must remain identical.
assert all(name in bpy.data.objects and signature(bpy.data.objects[name])==sig for name,sig in untouched.items())
# Add convenient facade scenes. Labels are the user's facade names.
base=bpy.data.scenes['01 Exterior']
settings=[('06 East windows','east',(1,-35,3.1),(1,-7.2,1.4),18.5),('07 South windows','south',(-35,1.7,3.3),(-2,1.7,1.4),21.5),('08 West windows','west',(1,35,3.1),(1,9.3,1.4),18.0)]
for title,key,pos,target,scale in settings:
 sc=bpy.data.scenes.new(title)
 for col in base.collection.children:sc.collection.children.link(col)
 bpy.context.window.scene=sc;bpy.context.view_layer.update()
 sc.camera=camera('Camera photo comparison '+key,pos,target,scale)
 sc.world=base.world;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True
 sc.render.resolution_x=1800;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 for c in sc.view_layers[0].layer_collection.children:c.exclude=c.name[:2]=='08'
 sc.render.filepath=str(HERE/(key+'.png'))
text='''PHOTO UPDATE — EAST, SOUTH AND WEST WINDOWS

Compared with IMG_2621.HEIC (east), IMG_2622.HEIC (south), IMG_2623.HEIC (west).
Original Saguramo_House.blend is preserved. Room geometry, surveyed wall
footprint and all other original meshes are unchanged except targeted openings.

East: three-part full-height glazed doorway, two narrow full-height windows
with top lights, and a lower-sill three-panel window.
South: added the missing three-panel window to the small projecting room;
corrected the recessed veranda window. Deeply obscured doors are unchanged.
West: four-panel full-height glazing, plus the small high frosted window.

Opening widths and positions follow the survey, except the missing south
window: its 1.91m width and placement are estimated from the photograph.
All opening sill/head heights are photo estimates, not measured elevations.
Sill/head values and source photos are stored on corrected objects and in
photo-update/facade_adjustments.json. Frames, hardware and sheers are visual
approximations. North facade was not changed. Roof remains the earlier estimate.

Use scenes 06, 07 and 08 to inspect the updated facades directly.
'''
bpy.data.texts.new('PHOTO UPDATE - East South West').write(text)
(HERE/'PHOTO_UPDATE_NOTES.txt').write_text(text)
bpy.context.window.scene=base
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Photo_Updated.blend'))
report={'untouched_original_meshes_verified':len(untouched),'removed_target_objects':removed,'updated_opening_groups':len(A['updates']),'scene_count':len(bpy.data.scenes),'rooms_and_terrace_area_m2':A['main_area_unchanged'],'original_blend_preserved':True}
(HERE/'update_validation.json').write_text(json.dumps(report,indent=2))
for title,key,*_ in settings:bpy.ops.render.render(write_still=True,scene=title)
base.render.filepath=str(HERE/'exterior.png');bpy.ops.render.render(write_still=True,scene=base.name)
print('PHOTO_UPDATE_COMPLETE',json.dumps(report))
