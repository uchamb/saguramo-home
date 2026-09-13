import bpy,json,hashlib,math,bmesh
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;R=json.loads((P/'build_validation.json').read_text())
def gs(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
def sig(o):return hashlib.sha256((gs(o)+repr([m.name for m in o.data.materials])).encode()).hexdigest()
for name,expected in R['unchanged_mesh_signatures'].items():assert name in bpy.data.objects and sig(bpy.data.objects[name])==expected,name
for name,expected in R['floor_geometry_signatures'].items():assert gs(bpy.data.objects[name])==expected,name
assert len(R['columns'])==2
roof=json.loads((P.parent/'roof-update/roof_geometry.json').read_text());f=next(f for f in roof['roof_faces'] if f['name']=='Dark west roof and annex');a,b,c=f['plane']
for col in R['columns']:
 ob=bpy.data.objects[col['name']];assert abs(math.dist(ob.location.xy,col['wall_xy'])-1)<1e-5
 assert ob.dimensions.z>2.5 and abs(ob.dimensions.x-.085)<1e-5 and abs(ob.dimensions.y-.085)<1e-5
 for v in ob.data.vertices:
  if v.co.z>0:
   w=ob.matrix_world@v.co;assert abs(w.z-(a*w.x+b*w.y+c-.085))<1e-5,(ob.name,list(w))
# Both rails of the first bay touch the existing column face exactly.
column=bpy.data.objects[R['railings'][0]['existing_column']];column_face=column.location.x+column.dimensions.x/2
for suffix in ['top handrail','bottom rail']:
 ob=bpy.data.objects['DETAIL | Basement railing | Terrace 1 side | bay 0 '+suffix]
 lo=min((ob.matrix_world@v.co).x for v in ob.data.vertices)
 assert abs(lo-column_face)<1e-5,(suffix,lo,column_face)
 assert abs(ob.location.y-column.location.y)<1e-5
solids=0
for name in R['new_railing_objects']:
 ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges),name;bm.free();solids+=1
 assert all(math.isfinite(x) for v in ob.data.vertices for x in v.co)
material=bpy.data.materials[R['tile_material']]
brick=next(n for n in material.node_tree.nodes if n.type=='TEX_BRICK')
assert brick.offset==0 and abs(brick.inputs['Brick Width'].default_value-.5)<1e-6 and abs(brick.inputs['Row Height'].default_value-.5)<1e-6
assert sum(n.type=='BUMP' for n in material.node_tree.nodes)==2
assert any(n.type=='TEX_WHITE_NOISE' for n in material.node_tree.nodes)
assert not any(n.type=='TEX_IMAGE' for n in material.node_tree.nodes)
for name in R['tile_targets']:assert bpy.data.objects[name].data.materials[0]==material
assert len(bpy.data.scenes)==14
report={'saved_model_reopened':True,'unrelated_meshes_preserved':len(R['unchanged_mesh_signatures']),'floor_meshes_unchanged':len(R['floor_geometry_signatures']),'full_height_columns_added':2,'column_distance_from_bathroom2_m':1,'column_tops_fit_roof_soffit':True,'terrace_railing_connected_to_existing_column':True,'closed_new_railing_meshes':solids,'procedural_square_tile_material_verified':True,'tile_size_estimate_m':.5,'tile_targets':R['tile_targets'],'childroom_door_roof_and_stairs_preserved':True,'scene_count':14}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('TERRACE_VERIFIED',json.dumps(report))
