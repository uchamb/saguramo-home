import bpy,json,math,bmesh,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=json.loads((P/'final_build_validation.json').read_text())
def gs(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
def sig(o):return hashlib.sha256((gs(o)+repr([m.name for m in o.data.materials])).encode()).hexdigest()
for name,s in R['unchanged_mesh_signatures'].items():assert sig(bpy.data.objects[name])==s,name
for name,s in R['floor_geometry_signatures'].items():assert gs(bpy.data.objects[name])==s,name
for name in R['removed_low_post_objects']:assert name not in bpy.data.objects
columns={}
for side in ['east','west']:
 expected=R[side+'_full_height_columns'];y=bpy.data.objects[expected[0]].location.y
 found=[o.name for o in bpy.data.objects if o.type=='MESH' and abs(o.location.y-y)<.0001 and o.dimensions.z>2.5 and abs(o.dimensions.x-.085)<.0001 and abs(o.dimensions.y-.085)<.0001]
 assert set(found)==set(expected),(side,found,expected);columns[side]=found
 assert len(found)==2
col=bpy.data.objects[R['new_column']];a,b,c=R['roof_plane']
for v in col.data.vertices:
 if v.co.z>0:
  w=col.matrix_world@v.co;assert abs(w.z-(a*w.x+b*w.y+c-.085))<.00001
face=col.location.x+col.dimensions.x/2
for name in R['modified_rails']:
 o=bpy.data.objects[name];assert abs(min((o.matrix_world@v.co).x for v in o.data.vertices)-face)<.00001
 assert abs(o.location.y-col.location.y)<.00001
for name in [R['new_column'],R['new_base_plate'],*R['modified_rails']]:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),name;bm.free()
mat=bpy.data.materials[R['tile_material']]
for name in R['tile_targets']:assert bpy.data.objects[name].data.materials[0]==mat
assert bpy.data.objects['MAIN 00 | veranda | 44.98 m2'].data.materials[0]==bpy.data.objects['MAIN 01 | terasa | 52.93 m2'].data.materials[0]
assert any(n.type=='TEX_BRICK' for n in mat.node_tree.nodes)
assert len(bpy.data.scenes)==14
result={'saved_model_reopened':True,'east_full_height_column_count':2,'west_full_height_column_count':2,'east_railing_unchanged':True,'west_end_column_fits_roof_soffit':True,'west_rails_meet_column_face':True,'both_terraces_share_identical_material':True,'floor_meshes_unchanged':len(R['floor_geometry_signatures']),'unrelated_meshes_unchanged':len(R['unchanged_mesh_signatures']),'changed_and_new_column_rail_meshes_closed':4,'scene_count':14}
(P/'final_verification.json').write_text(json.dumps(result,indent=2)+'\n');print('FINAL_TERRACES_VERIFIED',json.dumps(result))
