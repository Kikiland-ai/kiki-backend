"""Provisional cue packet validation; fixture geometry is synthetic, not a live anchor."""
import copy,json
from datetime import datetime,timedelta
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
ROOT=Path(__file__).resolve().parents[1]
schema=json.loads((ROOT/'contracts/screen_writing.schema.json').read_text())
example=json.loads((ROOT/'docs/architecture/examples/screen-writing.synthetic.example.json').read_text())
validator=Draft202012Validator(schema,format_checker=FormatChecker());Draft202012Validator.check_schema(schema)

def check(packet,context,now,live_adapter=False):
 validator.validate(packet)
 assert packet['context']==context,'Stale or foreign lab context'
 validity=packet['validity'];received=datetime.fromisoformat(packet['evidence']['received_at'])
 created=datetime.fromisoformat(validity['created_at']);expires=datetime.fromisoformat(validity['expires_at'])
 assert created<=now<expires and 0<(expires-created).total_seconds()<=8,'Expired or excessive cue lifetime'
 assert 0<=(now-received).total_seconds()*1000<=validity['max_frame_age_ms'],'Stale source frame'
 assert packet['render']['surface']!='live_workspace' or live_adapter,'Live workspace adapter missing'
 if packet['target']['resolution']=='unresolved':assert not packet['operations'] and packet['target']['region'] is None,'Drawing unresolved target'
 else:assert packet['target']['region'] is not None,'Resolved target has no region'
 for region in [packet['target']['region']]+[o.get('region') for o in packet['operations']]:
  if region:assert region['x']+region['width']<=1 and region['y']+region['height']<=1,'Region exceeds source frame'
 return True
now=datetime.fromisoformat('2026-10-14T00:30:02+05:30');check(example,example['context'],now)
mutations={
 'stale_visit':lambda p:p['context'].update(visit_id='different-visit'),
 'out_of_frame':lambda p:p['target']['region'].update(x=.9,width=.3),
 'unresolved_drawing':lambda p:p['target'].update(resolution='unresolved',region=None),
 'missing_live_adapter':lambda p:p['render'].update(surface='live_workspace'),
 'arbitrary_code':lambda p:p['operations'][0].update(javascript='untrusted'),
 'expired_cue':lambda p:p['validity'].update(expires_at='2026-10-14T00:30:01+05:30')}
for name,mutate in mutations.items():
 p=copy.deepcopy(example);mutate(p)
 try:check(p,example['context'],now)
 except (AssertionError,ValidationError):pass
 else:raise AssertionError(name)
print(json.dumps({'status':'PASS','rejected':list(mutations),'live_overlay_verified':False}))
