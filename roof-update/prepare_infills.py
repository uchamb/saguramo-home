import json
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
P=Path(__file__).resolve().parent;walls=json.loads((P/'wall_footprints.json').read_text());roof=json.loads((P/'roof_geometry.json').read_text())
result=[]
for w in walls:
 footprint=unary_union([Polygon(p) for p in w['bottom_faces']]).buffer(0)
 ilines=[LineString(p) for p in w['interior_edges']]
 for f in roof['roof_faces']:
  if not f['structural']:continue
  cut=footprint.intersection(Polygon([v[:2] for v in f['vertices']]))
  for g in getattr(cut,'geoms',[cut]):
   if g.geom_type!='Polygon' or g.area<.000001:continue
   # Remove numerical spikes at coincident edges, below 0.01mm precision.
   g=g.simplify(.000005,preserve_topology=True)
   rings=[list(g.exterior.coords)]+[list(r.coords) for r in g.interiors]
   mids=[]
   for ring in rings:
    for a,b in zip(ring,ring[1:]):
     mid=[(a[0]+b[0])/2,(a[1]+b[1])/2]
     if any(l.distance(Point(mid))<.0001 for l in ilines):mids.append(mid)
   result.append({'name':w['name'],'roof':f['name'],'plane':f['plane'],'geometry':{'rings':rings,'area':g.area,'triangles':[list(t.exterior.coords)[:3] for t in constrained_delaunay_triangles(g).geoms],'interior_midpoints':mids}})
(P/'infill_geometry.json').write_text(json.dumps(result))
