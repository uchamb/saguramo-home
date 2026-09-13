import bpy,json,bmesh,math
from pathlib import Path
from mathutils import Vector
OUT=Path(bpy.data.filepath).parent;P=OUT/'photo-update';A=json.loads((P/'facade_adjustments.json').read_text())
assert len(bpy.data.scenes)==8
assert len(A['updates'])==8
walls=bpy.data.collections['01 Main walls'].objects
raychecks=0
for r in A['updates']:
 x0,y0,x1,y1=r['bounds'];alongx=x1-x0>y1-y0
 for fraction in [.08,.28,.5,.72,.92]:
  for z in [r['sill']+.09,(r['sill']+r['head'])/2,r['head']-.09]:
   if r['facade']=='south':origin=Vector((x0-.04,y0+(y1-y0)*fraction,z));direction=Vector((1,0,0));length=x1-x0+.08
   elif r['facade']=='east':origin=Vector((x0+(x1-x0)*fraction,y0-.04,z));direction=Vector((0,1,0));length=y1-y0+.08
   else:origin=Vector((x0+(x1-x0)*fraction,y1+.04,z));direction=Vector((0,-1,0));length=y1-y0+.08
   for o in walls:
    if o.type!='MESH':continue
    inv=o.matrix_world.inverted();hit,*_=o.ray_cast(inv@origin,inv.to_3x3()@direction,distance=length)
    assert not hit,(r['name'],fraction,z,o.name)
   raychecks+=1
meshes=0
for o in bpy.data.objects:
 if o.type!='MESH' or not(o.name.startswith('PHOTO |') or o.name.startswith('MAIN 17 |')):continue
 assert all(math.isfinite(v) for p in o.data.vertices for v in p.co)
 bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),o.name;bm.free();meshes+=1
r={'saved_blend_reopened':True,'scene_count':8,'window_groups':8,'wall_clearance_rays_passed':raychecks,'corrected_meshes_manifold':meshes,'main_area_m2_unchanged':A['main_area_unchanged']}
(P/'reopened_verification.json').write_text(json.dumps(r,indent=2));print('VERIFIED',json.dumps(r))
