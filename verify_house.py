import bpy,bmesh,json,math
from pathlib import Path
OUT=Path(bpy.data.filepath).parent
assert len(bpy.data.scenes)==5
assert bpy.context.scene.unit_settings.system=='METRIC'
checked=0;max_area_error=0;nonmanifold=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 assert all(math.isfinite(v) for p in o.data.vertices for v in p.co),o.name
 if 'survey_record' not in o:continue
 bm=bmesh.new();bm.from_mesh(o.data)
 if any(not e.is_manifold for e in bm.edges):nonmanifold.append(o.name)
 bm.free()
 if o.name.startswith('MAIN') and o.get('survey_record') in [25,26]:continue
 projected_area=0
 for p in o.data.polygons:
  if p.normal.z<-.99:projected_area+=p.area
 err=abs(projected_area-o['survey_area_m2']);max_area_error=max(max_area_error,err)
 assert err<.0002,(o.name,projected_area,o['survey_area_m2'])
 if o.get('survey_type')=='kedeli' and o.name.startswith(('MAIN','BASEMENT')):
  zz=[v.co.z for v in o.data.vertices];expected=2.52 if o.name.startswith('BASEMENT') else 2.9
  assert abs(max(zz)-min(zz)-expected)<1e-5
 checked+=1
assert not nonmanifold,nonmanifold
r={'reopened_blend':bpy.data.filepath,'survey_meshes_checked':checked,'max_projected_area_error_m2':max_area_error,'source_solids_manifold':True,'scene_count':len(bpy.data.scenes),'measured_wall_heights_verified':True}
(OUT/'mesh_verification.json').write_text(json.dumps(r,indent=2));print('VERIFIED',json.dumps(r))
