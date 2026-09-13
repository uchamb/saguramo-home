import bpy,math,json,hashlib,bmesh,itertools
from pathlib import Path
from mathutils import Matrix,Vector
OUT=Path(bpy.data.filepath).parent;HERE=OUT/'roof-update';G=json.loads((HERE/'roof_geometry.json').read_text())
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
current={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
measured={}
for name,expected in [('Dark south veranda canopy',(.02,0)),('Dark west roof and annex',(0,-.06))]:
 o=bpy.data.objects['ROOF | '+name];tops={}
 for v in o.data.vertices:
  xy=(round(v.co.x,6),round(v.co.y,6));tops[xy]=max(tops.get(xy,-1e6),v.co.z)
 points=[(x,y,z) for (x,y),z in tops.items()]
 for pp in itertools.combinations(points,3):
  m=Matrix([(p[0],p[1],1) for p in pp])
  if abs(m.determinant())>.01:break
 plane=m.inverted()@Vector([p[2] for p in pp])
 assert abs(plane.x-expected[0])<2e-6 and abs(plane.y-expected[1])<2e-6,(name,list(plane))
 assert max(abs(plane.x*x+plane.y*y+plane.z-z) for x,y,z in points)<2e-5
 measured[name]={'dz_dx':plane.x,'dz_dy':plane.y,'slope_percent':100*math.hypot(plane.x,plane.y)}
solids=0
for f in G['roof_faces']:
 o=bpy.data.objects['ROOF | '+f['name']];bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),o.name;bm.free();solids+=1
 assert o.data.materials[0].name==('Roof | new black coated metal' if f['material']=='charcoal' else 'Roof | reddish coated metal')
assert len(bpy.data.scenes)==11
assert all(math.isfinite(c) for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
brick=bpy.data.materials['Brick | photo-matched terracotta'];assert any(n.type=='TEX_BRICK' for n in brick.node_tree.nodes);assert sum(n.type=='BUMP' for n in brick.node_tree.nodes)==2
height_report=json.loads((HERE/'wall_height_validation.json').read_text())
changed=set(height_report['modified_source_mesh_names'])
wall_checks=0
current_bounds={}
for o in bpy.data.collections['01 Main walls'].objects:
 if o.type!='MESH':continue
 current_bounds[o.name]=[min(v.co[i] for v in o.data.vertices) for i in range(2)]+[max(v.co[i] for v in o.data.vertices) for i in range(2)]
 if o.name not in changed:continue
 bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),o.name;bm.free()
 for poly in o.data.polygons:
  if poly.normal.z>.5:
   for vi in poly.vertices:
    v=o.data.vertices[vi];assert abs(v.co.z-(3-.06*max(0,v.co.y-4.65)))<.00001,(o.name,list(v.co))
 wall_checks+=1
ceiling_checks=0
for o in bpy.data.collections['05 Roof - estimated'].objects:
 if not o.name.startswith('Ceiling |'):continue
 for poly in o.data.polygons:
  if poly.normal.z<-.5:
   for vi in poly.vertices:
    v=o.data.vertices[vi];assert abs(v.co.z-(3-.06*max(0,v.co.y-4.65)))<.00001,o.name
 ceiling_checks+=1
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Saguramo_House_Photo_Updated.blend'))
roof=set(o.name for o in bpy.data.collections['05 Roof - estimated'].objects if not o.name.startswith('Ceiling | measured'))
verified=0
for o in bpy.data.objects:
 if o.type=='MESH' and o.name not in roof:
  if o.name in changed:
   if o.name in current_bounds:
    bounds=[min(v.co[i] for v in o.data.vertices) for i in range(2)]+[max(v.co[i] for v in o.data.vertices) for i in range(2)]
    assert max(abs(a-b) for a,b in zip(bounds,current_bounds[o.name]))<.00001,o.name
   continue
  if o.name.startswith('Veranda steel post'):continue
  assert current.get(o.name)==sig(o),o.name;verified+=1
report={'saved_roof_file_reopened':True,'non_roof_meshes_identical_to_window_corrected_model':verified,'owner_wall_height_solids_verified':wall_checks,'ceiling_heights_verified':ceiling_checks,'changed_wall_footprint_bounds_verified':True,'all_opening_meshes_identical':True,'closed_roof_solids':solids,'black_roof_slope_measurements':measured,'roof_finishes_verified':True,'brick_texture_nodes_verified':True,'scene_count':11}
(HERE/'verification.json').write_text(json.dumps(report,indent=2));print('ROOF_VERIFIED',json.dumps(report))
