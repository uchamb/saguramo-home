"""Eight perspective PNGs; run in Blender with the current concept loaded.
The source .blend is never saved or modified. Camera heights use the outdoor
parcel surface as their zero datum, rather than the raised first-floor slab.
"""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;OUT=P.parent.parent
source=Path(bpy.data.filepath);source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
base=bpy.data.scenes['18 Mansard concept']
ground=bpy.data.objects['Parcel | surveyed boundary; flat grade assumption']
ground_z=max((ground.matrix_world@v.co).z for v in ground.data.vertices)
# Fit every visible house part above the outdoor surface, including the stair.
points=[]
for col in base.collection.children:
 if col.name[:2] not in ['01','02','03','04','05','06','10','11','12','13']:continue
 for ob in col.objects:
  if ob.type!='MESH' or ob.hide_render:continue
  points.extend(ob.matrix_world@Vector(c) for c in ob.bound_box if (ob.matrix_world@Vector(c)).z>=ground_z-.05)
lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
target=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,(ground_z+hi.z)/2))
directions=[('south-east','Southeast corner',(-1,-1)),('south-west','Southwest corner',(-1,1)),('south','South side',(-1,0)),('west','West side',(0,1))]
views=[]
for key,title,(dx,dy) in directions:
 pair=[];length=math.hypot(dx,dy);distance=32
 for height in [2,10]:
  sc=bpy.data.scenes.new(f'Render | {title} | {height}m above ground')
  for c in base.collection.children:sc.collection.children.link(c)
  sc.world=base.world;sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True
  sc.render.resolution_x=1920;sc.render.resolution_y=1440;sc.render.resolution_percentage=100
  sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.view_settings.view_transform='AgX'
  sc.unit_settings.system='METRIC'
  data=bpy.data.cameras.new(f'View {key} {height}m');data.type='PERSP';data.lens=50;data.sensor_width=36;data.clip_start=.1;data.clip_end=500
  cam=bpy.data.objects.new(data.name,data);sc.collection.objects.link(cam)
  cam.location=(target.x+distance*dx/length,target.y+distance*dy/length,ground_z+height)
  cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
  bpy.context.window.scene=sc;bpy.context.view_layer.update()
  for lc in sc.view_layers[0].layer_collection.children:lc.exclude=lc.name[:2]=='08'
  coords=[world_to_camera_view(sc,cam,p) for p in points]
  mx=max(abs(p.x-.5) for p in coords);my=max(abs(p.y-.5) for p in coords)
  fit=50*min(.425/mx,.405/my)
  pair.append((sc,cam,height,fit))
 # Identical focal length and XY within each height pair.
 lens=min(p[3] for p in pair)
 for sc,cam,height,_ in pair:
  cam.data.lens=lens;folder=P/f'{height:02d}m';folder.mkdir(exist_ok=True)
  path=folder/(key+'.png');sc.render.filepath=str(path)
  assert abs(cam.location.z-ground_z-height)<1e-6
  coords=[world_to_camera_view(sc,cam,p) for p in points]
  bounds=[min(p.x for p in coords),min(p.y for p in coords),max(p.x for p in coords),max(p.y for p in coords)]
  assert bounds[0]>.06 and bounds[1]>.06 and bounds[2]<.94 and bounds[3]<.94,(key,height,bounds)
  views.append({'side':key,'title':title,'height_above_ground_m':height,'camera_location_m':list(cam.location),'look_at_m':list(target),'lens_mm':lens,'projection':'perspective','scene':sc.name,'file':str(path.relative_to(P)),'resolution':[1920,1440],'projected_house_bounds':bounds})
report={'source_model':source.name,'source_model_sha256':source_hash,'ground_datum_m':ground_z,'ground_datum_basis':'Top surface of the existing flat surveyed parcel mesh; first-floor slab is at model Z=0.','same_xy_and_lens_within_height_pairs':True,'source_model_saved_or_modified':False,'views':views}
(P/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
# Complete all low views first, then the corresponding high views.
for v in sorted(views,key=lambda x:x['height_above_ground_m']):
 print('RENDER_START',v['side'],v['height_above_ground_m'],flush=True)
 bpy.ops.render.render(write_still=True,scene=v['scene'])
 print('RENDER_DONE',v['file'],flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print('ALL_EIGHT_RENDERS_COMPLETE; SOURCE_MODEL_UNCHANGED',flush=True)
