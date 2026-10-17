"""Add the verified C-AM packet library, preserving the existing VCO preview."""
import argparse
import html
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('packets', type=Path)
args = parser.parse_args()
dist = Path(__file__).resolve().parent / 'dist'
if not (dist / 'vco').exists():
    (dist / 'vco').mkdir()
    for path in list(dist.iterdir()):
        if path.is_file():
            shutil.copyfile(path, dist / 'vco' / path.name)
manifest = json.loads((args.packets / 'batch-manifest.json').read_text())
cards = []
for i, concept in enumerate(manifest['concepts']):
    cid = concept['conceptId']
    source, target = args.packets / cid, dist / 'concepts' / cid
    target.mkdir(parents=True, exist_ok=True)
    packet = json.loads((source / 'packet.json').read_text())
    names = ['packet.json', 'scene.json', 'poster.svg', 'models.js', 'player.js']
    names += [a['localFile'] for a in packet['narration']]
    for name in names:
        shutil.copyfile(source / name, target / name)
    nav = '<nav class="library-nav" aria-label="Concept library"><a href="/">← All concepts</a><span>' + cid + ' · ' + str(i + 1) + ' of 10</span>'
    if i:
        nav += '<a href="../' + manifest['concepts'][i-1]['conceptId'] + '/">Previous concept</a>'
    if i < 9:
        nav += '<a href="../' + manifest['concepts'][i+1]['conceptId'] + '/">Next concept →</a>'
    nav += '</nav>'
    page = (source / 'index.html').read_text()
    page = page.replace('<title>C-AM concept packet</title>', '<title>' + html.escape(packet['title']) + ' · Kiki</title>')
    page = page.replace('</style>', '.library-nav{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:24px;font-size:14px}.library-nav a{color:#126a49;min-height:44px;display:inline-flex;align-items:center}.library-nav span{margin-right:auto;color:#526657}</style>')
    page = page.replace('<main><header>', '<main>' + nav + '<header>')
    (target / 'index.html').write_text(page)
    mins, secs = divmod(round(concept['durationSeconds']), 60)
    scope = 'Audio per placard' if concept['audioScope'] == 'placard' else 'Whole-concept audio'
    cards.append(f'<a class="card" href="concepts/{cid}/"><span class="number">{cid} <span>→</span></span><h2>{html.escape(concept["title"])}</h2><div class="meta"><span>4 placards</span><span>{mins}:{secs:02} audio</span></div><div class="card-foot"><span>{scope}</span><strong>Explore concept →</strong></div></a>')
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kiki · Concept Canvas Studio</title><meta name="description" content="Review ten Analog Modulation concepts with mixed Odia–English lessons, narration and interactive models."><style>
:root{font-family:system-ui,sans-serif;color:#203d32;background:#f7f8f4}*{box-sizing:border-box}body{margin:0}a{color:inherit}header{border-bottom:1px solid #dce3da;background:white}.bar{max-width:1280px;margin:auto;padding:20px 24px;display:flex;align-items:center;gap:24px;flex-wrap:wrap}.brand{text-decoration:none;font-size:32px;font-weight:800;letter-spacing:-2px;color:#1e5845}.brand span{color:#d9a23e}.bar-label{font-size:12px;letter-spacing:1.5px;text-transform:uppercase}.draft{margin-left:auto;padding:8px 14px;background:#fcf2dc;color:#78581f;border-radius:24px;font-size:12px}main{max-width:1280px;margin:auto;padding:48px 24px}.eyebrow{font-size:12px;letter-spacing:2px;font-weight:600;text-transform:uppercase;color:#617769}h1{font-size:clamp(32px,5vw,52px);letter-spacing:-2px;line-height:1.1;max-width:800px;margin:14px 0 20px}.intro{font-size:18px;line-height:1.65;max-width:780px;color:#596e61}.stats{display:flex;flex-wrap:wrap;gap:12px 32px;margin:26px 0 32px}.stats strong{font-size:25px;margin-right:8px}.stats span{font-size:14px}.guide{padding:18px 22px;background:#eaf0e8;border-radius:12px;line-height:1.7;margin-bottom:32px}.guide p{margin:0}.guide small{display:block;margin-top:6px;color:#536759}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.card{background:white;border:1px solid #dce3da;border-radius:16px;padding:26px;text-decoration:none;display:flex;flex-direction:column;min-height:240px;transition:box-shadow .15s,border-color .15s}.card:hover,.card:focus-visible{border-color:#277450;box-shadow:0 4px 20px #203d3210}.number{font-size:12px;font-weight:600;letter-spacing:1px;color:#617769;display:flex;justify-content:space-between}.number span{font-size:20px;color:#277450}h2{font-size:23px;line-height:1.3;letter-spacing:-.4px;margin:16px 0 22px;max-width:430px}.meta{display:flex;gap:20px;color:#617769;font-size:13px;margin-top:auto}.card-foot{border-top:1px solid #e9ede6;display:flex;gap:12px;flex-wrap:wrap;justify-content:space-between;padding-top:16px;margin-top:20px;font-size:12px}.card-foot strong{color:#26704c;font-weight:600}footer{display:flex;gap:20px;justify-content:space-between;flex-wrap:wrap;border-top:1px solid #dce3da;margin-top:36px;padding-top:24px;font-size:13px;line-height:1.7;color:#617769}footer a{color:#26704c}a:focus-visible{outline:3px solid #caa045;outline-offset:4px}@media(max-width:650px){main{padding:32px 18px}.bar{padding:16px 18px;gap:12px}.bar-label{font-size:10px}.draft{margin-left:0}.grid{grid-template-columns:1fr}.card{padding:22px;min-height:220px}.intro{font-size:16px}.stats{gap:12px 20px}h1{letter-spacing:-1px}}@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body><header><div class="bar"><a class="brand" href="/">ki<span>ki</span></a><span class="bar-label">Concept Canvas Studio</span><span class="draft">Review draft</span></div></header><main><div class="eyebrow">ECE / Analog Modulation</div><h1>See the concept.<br>Change what happens.</h1><p class="intro">Explore each idea alongside its mixed Odia–English explanation and narration. Move the controls to see how the signal, spectrum or recovered output responds.</p><div class="stats"><span><strong>10</strong> concepts</span><span><strong>40</strong> placards</span><span><strong>22</strong> recordings</span></div><div class="guide"><p>Choose a concept, press Play to listen, and use the sliders to explore. Next and Back move through its four placards; Reset restores the model.</p><small>English source text is available. Narration is in mixed Odia–English; its scope is labelled on each page. Placard navigation is manual, with no sentence synchronization.</small></div><section class="grid" aria-label="Concepts">__CARDS__</section><footer><span>Scientific, native-Odia and pronunciation reviews are pending.<br>These are teaching models; this preview is separate from the learning app.</span><a href="vco/">Open the earlier VCO demo →</a></footer></main></body></html>'''
(dist / 'index.html').write_text(page.replace('__CARDS__', ''.join(cards)))
(dist / 'review-manifest.json').write_text(json.dumps({'schema': 'cam-sites-review/v1', 'concepts': manifest['concepts'], 'reviewStatus': 'pending', 'audioClipCount': 22}, indent=2))
print('Prepared ten concept previews and preserved the VCO demo.')
