"""Apply owner wall heights, preserving footprint and opening elevations."""
import bpy,bmesh,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
G=json.loads((HERE/'roof_geometry.json').read_text())
def wall_height(y):return 3.0-.06*max(0,y-4.65)
changed=[]
for o in list(bpy.data.collections['01 Main walls'].objects):
 if o.type!='MESH' or abs(max(v.co.z for v in o.data.vertices)-2.9)>.002:continue
 # Insert vertices where a long wall crosses from constant height to slope.
 bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,4.65,0),plane_no=(0,1,0),clear_inner=False,clear_outer=False)
 for v in bm.verts:
  if abs(v.co.z-2.9)<.002:v.co.z=wall_height(v.co.y)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 if o.data.uv_layers.active:
  for poly in o.data.polygons:
   if abs(poly.normal.z)<.8:
    for i in poly.loop_indices:o.data.uv_layers.active.data[i].uv.y=o.data.vertices[o.data.loops[i].vertex_index].co.z
 o['accuracy']='Survey XY and photo openings retained; owner wall height 3m; west walls fall 6cm/m from red-roof junction'
 changed.append(o.name)
for o in list(bpy.data.collections['05 Roof - estimated'].objects):
 if not o.name.startswith('Ceiling |'):continue
 bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,4.65,0),plane_no=(0,1,0),clear_inner=False,clear_outer=False)
 for v in bm.verts:v.co.z=wall_height(v.co.y)+(.04 if v.co.z>2.94 else 0)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 old=o.name;o.name=old.replace('measured underside 2.90m','owner height 3m; west slope 6pct')
 o['accuracy']='Owner height supersedes prior 2.90m ceiling assumption; ceiling underside follows wall height, 40mm estimated lining'
 changed.append(old)
report={'main_wall_height_m':3.0,'west_high_wall_m':3.0,'west_slope_m_per_m':.06,'west_main_outer_wall_m':wall_height(9.138),'west_annex_outer_wall_m':wall_height(10.878),'approximate_owner_low_wall_m':2.55,'priority':'Owner confirmed retain 6cm/m; 2.55m approximate','modified_source_mesh_names':changed,'opening_elevations_unchanged':True}
(HERE/'wall_height_validation.json').write_text(json.dumps(report,indent=2))
print('WALL_HEIGHTS_APPLIED',json.dumps(report))
