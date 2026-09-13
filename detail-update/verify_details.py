"""Reopen latest .blend and verify isolated edits, clear doorway and two railings."""
import bpy,json,math,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
G=json.loads((P/'detail_geometry.json').read_text());B=json.loads((P/'build_validation.json').read_text())
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world),[m.name for m in o.data.materials])).encode()).hexdigest()
for name,s in B['unchanged_mesh_signatures'].items():assert name in bpy.data.objects and sig(bpy.data.objects[name])==s,name
for name in B['removed_objects']:assert name not in bpy.data.objects,name
assert not any('low stair enclosure' in o.name for o in bpy.data.objects)
solids=0
for name in B['new_object_names']:
 o=bpy.data.objects[name]
 assert all(math.isfinite(c) for v in o.data.vertices for c in v.co),name
 bm=bmesh.new();bm.from_mesh(o.data);assert all(e.is_manifold for e in bm.edges),name;bm.free();solids+=1
# Cast through the full original wall depth at low, mid and upper elevations.
# Window sill brick must no longer obstruct the two full-height side panels.
verts=[];faces=[]
for o in bpy.data.collections['01 Main walls'].objects:
 if o.type!='MESH':continue
 off=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend([tuple(i+off for i in f.vertices) for f in o.data.polygons])
tree=BVHTree.FromPolygons(verts,faces)
r=G['opening'];x0,y0,x1,y1=r['bounds'];samples=0
for f in [.08,.20,.40,.52,.62,.80,.92]:
 for z in [.12,.50,1.40,2.35]:
  start=Vector((x0+(x1-x0)*f,y1+.03,z))
  hit=tree.ray_cast(start,Vector((0,-1,0)),y1-y0+.06)
  assert hit[0] is None,('wall obstructs opening',f,z,hit[0]);samples+=1
prefix='DETAIL | Childroom to Terrace 1'
assert len([o for o in bpy.data.objects if o.name.startswith(prefix+' | full-height side glass')])==2
screen=bpy.data.objects[prefix+' | centre pleated insect screen'];assert len(screen.data.vertices)>100
assert abs(max((bpy.data.objects[prefix+' | lintel'].matrix_world@v.co).z for v in bpy.data.objects[prefix+' | lintel'].data.vertices)-3)<1e-5
# Two parallel guards, each has posts, fine vertical infill and both rails.
rail_runs=[]
for run in G['railings']['runs']:
 p='DETAIL | Basement railing | '+run['name'];objects=[o for o in bpy.data.objects if o.name.startswith(p)]
 bars=[o for o in objects if 'vertical iron bar' in o.name];assert len(bars)>=20
 posts=[o for o in objects if o.name.startswith(p+' | post')];assert len(posts)>=3
 for o in bars:
  assert o.dimensions.z>.8 and o.dimensions.x<.021 and o.dimensions.y<.021
  assert o.data.materials[0].name=='Detail | black door and railing finish'
 top=max((o.matrix_world@v.co).z for o in objects for v in o.data.vertices);assert abs(top-.95)<1e-5
 rail_runs.append({'name':run['name'],'vertical_bars':len(bars),'posts':len(posts),'top_z_m':top})
assert len(bpy.data.scenes)==13
report={'saved_blend_reopened':True,'unchanged_meshes_verified':len(B['unchanged_mesh_signatures']),'closed_new_meshes':solids,'door_wall_clearance_samples':samples,'survey_opening_width_m':x1-x0,'door_head_m':r['head_m'],'side_glass_panels':2,'centre_pleated_screen':True,'removed_brick_guard_count':2,'railings':rail_runs,'roof_and_other_openings_unchanged':True,'scene_count':13}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('DETAILS_VERIFIED',json.dumps(report))
