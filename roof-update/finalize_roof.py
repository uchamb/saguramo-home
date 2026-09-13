import bpy,ast,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;G=json.loads((P/'roof_geometry.json').read_text());COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
for path,names in [(P.parent/'build_house.py',['move','box','beam']),(P/'update_roof.py',['inside'])]:
 for node in ast.parse(path.read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'))
for o in list(COL['05'].objects):
 if o.name.startswith('ROOF | black perimeter fascia'):bpy.data.objects.remove(o,do_unlink=True)
black=bpy.data.materials['Roof | new black coated metal']
for ring in G['outline']:
 for a,b in zip(ring,ring[1:]):
  if math.dist(a,b)<.04:continue
  mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
  choices=[f for f in G['roof_faces'] if f['structural'] and any(inside(mid,t) for t in f['triangles'])]
  f=min(choices,key=lambda f:f['plane'][0]*mid[0]+f['plane'][1]*mid[1]+f['plane'][2]);aa,bb,c=f['plane']
  beam('ROOF | black perimeter fascia',(*a,aa*a[0]+bb*a[1]+c-.07),(*b,aa*b[0]+bb*b[1]+c-.07),.14,black,'05')
for o in COL['05'].objects:
 if 'basis' in o:o['basis']=G['assumptions']
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_rotation=bpy.data.objects['Camera drone'].rotation_euler.to_quaternion();area.spaces.active.region_3d.view_location=(0,1,1);area.spaces.active.region_3d.view_distance=34
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
for scene,file in [('09 Drone roof','drone'),('11 West roof','west_roof'),('01 Exterior','exterior'),('10 Roof overhead','overhead')]:
 sc=bpy.data.scenes[scene];sc.render.filepath=str(P/(file+'.png'));bpy.ops.render.render(write_still=True,scene=scene)
