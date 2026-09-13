"""Refine basement railing connections/supports and Terrace 1 tile finish."""
import bpy,math,json,ast,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P.parent
COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
for node in ast.parse((OUT/'build_house.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['move','mat','meshobj','box','beam','camera']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(OUT/'build_house.py'),'exec'))
def geometry_sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
def sig(o):return hashlib.sha256((geometry_sig(o)+repr([m.name for m in o.data.materials])).encode()).hexdigest()
oldrails=[o for o in bpy.data.objects if o.name.startswith('DETAIL | Basement railing |')]
assert oldrails
finish_targets=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('MAIN 00 | veranda') or o.name.startswith('Veranda entry step'))]
unchanged={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH' and o not in oldrails and o not in finish_targets}
floors_unchanged={o.name:geometry_sig(o) for o in finish_targets}
removed=[o.name for o in oldrails]
for o in oldrails:bpy.data.objects.remove(o,do_unlink=True)
black=bpy.data.materials['Detail | black door and railing finish']
# Select the actual existing canopy column nearest the terrace-side rail end.
posts=[o for o in bpy.data.objects if o.name.startswith('Veranda steel post')]
existing=min(posts,key=lambda o:math.dist(o.location.xy,(-6.25,8.7)))
ex,ey=existing.location.xy
bathroom_face_x=-2.80862
runs=[{'name':'Terrace 1 side','start':[float(ex),float(ey)],'end':[bathroom_face_x,float(ey)],'existing_column':existing.name},{'name':'Outer side','start':[-6.78862,10.62762],'end':[-2.80860,10.62762],'existing_column':None}]
new_objects=[];columns=[];rail_report=[]
# The west-roof soffit bottom is the roof surface minus the modeled 85mm build-up.
roof=json.loads((OUT/'roof-update/roof_geometry.json').read_text())
west=next(f for f in roof['roof_faces'] if f['name']=='Dark west roof and annex');a,b,c=west['plane']
def soffit(x,y):return a*x+b*y+c-.085
for run in runs:
 before=set(bpy.data.objects.keys());start=Vector((*run['start'],0));end=Vector((*run['end'],0));d=(end-start).normalized();length=(end-start).length
 column_center=end-d*1.0;cx,cy=column_center.xy;h=soffit(cx,cy)
 prefix='DETAIL | Basement railing | '+run['name']
 column=box(prefix+' | full-height roof column 1m from Bathroom 2',(cx,cy,h/2),(.085,.085,h),black,'04')
 # Top vertices meet the existing sloping soffit without changing the roof.
 for v in column.data.vertices:
  if v.co.z>0:
   world=column.matrix_world@v.co
   v.co.z=soffit(world.x,world.y)-column.location.z
 column['distance_from_bathroom2_wall_m']=1.0;column['distance_basis']='Bathroom 2 exterior wall face to column centre, along railing';column['owner_supplied']=True
 box(prefix+' | roof column base plate',(cx,cy,.005),(.14,.14,.010),black,'04')
 columns.append({'name':column.name,'center_xy':[cx,cy],'wall_xy':list(end.xy),'distance_from_wall_m':(end-column_center).length,'roof_underside_z_m':h})
 # Supports are at the wall, the owner-specified full-height column, and ends.
 # Add a low intermediate post only where an individual bay exceeds 1.6m.
 supports=[(0,.085 if run['existing_column'] else .045,'existing' if run['existing_column'] else 'low'),(length-1,.085,'full'),(length,.045,'low')]
 if length-1>1.6:supports.append(((length-1)/2,.045,'low'))
 supports.sort()
 for dist,width,kind in supports:
  if kind!='low':continue
  v=start+d*dist
  box(prefix+' | low post',(*v.xy,.475),(.045,.045,.95),black,'04')
  box(prefix+' | low-post base plate',(*v.xy,.004),(.085,.085,.008),black,'04')
 bar_count=0
 for j,(left,right) in enumerate(zip(supports,supports[1:])):
  lo=left[0]+left[1]/2;hi=right[0]-right[1]/2
  for label,z,thick in [('top handrail',.925,.05),('bottom rail',.075,.035)]:
   # Exact face-to-face rails connect to structural columns; no floating gap.
   av=start+d*lo;bv=start+d*hi
   ob=box(prefix+f' | bay {j} '+label,((av.x+bv.x)/2,(av.y+bv.y)/2,z),(hi-lo,.045,thick),black,'04');ob.rotation_euler.z=math.atan2(d.y,d.x)
  count=max(1,math.ceil((hi-lo)/.12)-1)
  for k in range(1,count+1):
   v=start+d*(lo+(hi-lo)*k/(count+1));box(prefix+' | vertical iron bar',(*v.xy,.49625),(.019,.019,.8075),black,'04');bar_count+=1
 for name in set(bpy.data.objects.keys())-before:
  ob=bpy.data.objects[name];ob['basis']='Owner correction: one roof-height column per railing, 1m from Bathroom 2; Terrace 1 railing connects to existing canopy column';new_objects.append(name)
 rail_report.append({**run,'supports_along_run_m':supports,'length_m':length,'vertical_bars':bar_count})
# Procedural porcelain/stoneware finish, based on the owner's tile close-up.
# A separate material limits the finish to Terrace 1 and its entrance steps.
tile=mat('Terrace 1 | weathered grey taupe square tiles',(.30,.29,.26),.64)
n=tile.node_tree.nodes;l=tile.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs[0],out.inputs['Surface'])
geo=n.new('ShaderNodeNewGeometry');pos=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],pos.inputs[0]);normal=n.new('ShaderNodeVectorMath');normal.operation='ABSOLUTE';l.new(geo.outputs['Normal'],normal.inputs[0]);ns=n.new('ShaderNodeSeparateXYZ');l.new(normal.outputs[0],ns.inputs[0])
def mathnode(op,a,b=None):
 q=n.new('ShaderNodeMath');q.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):q.inputs[i].default_value=v
  else:l.new(v,q.inputs[i])
 return q.outputs[0]
def mix(a,b,f,mode='MIX'):
 q=n.new('ShaderNodeMixRGB');q.blend_type=mode
 for i,v in [(0,f),(1,a),(2,b)]:
  if isinstance(v,(float,int)):q.inputs[i].default_value=v
  elif isinstance(v,tuple):q.inputs[i].default_value=v
  else:l.new(v,q.inputs[i])
 return q.outputs[0]
xface=mathnode('GREATER_THAN',ns.outputs['X'],.5);yface=mathnode('GREATER_THAN',ns.outputs['Y'],.5);vertical=mathnode('ADD',xface,yface)
u=mathnode('ADD',mathnode('MULTIPLY',pos.outputs['X'],mathnode('SUBTRACT',1,xface)),mathnode('MULTIPLY',pos.outputs['Y'],xface))
v=mathnode('ADD',mathnode('MULTIPLY',pos.outputs['Y'],mathnode('SUBTRACT',1,vertical)),mathnode('MULTIPLY',pos.outputs['Z'],vertical))
coords=n.new('ShaderNodeCombineXYZ');l.new(u,coords.inputs['X']);l.new(v,coords.inputs['Y'])
idvec=n.new('ShaderNodeCombineXYZ');l.new(mathnode('FLOOR',mathnode('DIVIDE',u,.50)),idvec.inputs[0]);l.new(mathnode('FLOOR',mathnode('DIVIDE',v,.50)),idvec.inputs[1])
random=n.new('ShaderNodeTexWhiteNoise');l.new(idvec.outputs[0],random.inputs['Vector'])
def ramp(inp,colors):
 q=n.new('ShaderNodeValToRGB');l.new(inp,q.inputs[0]);r=q.color_ramp;r.elements.remove(r.elements[1]);r.elements[0].position=colors[0][0];r.elements[0].color=colors[0][1]
 for t,col in colors[1:]:e=r.elements.new(t);e.color=col
 return q.outputs['Color']
base=ramp(random.outputs['Value'],[(0,(.145,.175,.178,1)),(.25,(.23,.245,.232,1)),(.48,(.285,.255,.220,1)),(.72,(.33,.245,.188,1)),(1,(.38,.335,.278,1))])
shift=n.new('ShaderNodeVectorMath');shift.operation='SCALE';l.new(random.outputs['Color'],shift.inputs[0]);shift.inputs['Scale'].default_value=27
local=n.new('ShaderNodeVectorMath');local.operation='ADD';l.new(coords.outputs[0],local.inputs[0]);l.new(shift.outputs[0],local.inputs[1])
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=8;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.72;l.new(local.outputs[0],noise.inputs['Vector'])
mask=ramp(noise.outputs['Fac'],[(.36,(0,0,0,1)),(.53,(.25,.25,.25,1)),(.66,(.85,.85,.85,1))])
colour=mix(base,(.47,.52,.51,1),mask)
# Fine elongated scuffs give the pale weathered glaze its rubbed appearance.
streakcoords=n.new('ShaderNodeVectorMath');streakcoords.operation='MULTIPLY';l.new(local.outputs[0],streakcoords.inputs[0]);streakcoords.inputs[1].default_value=(2,16,1)
scuff=n.new('ShaderNodeTexNoise');scuff.inputs['Scale'].default_value=16;scuff.inputs['Detail'].default_value=3;l.new(streakcoords.outputs[0],scuff.inputs['Vector'])
colour=mix(colour,scuff.outputs['Fac'],.12,'MULTIPLY')
br=n.new('ShaderNodeTexBrick');br.offset=0;br.offset_frequency=1;br.inputs['Scale'].default_value=1;br.inputs['Brick Width'].default_value=.50;br.inputs['Row Height'].default_value=.50;br.inputs['Mortar Size'].default_value=.0017;br.inputs['Mortar Smooth'].default_value=.0005;br.inputs['Mortar'].default_value=(.17,.16,.14,1)
l.new(coords.outputs[0],br.inputs['Vector']);l.new(colour,br.inputs['Color1']);l.new(colour,br.inputs['Color2']);l.new(br.outputs['Color'],bs.inputs['Base Color'])
rough=mathnode('ADD',.49,mathnode('MULTIPLY',noise.outputs['Fac'],.27));l.new(rough,bs.inputs['Roughness'])
bump=n.new('ShaderNodeBump');bump.invert=True;bump.inputs['Distance'].default_value=.0025;bump.inputs['Strength'].default_value=.7;l.new(br.outputs['Fac'],bump.inputs['Height'])
bump2=n.new('ShaderNodeBump');bump2.inputs['Distance'].default_value=.0006;bump2.inputs['Strength'].default_value=.3;l.new(scuff.outputs['Fac'],bump2.inputs['Height']);l.new(bump.outputs['Normal'],bump2.inputs['Normal']);l.new(bump2.outputs[0],bs.inputs['Normal'])
tile['reference']='terrace-update/reference/terrace-tiles.png';tile['tile_size_m']=.50;tile['tile_size_basis']='Estimated from photograph; owner has not supplied tile dimensions';tile['finish']='Mottled grey, taupe and brown square tiles, pale weathered patches, thin joints';tile['scope']='Terrace 1 and its entry steps'
for o in finish_targets:o.data.materials.clear();o.data.materials.append(tile)
assert all(sig(bpy.data.objects[k])==v for k,v in unchanged.items())
assert all(geometry_sig(bpy.data.objects[k])==v for k,v in floors_unchanged.items())
# Reuse the existing railing inspection; add a tile inspection on Terrace 1.
base=bpy.data.scenes['01 Exterior'];sc=bpy.data.scenes.new('14 Terrace 1 tiles')
for col in base.collection.children:sc.collection.children.link(col)
bpy.context.window.scene=sc;bpy.context.view_layer.update();sc.camera=camera('Camera Terrace 1 tiles',(-6.25,.6,2.65),(-5.1,3.3,0),5.5);sc.camera.data.type='PERSP';sc.camera.data.lens=28
sc.world=base.world;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=True;sc.render.resolution_x=1200;sc.render.resolution_y=1200;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
for cc in sc.view_layers[0].layer_collection.children:cc.exclude=cc.name[:2]=='08'
ld=bpy.data.lights.new('Terrace tile inspection soft light','AREA');ld.energy=170;ld.shape='DISK';ld.size=4
light=bpy.data.objects.new(ld.name,ld);sc.collection.objects.link(light);light.location=(-5.2,2.5,2.8);light.rotation_euler=(0,0,0)
# Area light local -Z points down at the terrace surface.
notes='''TERRACE 1 RAILING SUPPORTS AND TILE FINISH

Terrace-side guard is now aligned with the existing canopy column at
(-6.25, 8.70) and its rails terminate at that column's face.
One 85mm square full-height black column was added to each stair railing.
Each column centre is exactly 1.00m along the rail from Bathroom 2's external
wall, and its top follows the existing roof soffit. Stair access remains open.

Terrace 1 and its entry steps use procedural square tiles in mottled grey,
taupe and brown, with worn pale patches and thin grout joints, based on the
owner photograph. Tile size is assumed 500mm; no measured size was supplied.
No external texture dependency. Floor geometry and all unrelated meshes are
preserved. Scene 14 shows the tiles; scene 13 shows the amended railings.
'''
bpy.data.texts.new('TERRACE UPDATE - supports and tiles').write(notes);(P/'NOTES.txt').write_text(notes)
bpy.context.window.scene=base;bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Roof_Updated.blend'))
report={'unchanged_mesh_signatures':unchanged,'floor_geometry_signatures':floors_unchanged,'replaced_railing_objects':removed,'new_railing_objects':new_objects,'columns':columns,'railings':rail_report,'tile_material':tile.name,'tile_targets':[o.name for o in finish_targets],'tile_size_m':.5,'tile_size_measured':False,'scene_count':14}
(P/'build_validation.json').write_text(json.dumps(report,indent=2)+'\n')
for scene,filename in [('13 Basement railings','basement-railings'),('14 Terrace 1 tiles','terrace-tiles'),('09 Drone roof','overview')]:
 render_scene=bpy.data.scenes[scene];render_scene.render.filepath=str(P/(filename+'.png'));bpy.ops.render.render(write_still=True,scene=scene)
print('TERRACE_UPDATE_COMPLETE',len(unchanged),'unrelated meshes preserved')
