"""Run: blender --background --python build_house.py. Uses survey_geometry.json."""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
OUT=Path(__file__).resolve().parent
D=json.loads((OUT/'survey_geometry.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='01 Exterior'
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='METERS'
COL={}
for name in ['01 Main walls','02 Floors and terraces','03 Windows and doors','04 Veranda and stairs','05 Roof - estimated','06 Basement','07 Site - schematic grade','08 Survey labels','09 Lighting and cameras']:
 c=bpy.data.collections.new(name);scene.collection.children.link(c);COL[name[:2]]=c

def move(obj,c):
 for col in list(obj.users_collection): col.objects.unlink(obj)
 COL[c].objects.link(obj)
 return obj

def mat(name,color,rough=.6,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
brick=mat('Brick | photo-matched terracotta',(.44,.155,.066))
# Explicit wall UVs in metres keep brick courses vertical and correctly sized.
n=brick.node_tree.nodes;l=brick.node_tree.links
uv=n.new('ShaderNodeTexCoord');b=n.new('ShaderNodeTexBrick');l.new(uv.outputs['UV'],b.inputs['Vector'])
b.inputs['Color1'].default_value=(.40,.105,.035,1);b.inputs['Color2'].default_value=(.66,.245,.096,1);b.inputs['Mortar'].default_value=(.28,.20,.135,1)
b.inputs['Scale'].default_value=1;b.inputs['Mortar Size'].default_value=.007;b.inputs['Mortar Smooth'].default_value=.003;b.inputs['Brick Width'].default_value=.255;b.inputs['Row Height'].default_value=.072
l.new(b.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.008;l.new(b.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])
plaster=mat('Warm interior plaster',(.76,.735,.66));floor=mat('Warm stone floors',(.56,.50,.40));tile=mat('Veranda stone | photo estimate',(.45,.36,.265));concrete=mat('Exposed concrete',(.36,.365,.34));metal=mat('Dark powder-coated frames',(.033,.042,.047),.28,.65);roofmat=mat('Charcoal metal roof',(.075,.09,.094),.38,.7);wood=mat('Timber soffit',(.58,.37,.16));glass=mat('Smoky glazing',(.12,.22,.26),.16,.15)
glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.55
glass.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.45
grass=mat('Muted terrain',(.255,.29,.18));edge=mat('Survey boundary | ochre',(.75,.44,.13));white=mat('Annotation charcoal',(.035,.046,.046));doorwood=mat('Interior door oak',(.37,.24,.135));groundmat=mat('Studio ground',(.74,.735,.70))
# Subtle mottling on natural surfaces.
for m,scale in [(tile,4),(concrete,8),(grass,1.1),(floor,7)]:
 n=m.node_tree.nodes;l=m.node_tree.links;noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.018;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],n.get('Principled BSDF').inputs['Normal'])

def meshobj(name,verts,faces,material,col,uvs=None):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);COL[col].objects.link(obj);obj.data.materials.append(material)
 if uvs:
  layer=mesh.uv_layers.new(name='Metres')
  for p,coords in zip(mesh.polygons,uvs):
   for idx,uv in zip(p.loop_indices,coords):layer.data[idx].uv=uv
 return obj

def prism(name,g,z0,z1,material,col,record=None):
 if 'parts' in g:
  return [prism(name+f' {i}',p,z0,z1,material,col,record) for i,p in enumerate(g['parts'])]
 if g.get('area',1)<1e-8:return None
 verts=[];faces=[];uvs=[];interior_faces=[]
 def face(coords,uv):
  idx=len(verts);verts.extend(coords);faces.append(tuple(range(idx,idx+len(coords))));uvs.append(uv)
 for tri in g['triangles']:
  # Triangles from Shapely are CCW; make orientation explicit.
  a,b,c=tri
  if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0:tri=list(reversed(tri))
  face([(x,y,z0) for x,y in reversed(tri)],list(reversed(tri)))
  face([(x,y,z1) for x,y in tri],tri)
 for ri,ring in enumerate(g['rings']):
  ring=ring[:-1]
  area=sum(ring[i][0]*ring[(i+1)%len(ring)][1]-ring[(i+1)%len(ring)][0]*ring[i][1] for i in range(len(ring)))
  if (area>0)!=(ri==0):ring=list(reversed(ring))
  for a,b in zip(ring,ring[1:]+ring[:1]):
   mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
   if col=='01' and any(math.dist(mid,m)<.001 for m in g.get('interior_midpoints',[])):interior_faces.append(len(faces))
   length=math.dist(a,b);face([(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)],[(0,z0),(length,z0),(length,z1),(0,z1)])
 obj=meshobj(name,verts,faces,material,col,uvs)
 if interior_faces:
  obj.data.materials.append(plaster)
  for idx in interior_faces:obj.data.polygons[idx].material_index=1
 # Weld vertices for an editable, connected solid.
 import bmesh
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
 if record:
  obj['source']='shp sartuli/unit_polygon.shp' if col!='06' else 'shp sardafi/unit_polygon.shp';obj['survey_record']=record['id'];obj['survey_type']=record['type'];obj['survey_area_m2']=record['survey_area'];obj['accuracy']='Survey XY; measured ceiling height; vertical opening dimensions estimated'
 return obj

def box(name,loc,size,material,col):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=move(bpy.context.object,col);o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 return o

def beam(name,a,b,width,material,col):
 mid=(Vector(a)+Vector(b))/2;o=box(name,mid,(width,width,(Vector(b)-Vector(a)).length),material,col);o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler();return o

def label(name,text,xy,z,size=.3,col='08'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.0005
 o=bpy.data.objects.new(name,cu);COL[col].objects.link(o);o.location=(*xy,z);cu.materials.append(white);return o

# Source geometry, exactly transformed from UTM to local metre coordinates.
main=D['levels']['main'];base=D['levels']['basement'];ZBASE=-2.74
prism('Main structural slab | 220mm assumption',D['levels']['main_slab'],-.22,-.035,concrete,'02')
prism('Basement structural slab | 180mm assumption',D['levels']['basement_slab'],ZBASE-.18,ZBASE-.035,concrete,'06')
for level,records,z,h,col in [('main',main,0,2.90,'01'),('basement',base,ZBASE,2.52,'06')]:
 for r in records:
  g=r['geometry'];t=r['type'];name=f'{level.upper()} {r["id"]:02d} | {t}'
  if t=='kedeli':
   if 'guard_geometry' in r:
    prism(name+' low stair enclosure | height estimated',r['guard_geometry'],z,z+.95,brick,col,r)
    prism(name,r['full_height_geometry'],z,z+h,brick,col,r)
   else:prism(name,g,z,z+h,brick if level=='main' else concrete,col,r)
  elif t in ['iataki','veranda','terasa']:
   prism(name+f' | {r["survey_area"]:.2f} m2',g,z-.035,z,tile if t!='iataki' else floor,'02' if level=='main' else '06',r)
   if t=='iataki':label(name+' area',f'{r["survey_area"]:.2f} m²',r['center'],z+.015,.27 if r['survey_area']>6 else .15)
  elif t in ['fanjara','karebi']:
   x0,y0,x1,y1=r['bounds'];cx,cy=r['center'];alongx=(x1-x0)>(y1-y0);width=max(x1-x0,y1-y0);depth=min(x1-x0,y1-y0)
   iswin=t=='fanjara';sill=.85 if iswin else 0;head=2.2
   if level=='basement':head=2.05
   if iswin and r['id']==11:sill=1.35;head=2.25
   # Large glazed doors have their widths fixed by the survey.
   extdoor=(level=='main' and r['id'] in [32,34,35,36,37,38,39])
   isglazed=iswin or (extdoor and width>1.5)
   mc='03' if level=='main' else '06'
   if sill:prism(name+' sill wall',g,z,z+sill,brick,col,r)
   prism(name+' lintel',g,z+head,z+h,brick if level=='main' else concrete,col,r)
   def inset(n,a0,a1,h0,h1,dep,ma):
    loc=(cx+(a0+a1)/2,cy,z+(h0+h1)/2) if alongx else (cx,cy+(a0+a1)/2,z+(h0+h1)/2)
    sz=(a1-a0,dep,h1-h0) if alongx else (dep,a1-a0,h1-h0)
    return box(name+' '+n,loc,sz,ma,mc)
   f=.055
   for a in [-width/2+f/2,width/2-f/2]:inset('jamb',a-f/2,a+f/2,sill,head,.085,metal)
   for hz in [sill+f/2,head-f/2]:inset('rail',-width/2,width/2,hz-f/2,hz+f/2,.085,metal)
   if isglazed:
    inset('glass',-width/2+f,width/2-f,sill+f,head-f,.018,glass)
    divisions=max(1,round(width/.8))
    for k in range(1,divisions):
     a=-width/2+width*k/divisions;inset('mullion',a-.022,a+.022,sill,head,.075,metal)
   elif extdoor or level=='basement':inset('door leaf',-width/2+f,width/2-f,.035,head-f,.045,metal)
   else:
    # Interior leaves kept open to make room circulation visible.
    leaf=inset('open interior leaf',-width/2+f,width/2-f,.035,head-f,.037,doorwood)
    angle=math.radians(65)
    hinge=Vector((cx-width/2+f,cy,leaf.location.z)) if alongx else Vector((cx,cy-width/2+f,leaf.location.z))
    delta=leaf.location-hinge;leaf.location=hinge+Vector((delta.x*math.cos(angle)-delta.y*math.sin(angle),delta.x*math.sin(angle)+delta.y*math.cos(angle),0))
    leaf.rotation_euler.z=angle;leaf['assumption']='Door swing not documented; shown open for inspection'
   prism(name+' threshold',g,z-.025,z+.005,floor,'02' if level=='main' else '06')
# Main plinth below occupied area; basement remains physically below it.
# Restrict skirt to exterior survey slab rings and stop short of stair opening.
for g in D['levels']['main_slab'].get('parts',[D['levels']['main_slab']]):
 ring=g['rings'][0]
 for a,b in zip(ring,ring[1:]):
  o=box('Platform concrete skirt',((a[0]+b[0])/2,(a[1]+b[1])/2,-.48),(math.dist(a,b),.12,.52),concrete,'02');o.rotation_euler.z=math.atan2(b[1]-a[1],b[0]-a[0])
# Long veranda entrance stair, surveyed plan footprint; 0.72m grade drop assumed.
for k in range(4):
 x0=-7.899+k*.37;box(f'Veranda entry step {k+1}',((x0-6.419)/2,5.073,-.72+(k+1)*.18/2),(-6.419-x0,7.91,(k+1)*.18),tile,'04')
box('Basement upper landing | grade estimate',(-7.344,9.879,-.82),(1.11,1.70,.2),concrete,'04')
for k in range(12):
 x0=-6.789+k*(3.98/12);top=-.72-(k+1)*(2.02/12)
 box(f'Basement descending tread {k+1}',(x0+3.98/24,9.779,(top+ZBASE-.12)/2),(3.98/12,1.50,top-ZBASE+.12),concrete,'06')
# Steel posts, wood fascia and soffit observed in photographs; spacing is approximate.
for y in [-3.2,-.2,2.9,5.9,8.7]:
 beam('Veranda steel post | photo estimate',(-6.25,y,0),(-6.25,y,2.94),.085,metal,'04')
beam('Veranda edge beam',(-6.25,-3.6,2.94),(-6.25,9.15,2.94),.16,metal,'05')
# Roof panels: shallow main mono-pitch and lower veranda cover, independently editable.
def roofpanel(name,x0,x1,y0,y1,zfun):
 corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
 vs=[(x,y,zfun(x,y)) for x,y in corners]+[(x,y,zfun(x,y)+.16) for x,y in corners]
 o=meshobj(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],roofmat,'05');o['accuracy']='Estimated roof pitch, perimeter and build-up from exterior photographs; no roof survey'
 # Timber underside sits within panel build-up.
 meshobj(name+' timber soffit',[(x,y,zfun(x,y)-.006) for x,y in corners],[(0,3,2,1)],wood,'05')
 for a,b in zip(corners,corners[1:]+corners[:1]):beam(name+' fascia',(*a,zfun(*a)+.065),(*b,zfun(*b)+.065),.15,wood,'05')
 # Thin standing seams.
 x=x0+.35
 while x<x1:
  beam(name+' roof seam',(x,y0,zfun(x,y0)+.176),(x,y1,zfun(x,y1)+.176),.016,roofmat,'05');x+=.55
roofpanel('Main roof | estimated 3 percent slope',-4.43,8.58,-7.95,9.60,lambda x,y:3.03+.03*(y+7.95))
roofpanel('Rear annex roof | estimated',-3.12,-.25,9.60,11.28,lambda x,y:3.03+.03*(y+7.95))
roofpanel('Veranda canopy | estimated',-6.92,-4.28,-3.64,9.24,lambda x,y:2.93+.015*(x+6.92))
roofpanel('Small west room roof | estimated',-6.85,-4.43,-7.95,-3.40,lambda x,y:3.03+.03*(y+7.95))
# Close the wall-to-roof zone; ceiling remains at its measured 2.90m height.
for r in main:
 if r['type'] in ['kedeli','fanjara','karebi']:
  g=r.get('full_height_geometry',r['geometry'])
  o=prism(f'Roof infill above survey wall {r["id"]}',g,2.9,3.8,brick,'05')
  for obj in (o if isinstance(o,list) else [o]):
   if obj:
    for v in obj.data.vertices:
     if v.co.z>3.7:v.co.z=3.03+.03*(v.co.y+7.95)
 if r['type']=='iataki':prism('Ceiling | measured underside 2.90m',r['geometry'],2.90,2.98,plaster,'05')
# Terrain is flat at assumed grade; a survey boundary is a line, not an invented fence.
prism('Parcel | surveyed boundary; flat grade assumption',D['site']['terrain'],-1.00,-.74,grass,'07')
for ring in D['site']['nakveti']['rings']:
 for a,b in zip(ring,ring[1:]):beam('Cadastral boundary',(*a,-.725),(*b,-.725),.045,edge,'07')
# Easement shown only as a surveyed overlay; no fabricated driveway.
prism('Surveyed easement overlay',D['site']['valdebuleba'],-.742,-.736,tile,'07')
box('Studio ground',(0,0,-1.06),(200,200,.1),groundmat,'07')
# Small north arrow uses the UTM-to-model transform.
x,y=-11,-10;north=Vector((D['local_x_utm'][1],D['local_y_utm'][1],0))
a=Vector((x,y,-.70));b=a+north*2.0;beam('True grid north arrow',a,b,.055,white,'07')
for sign in [-1,1]:
 v=-north*.45+Vector((-north.y,north.x,0))*.23*sign;beam('North arrow head',b,b+v,.055,white,'07')
label('Grid north','N',(b.x,b.y+.45),-.69,.5,'07')
# Lighting and named cameras shared across inspection scenes.
world=bpy.data.worlds.new('Soft daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.80,.88,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;scene.world=world
bpy.ops.object.light_add(type='AREA',location=(-10,-8,20));light=move(bpy.context.object,'09');light.name='Large soft key';light.data.energy=2700;light.data.shape='DISK';light.data.size=12
bpy.ops.object.light_add(type='SUN',location=(0,0,20));sun=move(bpy.context.object,'09');sun.name='Afternoon sun';sun.rotation_euler=(math.radians(28),math.radians(-25),math.radians(-35));sun.data.energy=2.1;sun.data.angle=math.radians(12)
def camera(name,pos,target,scale):
 bpy.ops.object.camera_add(location=pos);o=move(bpy.context.object,'09');o.name=name;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=scale;o.data.lens=45;return o
cams={
 'exterior':camera('Camera exterior',(-27,-31,20),(0,1,1),31),
 'interior':camera('Camera roofless',(-23,-28,38),(0,1,0),31),
 'basement':camera('Camera basement',(-16,-12,17),(0,8,-1.8),21),
 'site':camera('Camera site',(-35,-30,58),(0,-6,0),56),
 'plan':camera('Camera plan',(0,.3,45),(0,.3,0),24)}
scene.camera=cams['exterior']
def configure(sc,hidden):
 bpy.context.window.scene=sc
 bpy.context.view_layer.update()
 sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
 sc.render.resolution_x=1600;sc.render.resolution_y=1200;sc.render.resolution_percentage=100
 sc.world=world;sc.render.image_settings.file_format='PNG';sc.view_settings.view_transform='AgX'
 for c in sc.view_layers[0].layer_collection.children:c.exclude=c.name[:2] in hidden
 sc.unit_settings.system='METRIC'
configure(scene,['08'])
scenes={'exterior':scene}
for name,key,hidden in [('02 Roofless interior','interior',['05','08']),('03 Basement inspection','basement',['01','02','03','04','05','07','08']),('04 Survey site','site',['08']),('05 Measured floor plan','plan',['05','07','06'])]:
 sc=bpy.data.scenes.new(name)
 for c in COL.values():sc.collection.children.link(c)
 sc.camera=cams[key];configure(sc,hidden);scenes[key]=sc
 if key=='plan':sc.render.resolution_x=1200;sc.render.resolution_y=1600
# Basement labels only in basement scene; main labels only in plan scene.
# Keep annotations floor-plan only to avoid labels from another level shining through.
for o in COL['08'].objects:
 if o.name.startswith('BASEMENT'):o.hide_render=True
# Useful startup viewport and embedded documentation.
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for area in scr.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=32;area.spaces.active.region_3d.view_location=(0,1,0);area.spaces.active.clip_end=1000
   area.spaces.active.region_3d.view_rotation=cams['exterior'].rotation_euler.to_quaternion();area.spaces.active.shading.color_type='MATERIAL'
readme='''SAGURAMO HOUSE - SURVEY-BASED MODEL

Scenes: 01 Exterior; 02 Roofless interior; 03 Basement inspection;
04 Survey site; 05 Measured floor plan. Use the Scene selector at the top.
Metric units: 1 Blender unit = 1 metre. Main finished floor Z = 0.

SOURCE: room, wall, opening, terrace and basement polygons from the supplied
shp sartuli and shp sardafi unit_polygon files. Parcel and easement from shp.
Ceiling heights: 2.90 m main, 2.52 m basement. Floor plans checked visually
against pages 2 and 4 of the measured PDF. Geometry is survey XY without
simplifying room outlines. Survey record IDs are stored on source meshes.

ASSUMPTIONS: main structural slab 0.22 m; basement floor Z=-2.74 m;
flat surrounding grade Z=-0.74 m; roof shape, pitches, overhangs and buildup;
stair enclosure height 0.95m; warm plaster on inferred interior wall faces;
window sill/head heights (usually 0.85/2.20m), door heads 2.20m;
frame profiles, glazing divisions, open door swings, posts and stair rises.
Brick, wood soffit and dark metal appearance estimated from shp/001-003.jpg.
Room uses are not assigned. Interiors are unfurnished. No structural design.
Photos and survey date from February/March 2025; later alterations unknown.

Roofs are isolated in collection 05 and removable for editing.
Site is flat because supplied survey has no elevation field. Terrain in the
exterior scene hides underground geometry; use Basement inspection to view it.

Coordinate metadata and reproducible source scripts accompany this file.
'''
bpy.data.texts.new('START HERE - sources and assumptions').write(readme)
(OUT/'MODEL_NOTES.txt').write_text(readme)
scene['source_crs']=D['crs'];scene['origin_utm']=D['origin_utm'];scene['local_x_utm']=D['local_x_utm'];scene['local_y_utm']=D['local_y_utm']
scene['main_floor_z_m']=0;scene['basement_floor_z_m']=ZBASE
# Save the complete native file before rendering.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House.blend'))
for key in ['exterior','interior','basement','plan']:
 sc=scenes[key];sc.render.filepath=str(OUT/f'{key}.png');bpy.ops.render.render(write_still=True,scene=sc.name)
# Validate reopened-file friendly object counts and source dimensions.
report={'blender':bpy.app.version_string,'objects':len(bpy.data.objects),'mesh_objects':sum(o.type=='MESH' for o in bpy.data.objects),'scenes':list(bpy.data.scenes.keys()),'main_rooms_and_veranda_area_m2':sum(r['survey_area'] for r in main if r['type'] in ['iataki','veranda']),'terrace_area_m2':main[1]['survey_area'],'main_total_including_terrace_m2':sum(r['survey_area'] for r in main if r['type'] in ['iataki','veranda','terasa']),'basement_usable_area_m2':sum(r['survey_area'] for r in base if r['type']=='iataki'),'ceiling_heights_m':[2.90,2.52],'coordinate_origin_utm':D['origin_utm']}
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print('MODEL_COMPLETE',json.dumps(report))
