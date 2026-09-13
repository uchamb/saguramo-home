import bpy,json,hashlib,bmesh,math,itertools
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent;OUT=P.parent;R=json.loads((P/'build_validation.json').read_text());G=json.loads((P/'floor_geometry.json').read_text())
def gs(o,restore=None):
 verts=[tuple(v.co) for v in o.data.vertices]
 for i in restore or []:verts[i]=(verts[i][0],verts[i][1],3.0)
 return hashlib.sha256(repr((verts,[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
def sig(o):return hashlib.sha256((gs(o)+repr(([m.name for m in o.data.materials],[p.material_index for p in o.data.polygons]))).encode()).hexdigest()
assert hashlib.sha256((OUT/'Saguramo_House_Roof_Updated.blend').read_bytes()).hexdigest()==R['source_model_sha256']
for name,s in R['unchanged_mesh_signatures'].items():assert name in bpy.data.objects and sig(bpy.data.objects[name])==s,name
for name,s in R['wall_geometry_signatures'].items():
 o=bpy.data.objects[name];ids=R['wall_top_adjustments'].get(name,[])
 for i in ids:assert abs(o.data.vertices[i].co.z-2.999)<1e-6
 assert gs(o,ids)==s,name
for name in R['removed_roof_and_ceiling_objects']:assert name not in bpy.data.objects,name
assert not any(any(m and m.name=='Roof | reddish coated metal' for m in o.data.materials) for o in bpy.data.objects if o.type=='MESH')
floor=bpy.data.objects[R['floor_object']];bm=bmesh.new();bm.from_mesh(floor.data);assert all(e.is_manifold for e in bm.edges);bm.free()
assert abs(min(v.co.z for v in floor.data.vertices)-2.94)<1e-6
assert all(abs(v.co.z-3)<1e-6 or abs(v.co.z-2.94)<1e-6 for v in floor.data.vertices)
tops=[p for p in floor.data.polygons if p.normal.z>.99]
assert tops and all(all(abs(floor.data.vertices[i].co.z-3)<1e-6 for i in p.vertices) for p in tops)
area=sum(p.area for p in tops);assert abs(area-G['area_m2'])<.0001
assert all(floor.data.materials[p.material_index].name=='Second-floor concept | natural oak boards' for p in tops)
wood=bpy.data.materials['Second-floor concept | natural oak boards'];assert any(n.type=='TEX_BRICK' for n in wood.node_tree.nodes);assert any(n.type=='TEX_NOISE' for n in wood.node_tree.nodes)
slopes={}
for name,expect in [('Dark west roof and annex',(0,-.06)),('Dark south veranda canopy',(.02,0))]:
 o=bpy.data.objects['ROOF | '+name];points={}
 for v in o.data.vertices:
  xy=(round(v.co.x,6),round(v.co.y,6));points[xy]=max(points.get(xy,-1e6),v.co.z)
 for tri in itertools.combinations([(x,y,z) for (x,y),z in points.items()],3):
  mat=Matrix([(p[0],p[1],1) for p in tri])
  if abs(mat.determinant())>.01:break
 coeff=mat.inverted()@Vector([p[2] for p in tri]);assert abs(coeff.x-expect[0])<2e-6 and abs(coeff.y-expect[1])<2e-6
 slopes[name]=round(100*math.hypot(coeff.x,coeff.y),5)
assert len(bpy.data.scenes)==17
# The concept geometry has no volume above the requested 3m floor level.
assert max(v.co.z for v in floor.data.vertices)==3.0
report={'concept_file_reopened':True,'original_house_file_unchanged':True,'flat_floor_top_m':3.0,'floor_area_m2':area,'closed_floor_solid':True,'red_roof_geometry_removed':True,'black_roof_and_retained_trim_meshes_identical':len(R['protected_black_roof_objects']),'black_roof_slopes_percent':slopes,'unrelated_meshes_identical':len(R['unchanged_mesh_signatures']),'wall_xy_and_openings_preserved':True,'hidden_wall_top_clearance_m':.001,'wood_material_verified':True,'mansard_added':False,'scene_count':17}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('SECOND_FLOOR_VERIFIED',json.dumps(report))
