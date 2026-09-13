"""Add west railing's end column and share the tile finish across both terraces."""
import bpy,json,math,ast,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P.parent
COL={c.name[:2]:c for c in bpy.context.scene.collection.children}
for node in ast.parse((OUT/'build_house.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['move','box']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(OUT/'build_house.py'),'exec'))
def gs(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
def sig(o):return hashlib.sha256((gs(o)+repr([m.name for m in o.data.materials])).encode()).hexdigest()
previous=json.loads((P/'build_validation.json').read_text());run=next(r for r in previous['railings'] if r['name']=='Outer side');x,y=run['start'];prefix='DETAIL | Basement railing | Outer side'
post=next(o for o in bpy.data.objects if o.name.startswith(prefix+' | low post') and math.dist(o.location.xy,(x,y))<.001)
plate=next(o for o in bpy.data.objects if o.name.startswith(prefix+' | low-post base plate') and math.dist(o.location.xy,(x,y))<.001)
rails=[bpy.data.objects[prefix+' | bay 0 '+label] for label in ['top handrail','bottom rail']]
tile=bpy.data.materials['Terrace 1 | weathered grey taupe square tiles'];terrace2=bpy.data.objects['MAIN 01 | terasa | 52.93 m2']
floors=[o for o in bpy.data.objects if o.type=='MESH' and (tile in list(o.data.materials) or o==terrace2)]
modified=[post,plate,*rails,*floors]
unchanged={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH' and o not in modified};floor_shapes={o.name:gs(o) for o in floors}
removed=[post.name,plate.name]
for o in [post,plate]:bpy.data.objects.remove(o,do_unlink=True)
black=bpy.data.materials['Detail | black door and railing finish'];roof=json.loads((OUT/'roof-update/roof_geometry.json').read_text());face=next(f for f in roof['roof_faces'] if f['name']=='Dark south veranda canopy');a,b,c=face['plane']
def soffit(x,y):return a*x+b*y+c-.085
h=soffit(x,y);column=box(prefix+' | full-height outer end column',(x,y,h/2),(.085,.085,h),black,'04')
for v in column.data.vertices:
 if v.co.z>0:
  w=column.matrix_world@v.co;v.co.z=soffit(w.x,w.y)-column.location.z
column['basis']='Owner correction: west railing has two full-height columns, matching the east railing arrangement';column['roof_plane']='Dark south veranda canopy';column['railing_side']='west'
newplate=box(prefix+' | outer end column base plate',(x,y,.005),(.14,.14,.01),black,'04')
# Trim 20mm from the start of both rails so they meet the wider column face.
for ob in rails:
 for v in ob.data.vertices:
  if v.co.x<0:v.co.x+=.020
 ob.data.update()
# The same shader datablock serves Terrace 1, Terrace 2 and existing tile steps.
terrace2.data.materials.clear();terrace2.data.materials.append(tile)
tile.name='Terraces | weathered grey taupe square tiles';tile['scope']='Terrace 1, Terrace 2 and Terrace 1 entry steps'
assert all(sig(bpy.data.objects[k])==v for k,v in unchanged.items())
assert all(gs(bpy.data.objects[k])==v for k,v in floor_shapes.items())
existing=previous['railings'][0]['existing_column'];east=[existing,previous['columns'][0]['name']];west=[previous['columns'][1]['name'],column.name]
report={'unchanged_mesh_signatures':unchanged,'floor_geometry_signatures':floor_shapes,'removed_low_post_objects':removed,'new_column':column.name,'new_base_plate':newplate.name,'modified_rails':[o.name for o in rails],'east_full_height_columns':east,'west_full_height_columns':west,'roof_plane':face['plane'],'column_center_xy':[x,y],'tile_material':tile.name,'tile_targets':[o.name for o in floors],'scene_count':len(bpy.data.scenes)}
(P/'final_build_validation.json').write_text(json.dumps(report,indent=2)+'\n')
notes='''FINAL OWNER CORRECTIONS
West basement railing now has two full-height black columns, matching the
east railing's two-column arrangement. Existing east railing remains unchanged.
The added west end column replaces the former short end post and meets the
canopy soffit. Both rails meet the column face. The previously specified
columns 1m from Bathroom 2 stay in place.
Terrace 1 and Terrace 2 now share exactly the same grey/taupe/brown tile shader.
All floor geometry is unchanged. Tile size remains an estimated 500mm.
'''
bpy.data.texts.new('FINAL TERRACE CORRECTIONS').write(notes);(P/'FINAL_NOTES.txt').write_text(notes)
bpy.context.window.scene=bpy.data.scenes['01 Exterior'];bpy.ops.object.select_all(action='DESELECT');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Saguramo_House_Roof_Updated.blend'))
for scene,file in [('13 Basement railings','basement-railings'),('09 Drone roof','overview'),('01 Exterior','exterior'),('14 Terrace 1 tiles','terrace-tiles')]:
 sc=bpy.data.scenes[scene];sc.render.filepath=str(P/(file+'.png'));bpy.ops.render.render(write_still=True,scene=scene)
print('WEST_COLUMN_AND_TERRACE_2_COMPLETE')
