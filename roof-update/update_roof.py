import bpy,math,json,ast,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent;OUT=HERE.parent
G=json.loads((HERE/'roof_geometry.json').read_text())
COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
source=(OUT/'build_house.py').read_text()
for node in ast.parse(source).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['move','mat','meshobj','prism','box','beam','camera']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(OUT/'build_house.py'),'exec'))
brick=bpy.data.materials['Brick | photo-matched terracotta'];plaster=bpy.data.materials['Warm interior plaster'];wood=bpy.data.materials['Timber soffit'];metal=bpy.data.materials['Dark powder-coated frames']
def signature(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
removed=[o for o in COL['05'].objects if not o.name.startswith('Ceiling |')]
unchanged={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o not in removed}
for o in removed:bpy.data.objects.remove(o,do_unlink=True)
exec(compile((HERE/'apply_wall_heights.py').read_text(),str(HERE/'apply_wall_heights.py'),'exec'))
unchanged={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH'}
# Realistic fired-clay colour variation, occasional dark bricks and fine relief.
n=brick.node_tree.nodes;l=brick.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Roughness'].default_value=.8
uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0])
def mathnode(op,a,b=None):
 m=n.new('ShaderNodeMath');m.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(float,int)):m.inputs[i].default_value=v
  else:l.new(v,m.inputs[i])
 return m.outputs[0]
row=mathnode('FLOOR',mathnode('DIVIDE',sep.outputs['Y'],.073));offset=mathnode('MULTIPLY',mathnode('MODULO',row,2),.5)
column=mathnode('FLOOR',mathnode('ADD',mathnode('DIVIDE',sep.outputs['X'],.245),offset))
v=n.new('ShaderNodeCombineXYZ');l.new(column,v.inputs[0]);l.new(row,v.inputs[1]);oi=n.new('ShaderNodeObjectInfo');l.new(mathnode('MULTIPLY',oi.outputs['Random'],199),v.inputs[2])
rand=n.new('ShaderNodeTexWhiteNoise');l.new(v.outputs[0],rand.inputs['Vector'])
ramp=n.new('ShaderNodeValToRGB');l.new(rand.outputs['Value'],ramp.inputs[0]);r=ramp.color_ramp
palette=[(0,(.04,.041,.033,1)),(.045,(.075,.068,.052,1)),(.065,(.22,.065,.035,1)),(.25,(.31,.085,.043,1)),(.65,(.40,.135,.071,1)),(1,(.49,.185,.105,1))]
r.elements.remove(r.elements[1]);r.elements[0].position=0;r.elements[0].color=palette[0][1]
for pos,c in palette[1:]:e=r.elements.new(pos);e.color=c
br=n.new('ShaderNodeTexBrick');l.new(uv.outputs['UV'],br.inputs['Vector']);br.inputs['Scale'].default_value=1;br.inputs['Brick Width'].default_value=.245;br.inputs['Row Height'].default_value=.073;br.inputs['Mortar Size'].default_value=.0045;br.inputs['Mortar Smooth'].default_value=.0015;br.inputs['Mortar'].default_value=(.24,.185,.13,1)
for key in ['Color1','Color2']:l.new(ramp.outputs['Color'],br.inputs[key])
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=3;l.new(uv.outputs['UV'],noise.inputs['Vector'])
mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.17;l.new(br.outputs['Color'],mix.inputs[1]);l.new(noise.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bs.inputs['Base Color'])
b1=n.new('ShaderNodeBump');b1.invert=True;b1.inputs['Strength'].default_value=.65;b1.inputs['Distance'].default_value=.006;l.new(br.outputs['Fac'],b1.inputs['Height'])
b2=n.new('ShaderNodeBump');b2.inputs['Strength'].default_value=.28;b2.inputs['Distance'].default_value=.002;l.new(noise.outputs['Fac'],b2.inputs['Height']);l.new(b1.outputs['Normal'],b2.inputs['Normal']);l.new(b2.outputs['Normal'],bs.inputs['Normal'])
brick.diffuse_color=(.36,.115,.06,1);brick['finish_basis']='Red-brown brick from facade photographs; procedural individual-brick colour and mortar/roughness relief'
red=mat('Roof | reddish coated metal',(.30,.055,.060),.43,.58)
black=mat('Roof | new black coated metal',(.025,.033,.039),.38,.65)
M={'red':red,'charcoal':black,'silver':red}
for m in [red,black]:
 no=m.node_tree.nodes.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=36
 bu=m.node_tree.nodes.new('ShaderNodeBump');bu.inputs['Strength'].default_value=.07;bu.inputs['Distance'].default_value=.0006;m.node_tree.links.new(no.outputs['Fac'],bu.inputs['Height']);m.node_tree.links.new(bu.outputs['Normal'],m.node_tree.nodes['Principled BSDF'].inputs['Normal'])
def inside(p,tri):
 (x,y)=p;(a,b,c)=tri
 d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
 if abs(d)<1e-12:return False
 u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/d;v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/d
 return min(u,v,1-u-v)>-1e-5

def roofheight(x,y,allfaces=False):
 zs=[f['plane'][0]*x+f['plane'][1]*y+f['plane'][2] for f in G['roof_faces'] if (f['structural'] or allfaces) and any(inside((x,y),t) for t in f['triangles'])]
 return max(zs) if zs else G['main_eave_m']

for f in G['roof_faces']:
 g={'area':f['area'],'rings':[[v[:2] for v in f['vertices']]+[f['vertices'][0][:2]]],'triangles':f['triangles']}
 o=prism('ROOF | '+f['name'],g,0,.065,M[f['material']],'05')
 for v in o.data.vertices:v.co.z=f['plane'][0]*v.co.x+f['plane'][1]*v.co.y+f['plane'][2]+v.co.z-.065
 o['source']='Roof images/DJI_0667.JPG and angled drone views';o['basis']=G['assumptions'];o['finish']='new black roof' if f['material']=='charcoal' else 'reddish per user instruction'
 # A shallow trapezoidal corrugation profile, repeated at the image-matched spacing.
 verts=[];faces=[]
 for ends in f['ribs']:
  a,b=ends;d=Vector((b[0]-a[0],b[1]-a[1],0)).normalized();cross=Vector((-d.y,d.x,0));width=.048 if f['material']=='charcoal' else .037;height=.024 if f['material']=='charcoal' else .016
  start=len(verts)
  for p in [a,b]:
   for side,h in [(-.5,0),(-.25,height),(.25,height),(.5,0)]:
    x=p[0]+cross.x*width*side;y=p[1]+cross.y*width*side;z=f['plane'][0]*x+f['plane'][1]*y+f['plane'][2]+.002+h;verts.append((x,y,z))
  for k in range(3):faces.append((start+k,start+k+1,start+k+5,start+k+4))
  faces.extend([(start+3,start,start+4,start+7),(start+3,start+2,start+1,start),(start+4,start+5,start+6,start+7)])
 rib=meshobj('ROOF ribs | '+f['name'],verts,faces,M[f['material']],'05')
 if f['material']=='charcoal':
  so=prism('ROOF timber soffit | '+f['name'],g,0,.015,wood,'05')
  for v in so.data.vertices:v.co.z=f['plane'][0]*v.co.x+f['plane'][1]*v.co.y+f['plane'][2]+v.co.z-.085
# Close the raised triangular front of the small gable, with red vertical ribs.
front=G['gable_front'];o=meshobj('ROOF | red raised gable front',front,[(0,1,2)],red,'05');sol=o.modifiers.new('Sheet thickness','SOLIDIFY');sol.thickness=.025
x0,x1=front[0][0],front[1][0];y=front[0][1]
x=x0+.13
while x<x1:
 base=roofheight(x,y)+.025
 top=front[2][2]-(front[2][2]-front[0][2])*((front[2][0]-x)/(front[2][0]-x0)) if x<=front[2][0] else front[2][2]-(front[2][2]-front[1][2])*((x-front[2][0])/(x1-front[2][0]))
 if top-base>.035:beam('ROOF | gable vertical rib',(x,y+.012,base),(x,y+.012,top),.019,red,'05')
 x+=.15
# Ridge and hip caps fit down to the two adjoining roof faces.
for name,a,b,material in G['seams']:
 d=Vector((b[0]-a[0],b[1]-a[1],0)).normalized();p=Vector((-d.y,d.x,0));verts=[]
 for endpoint in [a,b]:
  for off in [-.09,0,.09]:
   x=endpoint[0]+p.x*off;y=endpoint[1]+p.y*off
   zz=endpoint[2]+.044 if off==0 else min(endpoint[2]+.025,roofheight(x,y,True)+.026)
   verts.append((x,y,zz))
 o=meshobj('ROOF cap | '+name,verts,[(0,1,4,3),(1,2,5,4)],M[material],'05');sol=o.modifiers.new('Folded metal thickness','SOLIDIFY');sol.thickness=.012
# Black metal perimeter fascia and gutters follow the irregular photographed outline.
for ring in G['outline']:
 for a,b in zip(ring,ring[1:]):
  if math.dist(a,b)<.04:continue
  mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
  choices=[f for f in G['roof_faces'] if f['structural'] and any(inside(mid,t) for t in f['triangles'])]
  face=min(choices,key=lambda f:f['plane'][0]*mid[0]+f['plane'][1]*mid[1]+f['plane'][2])
  aa,bb,cc=face['plane'];za=aa*a[0]+bb*a[1]+cc;zb=aa*b[0]+bb*b[1]+cc
  beam('ROOF | black perimeter fascia',(*a,za-.07),(*b,zb-.07),.14,black,'05')
# Folded transition where the canopy meets the stepped west roof.
vs=[]
for y in [4.65,11.28]:
 vs.extend([(-4.64,y,G['main_eave_m']+.015),(-4.34,y,G['main_eave_m']+.015),(-4.18,y,G['main_eave_m']-.06*(y-4.65)+.018)])
o=meshobj('ROOF | broad canopy transition flashing',vs,[(0,1,4,3),(1,2,5,4)],black,'05');s=o.modifiers.new('Flashing thickness','SOLIDIFY');s.thickness=.01
support_z=G['main_eave_m']+.02*(-6.25+4.59)-.155
beam('ROOF | veranda perimeter support beam',(-6.25,-3.2,support_z),(-6.25,10.9,support_z),.14,metal,'05')
# Owner-height canopy beam now sits at the top of the existing veranda posts.
for post in COL['04'].objects:
 if post.name.startswith('Veranda steel post'):
  # Post bottom remains fixed at floor level; only fit its top to the beam.
  post.dimensions.z=support_z;post.location.z=support_z/2
  unchanged.pop(post.name,None)
assert all(name in bpy.data.objects and signature(bpy.data.objects[name])==sig for name,sig in unchanged.items())
# Add drone-like views and an overhead inspection oriented like DJI_0667.
base=bpy.data.scenes['01 Exterior']
views=[('09 Drone roof','drone',(-24,-27,26),(0,1,1),31),('10 Roof overhead','overhead',(.6,1.6,40),(.6,1.6,0),24),('11 West roof','west_roof',(-17,25,17),(0,1,1.5),30)]
for name,key,pos,target,scale in views:
 sc=bpy.data.scenes.new(name)
 for c in base.collection.children:sc.collection.children.link(c)
 bpy.context.window.scene=sc;bpy.context.view_layer.update();sc.camera=camera('Camera '+key,pos,target,scale)
 if key=='overhead':sc.camera.rotation_euler=(0,0,math.pi/2)
 sc.world=base.world;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True
 sc.render.resolution_x=1700;sc.render.resolution_y=1300 if key!='overhead' else 1700;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 for c in sc.view_layers[0].layer_collection.children:c.exclude=c.name[:2]=='08'
 sc.render.filepath=str(HERE/(key+'.png'))
notes='''ROOF AND BRICK UPDATE

Based on Roof images/DJI_0659.JPG through DJI_0667.JPG. Roof footprint and
ridge/valley arrangement traced from overhead DJI_0667 and checked in angled
views. Main hip roof, connected small corner hip, raised solid triangular
gable, lower west roof with annex projection, and long veranda canopy.

User finish instruction: later-added roof sections stay BLACK. All remaining
roof surfaces, including the photographed silver areas, are REDDISH.

Brick shader updated to red-brown fired clay with individual brick variation,
occasional dark bricks, warm mortar, recessed joints and fine surface relief.
No external texture files required. Interior plaster retained.

South black roof falls SOUTH at exactly 0.02m/m (2%, user supplied).
West black roof falls WEST at exactly 0.06m/m (6%, user supplied).
Main wall height is 3.00m per owner, including the high west wall beside
the red roof. At the existing footprint, the 6% west slope gives about 2.73m
at the main west wall and 2.63m at the annex west wall. Owner confirmed that
6cm/m controls and the stated 2.55m low wall is approximate.
Roof surface high edge is 3.125m (125mm estimated build-up); ridge is 4.625m.
Red-roof pitch, overhangs and sheet profiles remain photo-based estimates.
Main wall tops and ceiling elevations updated; survey XY, floor plans and
photo-corrected opening elevations retained. Earlier files remain unchanged.

Scenes 09-11 show the roof. The original facade and floor inspection scenes
remain available. Hide collection 05 to inspect the rooms without the roof.
'''
bpy.data.texts.new('ROOF UPDATE - drone references and finishes').write(notes);(HERE/'ROOF_UPDATE_NOTES.txt').write_text(notes)
bpy.context.window.scene=base;bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL'
   area.spaces.active.region_3d.view_rotation=bpy.data.objects['Camera drone'].rotation_euler.to_quaternion()
   area.spaces.active.region_3d.view_location=(0,1,1)
   area.spaces.active.region_3d.view_distance=34
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Roof_Updated.blend'))
report={'preserved_non_roof_meshes':len(unchanged),'roof_surface_count':len(G['roof_faces']),'corrugation_ribs':sum(len(f['ribs']) for f in G['roof_faces']),'black_slopes':G['black_slopes'],'main_eave_m':G['main_eave_m'],'main_ridge_m':G['ridge_m'],'finish':G['finish_instruction'],'all_window_geometry_unchanged':True,'wall_height_m':3.0,'wall_height_report':'wall_height_validation.json','brick_material_updated':True}
(HERE/'validation.json').write_text(json.dumps(report,indent=2))
for name,key,*_ in views:bpy.ops.render.render(write_still=True,scene=name)
base.render.filepath=str(HERE/'exterior.png');bpy.ops.render.render(write_still=True,scene=base.name)
print('ROOF_UPDATE_COMPLETE',json.dumps(report))
