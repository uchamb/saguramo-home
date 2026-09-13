"""Verify the reopened final model, preserving all baseline house/deck geometry."""
import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P.parent;G=json.loads((P/'mansard_geometry.json').read_text());R=json.loads((P/'build_validation.json').read_text());F=G['floor_level_m']
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world),[m.name if m else None for m in o.data.materials],[p.material_index for p in o.data.polygons])).encode()).hexdigest()
for name,s in R['preserved_mesh_signatures'].items():assert name in bpy.data.objects and sig(bpy.data.objects[name])==s,name
assert hashlib.sha256((OUT/'Saguramo_House_Roof_Updated.blend').read_bytes()).hexdigest()==R['existing_house_sha256']
for name in R['closed_solids']:
 bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);assert all(e.is_manifold for e in bm.edges),name;assert abs(bm.calc_volume())>1e-8,name;bm.free()
roof=bpy.data.collections['10 Mansard roof'];peak=max((o.matrix_world@v.co).z for o in roof.objects if o.type=='MESH' for v in o.data.vertices);assert abs(peak-F-5)<1e-6,(peak,F)
# Ray-test the real dormer cut-out: sheet must be the raised shed plane, not the
# old diagonal plane passing through the room. Also check the doorway in masonry.
room=G['south_room'];front,y0,back,y1=room['bounds_xy'];yc=(y0+y1)/2
for frac in [.1,.4,.8]:
 x=front+(back-front)*frac
 for spec in G['roof_planes']:
  o=bpy.data.objects['MANSARD | '+spec['name']];hit,loc,*_=o.ray_cast(Vector((x,yc,F)),Vector((0,0,1)))
  if spec['name']=='South shed dormer roof':
   assert hit;expected=sum([spec['plane'][0]*x,spec['plane'][1]*yc,spec['plane'][2]])-.06;assert abs(loc.z-expected)<1e-5
  else:assert not hit,(spec['name'],x)
for z in [F+.15,F+1.1,F+2.05]:
 for o in bpy.data.collections['12 Mansard south room'].objects:
  if o.type!='MESH' or not any(t in o.name for t in ['pier','header','cheek']):continue
  inv=o.matrix_world.inverted();hit,*_=o.ray_cast(inv@Vector((front-1,yc,z)),inv.to_3x3()@Vector((1,0,0)),distance=1.3);assert not hit,o.name
rails=bpy.data.collections['11 Upper terrace railings'];rail_top=max((o.matrix_world@v.co).z for o in rails.objects if o.type=='MESH' for v in o.data.vertices);assert abs(rail_top-F-1.1)<1e-6
assert len(R['guard_segments'])==len(G['railing_ring'])-1
assert all(bpy.data.scenes.get(name) for name in R['views'])
report={'saved_file_reopened':True,'ridge_height_above_wood_floor_m':peak-F,'ridge_absolute_m':peak,'floor_level_m':F,'preserved_existing_meshes':len(R['preserved_mesh_signatures']),'original_house_file_unchanged':True,'black_roofs_and_deck_unchanged':True,'closed_roof_room_solids':len(R['closed_solids']),'south_dormer_roof_cutout_verified':True,'doorway_clear_of_walls':True,'door_nominal_width_m':1,'door_height_m':2.2,'south_room_gross_area_m2':room['area_m2'],'uncovered_upper_terrace_area_m2':G['terrace_area_m2'],'railing_height_m':rail_top-F,'guarded_deck_perimeter_m':sum(s['length_m'] for s in R['guard_segments']),'railing_posts':R['railing_posts'],'preview_scenes':R['views']}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('MANSARD_VERIFIED',json.dumps(report))
