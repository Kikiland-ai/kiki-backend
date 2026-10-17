"""Browser pixel regression: unchanged sources must survive JPEG/raster comparison.
Supplied images stay local; output contains only hashes and numeric diagnostics.
No model requests, production calls or installed-extension claims.
"""
import asyncio,json,argparse,base64,hashlib
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[3]
async def main():
 parser=argparse.ArgumentParser();parser.add_argument("--image",action="append",default=[]);parser.add_argument("--output",default="work/still-frame-diagnostic/raster-regression.json");args=parser.parse_args()
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page()
  await page.add_script_tag(path=str(ROOT/'prototypes/json_stream_site/assets/writing-protocol.js'))
  results=await page.evaluate('''async()=>{
   const rows=[];
   for(const [width,height] of [[1200,800],[1848,1014],[1920,1080],[2560,1440]]){
    const raw=document.createElement('canvas');raw.width=width;raw.height=height;const c=raw.getContext('2d');c.fillStyle='white';c.fillRect(0,0,width,height);
    c.fillStyle='#333';c.font='14px Arial';for(let y=32;y<height;y+=29){c.fillText('Message  Carrier  Modulator  Receiver  Recovery Gain 2  Frequency (rad/sec) 2*pi*2000',70,y);c.strokeStyle='#333';c.strokeRect(65,y+3,540,21);c.beginPath();c.moveTo(605,y+11);c.lineTo(width-100,y+11);c.stroke();}
    const encoded=document.createElement('canvas'),scale=Math.min(1,1600/Math.max(width,height));encoded.width=Math.round(width*scale);encoded.height=Math.round(height*scale);encoded.getContext('2d').drawImage(raw,0,0,encoded.width,encoded.height);
    const jpeg=await new Promise(r=>encoded.toBlob(r,'image/jpeg',.8)),decoded=await createImageBitmap(jpeg);
    const fp=KikiWritingProtocol.fingerprint,reference=fp(decoded),live=fp(raw),canonical=fp(encoded),max=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
    rows.push({source:[width,height],encoded:[encoded.width,encoded.height],raw_vs_jpeg:{changed:KikiWritingProtocol.changed(live,reference),max_delta:max(live,reference),tiles_over_3:live.filter((v,i)=>Math.abs(v-reference[i])>3).length},same_size_raw_vs_jpeg:{changed:KikiWritingProtocol.changed(canonical,reference),max_delta:max(canonical,reference),tiles_over_3:canonical.filter((v,i)=>Math.abs(v-reference[i])>3).length},raw_vs_itself:KikiWritingProtocol.changed(live,live)});decoded.close();
   }return rows;
  }''')
  for path in args.image:
   image_path=Path(path);pixels=image_path.read_bytes()
   row=await page.evaluate('''async data=>{const img=await createImageBitmap(await(await fetch(data)).blob()),raw=document.createElement('canvas');raw.width=img.width;raw.height=img.height;raw.getContext('2d').drawImage(img,0,0);const encoded=document.createElement('canvas'),scale=Math.min(1,1600/Math.max(img.width,img.height));encoded.width=Math.round(img.width*scale);encoded.height=Math.round(img.height*scale);encoded.getContext('2d').drawImage(raw,0,0,encoded.width,encoded.height);const blob=await new Promise(r=>encoded.toBlob(r,'image/jpeg',.8)),decoded=await createImageBitmap(blob),f=KikiWritingProtocol;const reference=f.fingerprint(decoded),before=f.difference(f.fingerprint(raw),reference),after=f.difference(f.fingerprint(encoded),reference);encoded.getContext('2d').fillStyle='black';encoded.getContext('2d').fillRect(encoded.width*.3,encoded.height*.4,encoded.width*.08,encoded.height*.08);const changed_source_rejected=f.changed(f.fingerprint(encoded),reference);img.close();decoded.close();return {source:[raw.width,raw.height],encoded:[encoded.width,encoded.height],before,after,changed_source_rejected};}''', 'data:image/png;base64,'+base64.b64encode(pixels).decode())
   row.update(source_kind='supplied_image',source_name=image_path.name,sha256=hashlib.sha256(pixels).hexdigest());results.append(row)
  for row in results:
   if 'after' in row:
    assert not row['after']['changed'],row
    assert row['changed_source_rejected'],row
   else:assert not row['same_size_raw_vs_jpeg']['changed'],row
  out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
  await browser.close()
asyncio.run(main())
