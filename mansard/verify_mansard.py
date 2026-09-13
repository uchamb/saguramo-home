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
assert len(R['guard_segments'])==len(G['railing_segments'])
assert all(bpy.data.scenes.get(name) for name in R['views'])
# Independent checks of the owner's revised roof/deck relationship.
deck=bpy.data.objects['CONCEPT | raised second-floor timber deck | 300mm thick']
deck_x=max(v.co.x for v in deck.data.vertices);deck_y=max(v.co.y for v in deck.data.vertices);deck_east=min(v.co.y for v in deck.data.vertices)
main_sheets=[bpy.data.objects['MANSARD | '+q['name']] for q in G['roof_planes'][:2]]
rx=max(v.co.x for o in main_sheets for v in o.data.vertices);ry=max(v.co.y for o in main_sheets for v in o.data.vertices);ey=min(v.co.y for o in main_sheets for v in o.data.vertices)
assert abs(rx-deck_x)<1e-6 and abs(ry-deck_y)<1e-6
assert abs(ey-deck_east-1)<1e-6
approved=json.loads((P/'approved_south_room_signatures.json').read_text())
for name,s in approved.items():assert sig(bpy.data.objects[name])==s,name
# Gable openings are genuinely cut through the wall; glass and door frames match.
for side,y,direction in [('east',G['gable_doors']['east_y'],1),('west',G['gable_doors']['west_y'],-1)]:
 o=bpy.data.objects['MANSARD | '+side+' gable enclosure']
 for x in [G['ridge_x']-1.1,G['ridge_x'],G['ridge_x']+1.1]:
  for z in [F+.15,F+1.10,F+2.05]:
   hit,*_=o.ray_cast(Vector((x,y-direction,z)),Vector((0,direction,0)),distance=1.5);assert not hit,(side,x,z)
 pane=bpy.data.objects['MANSARD '+side.upper()+' | terrace door glass']
 assert list(pane.data.materials)[0].name=='Mansard | clear terrace glazing'
 assert abs(pane.dimensions.x-.95)<1e-6 and abs(pane.dimensions.z-2.10)<1e-6
 # Verify the wall still exists above the door.
 hit,*_=o.ray_cast(Vector((G['ridge_x'],y-direction,F+2.5)),Vector((0,direction,0)),distance=1.5);assert hit,side
st=G['east_stair'];cx,cy=st['turn_center_xy'];w=st['width_m']
for o in rails.objects:
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 # All north-side guards, including the east strip's north end, are removed.
 assert not (min(p.x for p in pts)>deck_x-.12 and max(p.y for p in pts)-min(p.y for p in pts)>.2),o.name
 # No west guard stands beside the roof footprint.
 assert not (min(p.y for p in pts)>deck_y-.13 and max(p.x for p in pts)>G['roof_bounds_xy'][0]+.01),o.name
 # No horizontal rail or bar blocks the middle of the east stair opening.
 for z in [F+.4,F+.9]:
  inv=o.matrix_world.inverted();hit,*_=o.ray_cast(inv@Vector((cx+w/2,deck_east-.20,z)),inv.to_3x3()@Vector((0,1,0)),distance=.4);assert not hit,o.name
assert any(abs(a[1]-(deck_y-.075))<1e-5 and a[0]<G['roof_bounds_xy'][0] for a,b in G['railing_segments'])
# Measure every saved tread and check the final riser into the deck.
last=0
for step in st['steps']:
 o=bpy.data.objects['EAST STAIR | tread %02d'%step['index']];top=max(v.co.z for v in o.data.vertices)
 assert abs(top-last-st['riser_m'])<1e-6,(step['index'],top,last)
 assert min(v.co.z for v in o.data.vertices)>last-.06
 last=top
assert abs(F-last-st['riser_m'])<1e-6
laststep=bpy.data.objects['EAST STAIR | tread %02d'%len(st['steps'])]
assert abs(max(v.co.y for v in laststep.data.vertices)-deck_east)<1e-6
assert abs(min(v.co.x for v in laststep.data.vertices)-cx)<1e-6
assert abs(max(v.co.x for v in laststep.data.vertices)-cx-w)<1e-6
assert len(st['steps'])+1==st['riser_count']
# First tread and the turn's structural newel sit on the existing Terrace 2.
terrace=next(o for o in bpy.data.collections['02 Floors and terraces'].objects if o.name.startswith('MAIN 01 |'))
for x,y in [(st['start_x']+.1,cy-w/2),(cx,cy)]:
 hit,loc,*_=terrace.ray_cast(Vector((x,y,1)),Vector((0,0,-1)));assert hit and abs(loc.z)<1e-6
report={'saved_file_reopened':True,'ridge_height_above_wood_floor_m':peak-F,'ridge_absolute_m':peak,'floor_level_m':F,'preserved_existing_meshes':len(R['preserved_mesh_signatures']),'approved_south_room_meshes_unchanged':len(approved),'original_house_file_unchanged':True,'black_roofs_and_deck_unchanged':True,'closed_roof_room_stair_solids':len(R['closed_solids']),'south_dormer_roof_cutout_verified':True,'doorway_clear_of_walls':True,'east_and_west_glazed_door_openings_verified':True,'roof_meets_north_and_west_deck_edges':True,'east_terrace_setback_m':ey-deck_east,'north_guards_removed':True,'west_guards_removed_beside_roof_and_retained_on_terrace':True,'east_stair_guard_opening_clear':True,'door_nominal_width_m':1,'door_height_m':2.2,'south_room_gross_area_m2':room['area_m2'],'uncovered_upper_terrace_area_m2':G['terrace_area_m2'],'railing_height_m':rail_top-F,'guarded_deck_perimeter_m':sum(s['length_m'] for s in R['guard_segments']),'railing_posts':R['railing_posts'],'east_stair':{'riser_count':st['riser_count'],'riser_m':st['riser_m'],'width_m':w,'winder_treads':st['winder_treads'],'first_tread_and_turn_support_on_terrace_2':True,'top_tread_connects_to_upper_deck':True},'preview_scenes':R['views']}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('MANSARD_VERIFIED',json.dumps(report))
