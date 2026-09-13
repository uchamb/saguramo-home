"""Replace the red roof with a flat timber floor; preserve the existing house file."""
import bpy,math,json,ast,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P.parent
G=json.loads((P/'floor_geometry.json').read_text());R=json.loads((OUT/'roof-update/roof_geometry.json').read_text())
COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
for path,names in [(OUT/'build_house.py',['move','mat','meshobj','prism','box','camera']),(OUT/'roof-update/update_roof.py',['inside'])]:
 for node in ast.parse(path.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'))
plaster=bpy.data.materials['Warm interior plaster']
def gs(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
def sig(o):return hashlib.sha256((gs(o)+repr(([m.name for m in o.data.materials],[p.material_index for p in o.data.polygons]))).encode()).hexdigest()
source_hash=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
# Measure evaluated geometry, including corrugation crests and folded flashing.
deps=bpy.context.evaluated_depsgraph_get();black_heights=[]
for ob in COL['05'].objects:
 if ob.type!='MESH' or not any(m and m.name=='Roof | new black coated metal' for m in ob.data.materials):continue
 evaluated=ob.evaluated_get(deps);mesh=evaluated.to_mesh()
 black_heights.append((max((evaluated.matrix_world@v.co).z for v in mesh.vertices),ob.name));evaluated.to_mesh_clear()
black_highest,black_highest_object=max(black_heights)
floor_top=black_highest+G['clearance_above_black_roof_m'];floor_bottom=floor_top-G['floor_thickness_m']

original={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
wall_shapes={o.name:gs(o) for o in COL['01'].objects if o.type=='MESH'}
red=bpy.data.materials['Roof | reddish coated metal'];remove=[o for o in COL['05'].objects if o.type=='MESH' and red in list(o.data.materials)]
# Remove eave trim belonging to the removed red roof; keep all black-roof trim.
for o in COL['05'].objects:
 if not o.name.startswith('ROOF | black perimeter fascia'):continue
 x,y=o.location.xy
 faces=[f for f in R['roof_faces'] if f['structural'] and any(inside((x,y),t) for t in f['triangles'])]
 if faces and all(f['material']=='red' for f in faces):remove.append(o)
# Remove superseded ceiling boards within the new floor volume.
# Retain exactly the parts below black roofs; remove the ceiling overlay below the new floor.
ceiling_remainders=[]
for o in list(COL['05'].objects):
 if not o.name.startswith('Ceiling |'):continue
 bounds=[min(v.co[i] for v in o.data.vertices) for i in range(2)]+[max(v.co[i] for v in o.data.vertices) for i in range(2)]
 match=next((r for r in G['ceilings'] if max(abs(a-b) for a,b in zip(bounds,r['original_bounds']))<.0001),None)
 if match:
  remove.append(o)
  if match['remaining_under_black_roof']:ceiling_remainders.append(match)
removed=[o.name for o in remove]
for o in remove:bpy.data.objects.remove(o,do_unlink=True)
for r in ceiling_remainders:
 result=prism('Ceiling | retained below black roof | room '+str(r['room_id']),r['remaining_under_black_roof'],0,1,plaster,'05')
 for o in result if isinstance(result,list) else [result]:
  for v in o.data.vertices:v.co.z=3-.06*max(0,v.co.y-4.65)+(.04 if v.co.z>.5 else 0)
  o['basis']='Original ceiling retained only beneath unchanged black roof'
# World-position texture coordinates keep the board pattern continuous
# across the entire new floor footprint.
wood=mat('Second-floor concept | natural oak boards',(.36,.20,.085),.55)
n=wood.node_tree.nodes;l=wood.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs[0],out.inputs[0])
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
def mathnode(op,a,b=None):
 m=n.new('ShaderNodeMath');m.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):m.inputs[i].default_value=v
  else:l.new(v,m.inputs[i])
 return m.outputs[0]
row=mathnode('FLOOR',mathnode('DIVIDE',sep.outputs['Y'],.16));offset=mathnode('MULTIPLY',mathnode('MODULO',row,2),.5)
col=mathnode('FLOOR',mathnode('ADD',mathnode('DIVIDE',sep.outputs['X'],1.8),offset))
ids=n.new('ShaderNodeCombineXYZ');l.new(col,ids.inputs[0]);l.new(row,ids.inputs[1]);random=n.new('ShaderNodeTexWhiteNoise');l.new(ids.outputs[0],random.inputs['Vector'])
ram=n.new('ShaderNodeValToRGB');l.new(random.outputs['Value'],ram.inputs[0]);cr=ram.color_ramp;cr.elements[0].color=(.22,.105,.032,1);cr.elements[1].color=(.48,.30,.135,1);e=cr.elements.new(.5);e.color=(.35,.19,.07,1)
vector=n.new('ShaderNodeVectorMath');vector.operation='MULTIPLY';vector.inputs[1].default_value=(2.2,155,8);l.new(geo.outputs['Position'],vector.inputs[0])
grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=1;grain.inputs['Detail'].default_value=4;grain.inputs['Roughness'].default_value=.7;l.new(vector.outputs[0],grain.inputs['Vector'])
grain_ramp=n.new('ShaderNodeValToRGB');l.new(grain.outputs['Fac'],grain_ramp.inputs[0]);grain_ramp.color_ramp.elements[0].position=.22;grain_ramp.color_ramp.elements[0].color=(.32,.22,.12,1);grain_ramp.color_ramp.elements[1].position=.78;grain_ramp.color_ramp.elements[1].color=(1,.92,.75,1)
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.48;l.new(ram.outputs['Color'],mix.inputs[1]);l.new(grain_ramp.outputs[0],mix.inputs[2])
boards=n.new('ShaderNodeTexBrick');boards.offset=.5;boards.offset_frequency=2;boards.inputs['Scale'].default_value=1;boards.inputs['Brick Width'].default_value=1.8;boards.inputs['Row Height'].default_value=.16;boards.inputs['Mortar Size'].default_value=.0008;boards.inputs['Mortar Smooth'].default_value=.0003;boards.inputs['Mortar'].default_value=(.095,.048,.021,1)
l.new(geo.outputs['Position'],boards.inputs['Vector']);l.new(mix.outputs[0],boards.inputs['Color1']);l.new(mix.outputs[0],boards.inputs['Color2']);l.new(boards.outputs['Color'],bs.inputs['Base Color'])
bump=n.new('ShaderNodeBump');bump.invert=True;bump.inputs['Distance'].default_value=.0014;bump.inputs['Strength'].default_value=.5;l.new(boards.outputs['Fac'],bump.inputs['Height'])
bump2=n.new('ShaderNodeBump');bump2.inputs['Distance'].default_value=.00035;bump2.inputs['Strength'].default_value=.25;l.new(grain.outputs['Fac'],bump2.inputs['Height']);l.new(bump.outputs[0],bump2.inputs['Normal']);l.new(bump2.outputs[0],bs.inputs['Normal']);bs.inputs['Roughness'].default_value=.52
wood['finish']='Natural warm oak floor boards with staggered joints and fine grain';wood['dimensions_basis']='Illustrative 160mm-wide, 1.8m-long pattern; no product specified'
slab=prism('CONCEPT | raised second-floor timber deck | 300mm thick',G['geometry'],floor_bottom,floor_top,wood,'05')
slab.data.materials.append(plaster)
for face in slab.data.polygons:
 if face.normal.z<-.5:face.material_index=1
slab['surface_height_m']=floor_top;slab['thickness_m']=G['floor_thickness_m'];slab['clearance_above_black_roof_m']=G['clearance_above_black_roof_m'];slab['stage']=G['stage'];slab['thickness_basis']='Owner-specified 300mm thickness, with top 100mm above evaluated black-roof maximum';slab['footprint_basis']=G['footprint_basis'];slab['area_m2']=G['area_m2']
# Recess only hidden wall-cap vertices by 1mm to avoid coplanar self-shadowing.
# Preserve the initial concept wall-cap clearance; visible wall footprint,
# openings and lower wall vertices are unchanged.
capped=[];wall_adjustments={}
for wall in COL['01'].objects:
 if wall.type!='MESH':continue
 ids=[v.index for v in wall.data.vertices if abs(v.co.z-3)<.00001 and any(inside((v.co.x,v.co.y),t) for t in G['geometry']['triangles'])]
 if not ids:continue
 for i in ids:wall.data.vertices[i].co.z-=.001
 wall.data.update();capped.append(wall.name);wall_adjustments[wall.name]=ids
unchanged={k:v for k,v in original.items() if k not in removed and k not in capped}
assert all(sig(bpy.data.objects[k])==v for k,v in unchanged.items())
assert all(gs(bpy.data.objects[k])==v for k,v in wall_shapes.items() if k not in wall_adjustments)
black_names=[o.name for o in COL['05'].objects if o.type=='MESH' and o.name in unchanged]
# New views clearly distinguish the open concept from the retained existing model.
base=bpy.data.scenes['01 Exterior'];views=[('15 Second floor concept','concept',(-24,-27,23),(0,1,1),30),('16 Second floor plan','plan',(.6,1.6,40),(.6,1.6,0),24),('17 Timber floor detail','wood-detail',(3,-6,8),(1,-2,floor_top),6.5)]
for title,key,pos,target,scale in views:
 sc=bpy.data.scenes.new(title)
 for c in base.collection.children:sc.collection.children.link(c)
 bpy.context.window.scene=sc;bpy.context.view_layer.update();sc.camera=camera('Camera second-floor '+key,pos,target,scale)
 if key=='plan':sc.camera.rotation_euler=(0,0,math.pi/2)
 sc.world=base.world;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.render.resolution_x=1700 if key=='concept' else 1300;sc.render.resolution_y=1300;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 for c in sc.view_layers[0].layer_collection.children:c.exclude=c.name[:2]=='08'
 sc.render.filepath=str(P/(key+'.png'))
notes=f'''SECOND-FLOOR CONCEPT — FLAT WOODEN FLOOR ONLY

All former red roof panels, ribs, ridges, hips, raised gable and their perimeter
trim are removed in this concept. Their combined plan footprint becomes a flat
wooden floor with its top {floor_top:.5f}m above the main floor, exactly 100mm
above the highest black-roof point ({black_highest:.5f}m, including ribs).
The floor is 300mm thick, with its underside at {floor_bottom:.5f}m.
Warm oak board finish is procedural; board sizes remain illustrative.

Both black roof sections, their slopes, corrugations, supports, soffits and
associated trim are retained. Old ceiling portions above the new floor are
removed only within its footprint; the ceiling beneath the black roof remains.
Wall XY, openings and lower vertices are unchanged; hidden cap vertices
under the floor are recessed 1mm solely to avoid coplanar render artifacts.
No mansard, upper-storey walls, pitched roof, access stair or furniture is added.

The original Saguramo_House_Roof_Updated.blend remains unchanged.
Open Saguramo_House_Second_Floor_Concept.blend; scenes 15–17 show this concept.
'''
bpy.data.texts.new('SECOND FLOOR - current concept stage').write(notes);(P/'NOTES.txt').write_text(notes)
bpy.context.window.scene=bpy.data.scenes['15 Second floor concept'];bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_rotation=bpy.data.objects['Camera second-floor concept'].rotation_euler.to_quaternion();area.spaces.active.region_3d.view_location=(0,1,1);area.spaces.active.region_3d.view_distance=32
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Second_Floor_Concept.blend'))
report={'source_model_sha256':source_hash,'removed_roof_and_ceiling_objects':removed,'wall_top_clearance_m':.001,'wall_top_adjustments':wall_adjustments,'unchanged_mesh_signatures':unchanged,'wall_geometry_signatures':wall_shapes,'protected_black_roof_objects':black_names,'floor_object':slab.name,'floor_top_m':floor_top,'floor_bottom_m':floor_bottom,'floor_thickness_m':G['floor_thickness_m'],'black_roof_highest_m':black_highest,'black_roof_highest_object':black_highest_object,'clearance_above_black_roof_m':G['clearance_above_black_roof_m'],'floor_area_m2':G['area_m2'],'retained_ceiling_parts':[r['room_id'] for r in ceiling_remainders],'scene_count':17,'mansard_added':False}
(P/'build_validation.json').write_text(json.dumps(report,indent=2)+'\n')
for title,key,*_ in views:bpy.ops.render.render(write_still=True,scene=title)
print('SECOND_FLOOR_CONCEPT_COMPLETE')
