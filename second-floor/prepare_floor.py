from pathlib import Path
import json
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
P=Path(__file__).resolve().parent;OUT=P.parent
R=json.loads((OUT/'roof-update/roof_geometry.json').read_text());D=json.loads((OUT/'survey_geometry.json').read_text())
red=[f for f in R['roof_faces'] if f['structural'] and f['material']=='red']
g=unary_union([Polygon([v[:2] for v in f['vertices']]) for f in red]);assert g.is_valid and g.geom_type=='Polygon'
def geom(g):
 if g.is_empty:return None
 if g.geom_type=='MultiPolygon':return {'parts':[geom(p) for p in g.geoms]}
 return {'rings':[list(g.exterior.coords)]+[list(r.coords) for r in g.interiors],'area':g.area,'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms]}
ceilings=[]
for r in D['levels']['main']:
 if r['type']!='iataki':continue
 p=Polygon(r['geometry']['rings'][0]);overlap=p.intersection(g)
 if overlap.area<1e-6:continue
 remaining=p.difference(g)
 ceilings.append({'room_id':r['id'],'original_bounds':list(p.bounds),'remaining_under_black_roof':geom(remaining),'removed_area_m2':overlap.area})
report={'clearance_above_black_roof_m':.10,'floor_thickness_m':.30,'footprint_basis':'Exact union of former red roof plan footprints, including its small corner hip and existing overhangs','area_m2':g.area,'geometry':geom(g),'red_structural_surfaces':[f['name'] for f in red],'ceilings':ceilings,'stage':'Flat timber-finished second-floor concept only; no mansard, upper walls or roof added','wood_finish':'Natural warm oak boards; 160mm x 1800mm pattern is illustrative'}
(P/'floor_geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print('Flat floor footprint',g.area,'m2; affected ceiling rooms',len(ceilings))
