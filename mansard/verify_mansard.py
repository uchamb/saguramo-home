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
assert abs(rx-deck_x)<1e-6
assert abs(ey-deck_east-1.5)<1e-6 and abs(deck_y-ry-1.5)<1e-6
approved=json.loads((P/'approved_east_stair_signatures.json').read_text())
for name,s in approved.items():assert sig(bpy.data.objects[name])==s,name
# The yellow outline becomes a single rectangular deck, with original height
# and thickness. Confirm that the extension covers the old footprint exactly.
deck_south=min(v.co.x for v in deck.data.vertices)
assert abs(deck_south+6.85)<1e-6
assert all(abs(v.co.z-F)<1e-6 or abs(v.co.z-(F-.30))<1e-6 for v in deck.data.vertices)
deck_tops=[p for p in deck.data.polygons if p.normal.z>.99]
assert abs(sum(p.area for p in deck_tops)-194.418)<1e-4
assert all(deck.data.materials[p.material_index].name=='Second-floor concept | natural oak boards' for p in deck_tops)
for x,y in [(-6.8,4.6),(-6.8,0),(-4.7,4.6),(-4.7,-2.9)]:
 hit,loc,*_=deck.ray_cast(Vector((x,y,F+1)),Vector((0,0,-1)));assert hit and abs(loc.z-F)<1e-6
# Ridge and both end doors are centered in the widened main roof, independently
# of the south dormer. The north and south slope pitches must now be equal.
roof_south=min(v.co.x for o in main_sheets for v in o.data.vertices);center=(roof_south+rx)/2
assert abs(roof_south+1.60)<1e-6 and abs(center-3.49)<1e-6
cap=bpy.data.objects['MANSARD | ridge cap | 5m above wooden floor']
crest=[v.co for v in cap.data.vertices if abs(v.co.z-peak)<1e-6]
assert len(crest)==2 and all(abs(v.x-center)<1e-6 for v in crest)
assert abs(abs(G['roof_planes'][0]['plane'][0])-abs(G['roof_planes'][1]['plane'][0]))<1e-8
for side in ['east','west']:
 door=bpy.data.objects['MANSARD '+side.upper()+' | terrace door glass'];assert abs(door.location.x-center)<1e-6
# West rail spans the full new terrace and the south guard follows the new edge.
west_rails=[o for o in rails.objects if o.name.startswith('UPPER TERRACE | horizontal rail') and abs(o.location.y-(deck_y-.075))<1e-5]
assert len(west_rails)==2
for o in west_rails:
 pts=[o.matrix_world@v.co for v in o.data.vertices]
 assert abs(min(p.x for p in pts)-(deck_south+.075))<1e-5 and abs(max(p.x for p in pts)-(deck_x-.075))<1e-5
south_rails=[o for o in rails.objects if o.name.startswith('UPPER TERRACE | horizontal rail') and abs(o.location.x-(deck_south+.075))<1e-5]
assert len(south_rails)==2
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
report={'saved_file_reopened':True,'ridge_height_above_wood_floor_m':peak-F,'ridge_absolute_m':peak,'floor_level_m':F,'preserved_existing_meshes':len(R['preserved_mesh_signatures']),'approved_east_stair_meshes_unchanged':len(approved),'original_house_file_unchanged':True,'original_black_roofs_unchanged':True,'deck_height_and_thickness_preserved':True,'expanded_deck_area_m2':sum(p.area for p in deck_tops),'south_extension_area_m2':G['deck_extension_area_m2'],'new_south_deck_edge_x':deck_south,'new_south_roof_edge_x':roof_south,'ridge_and_end_doors_center_x':center,'symmetric_roof_slopes':True,'closed_roof_room_stair_solids':len(R['closed_solids']),'south_dormer_roof_cutout_verified':True,'doorway_clear_of_walls':True,'east_and_west_glazed_door_openings_verified':True,'roof_meets_north_deck_edge':True,'east_terrace_setback_m':ey-deck_east,'west_terrace_setback_m':deck_y-ry,'north_guards_removed':True,'west_terrace_fully_guarded':True,'expanded_south_edge_guarded':True,'east_stair_guard_opening_clear':True,'door_nominal_width_m':1,'door_height_m':2.2,'south_room_gross_area_m2':room['area_m2'],'uncovered_upper_terrace_area_m2':G['terrace_area_m2'],'railing_height_m':rail_top-F,'guarded_deck_perimeter_m':sum(s['length_m'] for s in R['guard_segments']),'railing_posts':R['railing_posts'],'east_stair':{'riser_count':st['riser_count'],'riser_m':st['riser_m'],'width_m':w,'winder_treads':st['winder_treads'],'first_tread_and_turn_support_on_terrace_2':True,'top_tread_connects_to_upper_deck':True},'preview_scenes':R['views']}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('MANSARD_VERIFIED',json.dumps(report))
