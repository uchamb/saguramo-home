"""Add the owner-marked gable roof, south dormer room and upper terrace guards.
Run on the saved flat-floor stage; see README for the rebuild sequence.
"""
import bpy,math,json,ast,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P.parent
G=json.loads((P/'mansard_geometry.json').read_text());F=G['floor_level_m']
assert not bpy.data.collections.get('10 Mansard roof'),'Start from the flat-floor stage'
COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
for node in ast.parse((OUT/'build_house.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['move','mat','meshobj','prism','box','beam','camera']:exec(compile(ast.Module(body=[node],type_ignores=[]),'build_house.py','exec'))
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world),[m.name if m else None for m in o.data.materials],[p.material_index for p in o.data.polygons])).encode()).hexdigest()
original={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
source_hash=hashlib.sha256((OUT/'Saguramo_House_Roof_Updated.blend').read_bytes()).hexdigest()
base=bpy.data.scenes['01 Exterior']
for name in ['10 Mansard roof','11 Upper terrace railings','12 Mansard south room']:
 c=bpy.data.collections.new(name);COL[name[:2]]=c
 for sc in list(bpy.data.scenes):sc.collection.children.link(c)
plaster=bpy.data.materials['Warm interior plaster'];black=bpy.data.materials['Detail | black door and railing finish']
roof=bpy.data.materials['Roof | new black coated metal'].copy();roof.name='Mansard | charcoal standing seam'
wood=mat('Mansard | warm timber cladding',(.32,.17,.075),.52)
n=wood.node_tree.nodes;l=wood.node_tree.links;geo=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(35,35,2);l.new(geo.outputs['Generated'],scale.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3;noise.inputs['Detail'].default_value=3;l.new(scale.outputs[0],noise.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.14,.061,.022,1);r.color_ramp.elements[1].color=(.44,.27,.13,1);l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
glass=mat('Mansard | clear terrace glazing',(.77,.86,.88),.08);bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=1;bs.inputs['IOR'].default_value=1.45
solid_names=[]
def solid(name,verts,faces,material,col):
 o=meshobj(name,verts,faces,material,col);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();solid_names.append(o.name);return o
def extrusion(name,poly,axis,lo,hi,material,col):
 def co(p,t):return (t,p[0],p[1]) if axis==0 else (p[0],t,p[1])
 k=len(poly);v=[co(p,t) for t in [lo,hi] for p in poly];faces=[tuple(reversed(range(k))),tuple(range(k,k*2))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
 return solid(name,v,faces,material,col)
def zplane(p,x,y):return p[0]*x+p[1]*y+p[2]
for spec in G['roof_planes']:
 p=spec['plane'];o=prism('MANSARD | '+spec['name'],spec['geometry'],0,.06,roof,'10');solid_names.append(o.name)
 for v in o.data.vertices:v.co.z=zplane(p,v.co.x,v.co.y)+v.co.z-.06
 o.data.update();o['roof_plane']=p;o['sheet_thickness_vertical_m']=.06
 # Closed trapezoid standing seams clipped to each actual roof polygon.
 verts=[];faces=[]
 for a,b in spec['rib_lines']:
  start=len(verts)
  for x,y in [a,b]:
   for dy,dz in [(-.02,0),(-.006,.02),(.006,.02),(.02,0)]:verts.append((x,y+dy,zplane(p,x,y+dy)+dz))
  faces.extend([tuple(start+i for i in [3,2,1,0]),tuple(start+i for i in [4,5,6,7])]+[tuple(start+j for j in [i,(i+1)%4,(i+1)%4+4,i+4]) for i in range(4)])
 solid('MANSARD | seams | '+spec['name'],verts,faces,roof,'10')
x0,y0,x1,y1=G['roof_bounds_xy'];xr=G['ridge_x'];peak=G['ridge_top_m']
south,north,dormer=[s['plane'] for s in G['roof_planes']]
# Folded cap closes the ridge; its visible crest is exactly five metres above deck.
profile=[(xr-.12,zplane(south,xr-.12,0)+.025),(xr,peak),(xr+.12,zplane(north,xr+.12,0)+.025),(xr+.12,zplane(north,xr+.12,0)+.012),(xr,peak-.013),(xr-.12,zplane(south,xr-.12,0)+.012)]
extrusion('MANSARD | ridge cap | 5m above wooden floor',profile,1,y0,y1,roof,'10')
for y,label in [(y0,'east'),(y1,'west')]:
 extrusion('MANSARD | '+label+' gable enclosure',[(x0,F),(x1,F),(xr,G['ridge_sheet_m']-.06)],1,y+.025 if y==y0 else y-.145,y+.145 if y==y0 else y-.025,wood,'12')
 # End flashing follows both roof slopes without adding height at the ridge.
 for a,b,p in [(x0,xr,south),(xr,x1,north)]:
  poly=[(a,zplane(p,a,y)-.09),(b,zplane(p,b,y)-.09),(b,zplane(p,b,y)),(a,zplane(p,a,y))]
  extrusion('MANSARD | '+label+' barge flashing',poly,1,y-.015,y+.015,roof,'10')
# Broad south shed dormer: real enclosed room, with no sloping main sheet inside.
r=G['south_room'];front,dy0,back,dy1=r['bounds_xy'];yc=(dy0+dy1)/2;head=F+r['door_height_m'];front_top=r['front_roof_z']-.06;back_top=r['back_roof_z']-.06
for y,label in [(dy0,'east'),(dy1,'west')]:
 extrusion('MANSARD ROOM | '+label+' cheek',[(front,F),(back,F),(back,back_top),(front,front_top)],1,y if y==dy0 else y-.12,y+.12 if y==dy0 else y,wood,'12')
box('MANSARD ROOM | rear wall',((back-.06),yc,(F+back_top)/2),(.12,dy1-dy0,back_top-F),plaster,'12')
gl0=yc-r['glazing_group_width_m']/2;gl1=yc+r['glazing_group_width_m']/2
for a,b in [(dy0,gl0),(gl1,dy1)]:box('MANSARD ROOM | south front pier',(front+.06,(a+b)/2,(F+front_top)/2),(.12,b-a,front_top-F),wood,'12')
box('MANSARD ROOM | door header',(front+.06,yc,(head+front_top)/2),(.12,gl1-gl0,front_top-head),wood,'12')
# Interior lining under shed roof, an actual sloping ceiling.
ceiling=prism('MANSARD ROOM | ceiling',G['roof_planes'][2]['geometry'],0,.018,plaster,'12');solid_names.append(ceiling.name)
for v in ceiling.data.vertices:v.co.z=zplane(dormer,v.co.x,v.co.y)-.06-v.co.z
bm=bmesh.new();bm.from_mesh(ceiling.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ceiling.data);bm.free();ceiling.data.update()
# Full-height black framed sidelights and centre door.
d0,d1=yc-.5,yc+.5
for y in [gl0,d0,d1,gl1]:box('MANSARD ROOM | black glazing jamb',(front-.012,y,F+1.10),(.085,.045,2.20),black,'12')
for z in [F+.025,head-.025]:box('MANSARD ROOM | glazing horizontal frame',(front-.012,yc,z),(.085,3.20,.05),black,'12')
for a,b,label in [(gl0,d0,'east fixed pane'),(d0,d1,'terrace door glass'),(d1,gl1,'west fixed pane')]:
 o=box('MANSARD ROOM | '+label,(front-.015,(a+b)/2,F+1.10),(.014,b-a-.05,2.10),glass,'12');o['opening_to']='Upper wooden terrace on south side'
for y in [d0+.043,d1-.043]:box('MANSARD ROOM | door leaf stile',(front-.026,y,F+1.10),(.05,.025,2.10),black,'12')
box('MANSARD ROOM | terrace door pull',(front-.095,d1-.105,F+1.08),(.035,.025,.28),black,'12')
for z in [F+.96,F+1.20]:box('MANSARD ROOM | handle stand-off',(front-.06,d1-.105,z),(.08,.022,.022),black,'12')
# Thin vertical shadow joints reinforce the timber finish without changing the envelope.
for a,b in [(dy0+.08,gl0-.08),(gl1+.08,dy1-.08)]:
 y=a
 while y<b:
  box('MANSARD ROOM | timber joint',(front-.001,y,(F+front_top)/2),(.002,.005,front_top-F),black,'12');y+=.14
# Continuous guards on the wooden deck exterior; none blocks the room doorway.
ring=G['railing_ring'];height=G['railing_height_m'];post_positions={};guard_segments=[]
for idx,(a,b) in enumerate(zip(ring,ring[1:])):
 va,vb=Vector(a),Vector(b);length=(vb-va).length;nspan=math.ceil(length/1.5)
 for i in range(nspan+1):
  p=va+(vb-va)*(i/nspan);post_positions[(round(p.x,5),round(p.y,5))]=p
 for z,w in [(F+height-.025,.05),(F+.115,.035)]:beam('UPPER TERRACE | horizontal rail',(*a,z),(*b,z),w,black,'11')
 bars=math.ceil(length/.12)
 for j in range(1,bars):
  p=va+(vb-va)*j/bars;box('UPPER TERRACE | vertical baluster',(p.x,p.y,F+.60),(.018,.018,.93),black,'11')
 guard_segments.append({'start':a,'end':b,'length_m':length})
for p in post_positions.values():
 box('UPPER TERRACE | square post',(p.x,p.y,F+height/2),(.055,.055,height),black,'11');box('UPPER TERRACE | base plate',(p.x,p.y,F+.007),(.11,.11,.014),black,'11')
# New upper geometry is excluded from the ground-floor and basement cutaway scenes.
for sc in bpy.data.scenes:
 for lc in sc.view_layers[0].layer_collection.children:
  if lc.name[:2] in ['10','11','12'] and sc.name[:2] in ['02','03','05']:lc.exclude=True
views=[('18 Mansard concept','concept',(-24,-27,24),(0,.3,3),32),('19 Mansard plan','plan',(.6,1.6,40),(.6,1.6,0),24),('20 South dormer and terrace','south-dormer',(-13,-13,11),(.8,-1.7,4.9),18)]
for title,key,pos,target,scale in views:
 sc=bpy.data.scenes.new(title)
 for c in base.collection.children:sc.collection.children.link(c)
 bpy.context.window.scene=sc;bpy.context.view_layer.update();sc.camera=camera('Camera mansard '+key,pos,target,scale)
 if key=='plan':sc.camera.rotation_euler=(0,0,0)
 sc.world=base.world;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True;sc.render.resolution_x=1700;sc.render.resolution_y=1300;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 for lc in sc.view_layers[0].layer_collection.children:lc.exclude=lc.name[:2]=='08'
 sc.render.filepath=str(P/(key+'.png'))
notes=f'''MANSARD CONCEPT — OWNER-MARKED ROOF AND SOUTH TERRACE ROOM
Roof plan follows the red rectangle; ridge follows the blue line.
Two straight slopes form an upside-down V, with a broad south shed dormer.
The visible ridge crest is 5.000m above the wooden floor ({peak:.5f}m absolute).
The floor remains 300mm thick at {F:.5f}m, 100mm above the existing black roof.
A timber-clad room with clear sidelights and a 1m terrace door is enclosed
within the south dormer. It opens directly onto the upper wooden terrace.
Black vertical-bar guards, 1.10m high, follow all exposed deck perimeter edges.
Both original black roofs and every pre-existing mesh are unchanged.
Room width/depth, 2.20m door height, charcoal finish and railing profiles are
concept choices based on the supplied images, not surveyed construction details.
Roof footprint approx. 8.05 x 10.85m; room gross area {r['area_m2']:.2f}m2.
Scenes 18–20 show this stage; second-floor/ retains the historical flat stage.
'''
textblock=bpy.data.texts.get('SECOND FLOOR - current concept stage');textblock.clear();textblock.write(notes);(P/'NOTES.txt').write_text(notes)
bpy.context.window.scene=bpy.data.scenes['18 Mansard concept'];bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_rotation=bpy.data.objects['Camera mansard concept'].rotation_euler.to_quaternion();area.spaces.active.region_3d.view_location=(0,.3,3);area.spaces.active.region_3d.view_distance=33
assert all(sig(bpy.data.objects[k])==v for k,v in original.items()),'Existing geometry changed'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Second_Floor_Concept.blend'))
(P/'build_validation.json').write_text(json.dumps({'preserved_mesh_signatures':original,'existing_house_sha256':source_hash,'closed_solids':solid_names,'guard_segments':guard_segments,'railing_posts':len(post_positions),'ridge_top_m':peak,'floor_top_m':F,'views':[v[0] for v in views]},indent=2)+'\n')
for title,*_ in views:bpy.ops.render.render(write_still=True,scene=title)
print('MANSARD_BUILD_COMPLETE')
