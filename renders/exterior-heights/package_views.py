"""Validate the eight PNGs and assemble a labeled comparison sheet and gallery."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,html,zipfile
P=Path(__file__).resolve().parent;OUT=P.parent.parent
M=json.loads((P/'render_manifest.json').read_text());source=OUT/M['source_model']
assert hashlib.sha256(source.read_bytes()).hexdigest()==M['source_model_sha256']
sides=['south-east','south-west','south','west'];labels=['SOUTHEAST CORNER','SOUTHWEST CORNER','SOUTH SIDE','WEST SIDE'];heights=[2,10]
assert len(M['views'])==8
rows=[]
for side in sides:
 pair=[v for v in M['views'] if v['side']==side];assert len(pair)==2
 assert pair[0]['camera_location_m'][:2]==pair[1]['camera_location_m'][:2]
 assert pair[0]['lens_mm']==pair[1]['lens_mm']
 for v in pair:
  assert abs(v['camera_location_m'][2]-M['ground_datum_m']-v['height_above_ground_m'])<1e-6
  with Image.open(P/v['file']) as im:assert im.size==(1920,1440);im.verify()
  rows.append({'file':v['file'],'bytes':(P/v['file']).stat().st_size,'sha256':hashlib.sha256((P/v['file']).read_bytes()).hexdigest()})
assert len({r['sha256'] for r in rows})==8
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(fontpath,24);title=ImageFont.truetype(fontpath,34);small=ImageFont.truetype(fontpath,20)
w,h=600,450;pad=18;header=96;label_h=44;row_h=h+label_h+pad
sheet=Image.new('RGB',(pad*5+w*4,header+row_h*2+52),'#f1f0ed');draw=ImageDraw.Draw(sheet)
draw.text((pad,18),'SAGURAMO / EXTERIOR VIEWS',font=title,fill='#202625')
draw.text((pad,61),'Camera heights above outdoor ground · 2m top row / 10m bottom row',font=small,fill='#4c5552')
for row,height in enumerate(heights):
 for col,(side,label) in enumerate(zip(sides,labels)):
  v=next(v for v in M['views'] if v['side']==side and v['height_above_ground_m']==height)
  x=pad+col*(w+pad);y=header+row*row_h
  draw.text((x,y+7),f'{label} / {height}m',font=font,fill='#202625')
  with Image.open(P/v['file']) as im:sheet.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(x,y+label_h))
draw.text((pad,sheet.height-35),'Eight original 1920 × 1440 PNGs included; model geometry unchanged.',font=small,fill='#4c5552')
sheet.save(P/'comparison.jpg',quality=94,subsampling=0)
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Saguramo exterior views</title><style>body{font:16px system-ui;background:#eeeae4;color:#222;margin:32px}h1{font-size:30px}main{max-width:1500px;margin:auto}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:40px}figure{margin:0;background:white;padding:12px;border-radius:8px}img{display:block;width:100%;height:auto}figcaption{padding:10px 0 2px}a{color:inherit}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><main><h1>Saguramo exterior views</h1><p>Four directions at 2m and 10m above outdoor ground. Click an image to open its full-resolution PNG.</p><p><a href="exterior-renders.zip">Download all eight PNGs</a></p>']
for side,label in zip(sides,labels):
 parts.append(f'<h2>{html.escape(label.title())}</h2><section class="pair">')
 for height in heights:
  path=f'{height:02d}m/{side}.png';parts.append(f'<figure><a href="{path}"><img src="{path}" alt="{label.title()}, camera {height}m above ground"></a><figcaption>{height}m above ground · 1920 × 1440</figcaption></figure>')
 parts.append('</section>')
parts.append('</main></html>');(P/'index.html').write_text(''.join(parts))
with zipfile.ZipFile(P/'exterior-renders.zip','w',compression=zipfile.ZIP_STORED) as archive:
 for v in M['views']:archive.write(P/v['file'],v['file'])
 archive.write(P/'comparison.jpg','comparison.jpg');archive.write(P/'render_manifest.json','render_manifest.json')
report={'source_model_unchanged':True,'camera_heights_verified':[2,10],'ground_datum_m':M['ground_datum_m'],'pair_xy_and_lens_identical':True,'unique_images':8,'resolution':[1920,1440],'files':rows}
(P/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('EIGHT_IMAGES_PACKAGED_AND_VERIFIED')
