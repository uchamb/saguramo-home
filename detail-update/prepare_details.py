from pathlib import Path
import json
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
P=Path(__file__).resolve().parent
D=json.loads((P.parent/'survey_geometry.json').read_text())
R={r['id']:r for r in D['levels']['main']}
g=unary_union([Polygon(R[i]['geometry']['rings'][0]) for i in [9,32,10]]).buffer(.00003,join_style=2).buffer(-.00003,join_style=2)
assert g.geom_type=='Polygon' and g.is_valid
spec={'opening':{'name':'Childroom to Terrace 1','source_records':[9,32,10],'reference':'reference/childroom-door.png','bounds':list(g.bounds),'geometry':{'rings':[list(g.exterior.coords)],'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms],'area':g.area},'sill_m':.025,'head_m':2.50,'wall_top_m':3.0,'panel_splits':[.33,.71],'photo_left_to_right_panel_ratios':[.29,.38,.33],'frame_depth_m':.09,'frame_face_m':.055,'pleat_pitch_m':.014,'basis':'Survey footprint retained; head height, panel ratios, frame and pleated insect-screen details estimated from owner close-up. No transom or raised side sills.'},'railings':{'reference':'reference/basement-railing.png','replaced_records':[25,26],'height_m':.95,'post_width_m':.045,'bar_width_m':.019,'maximum_bar_pitch_m':.12,'bottom_rail_z_m':.075,'runs':[{'name':'Terrace 1 side','start':[-6.41864,8.92879],'end':[-2.80862,8.92879]},{'name':'Outer side','start':[-6.78862,10.62762],'end':[-2.80860,10.62762]}],'basis':'Both original low brick guards replaced with black metal railings along their survey centre lines. Existing 0.95m guard height retained; sections and bar spacing are photo estimates. Stair geometry and access ends remain unchanged.'}}
(P/'detail_geometry.json').write_text(json.dumps(spec,indent=2)+'\n')
print('Prepared door footprint:',g.area,'m2;',g.bounds)
