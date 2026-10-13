import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

report_path=Path('work/gemini-access-investigation.json')
key=os.environ['GEMINI_API_KEY']
report=json.loads(report_path.read_text())
advertised={m['name'].removeprefix('models/') for m in report['models']}
payload={'contents':[{'role':'user','parts':[{'text':'Reply with exactly OK.'}]}], 'generationConfig':{'maxOutputTokens':128}}
encoded=json.dumps(payload).encode()
for model in sys.argv[1:]:
    if model not in advertised:
        print('Not advertised; skipped:',model,flush=True)
        continue
    if any(p['model']==model and p['probe']=='minimal_text' for p in report['probes']):
        print('Existing probe preserved; skipped:',model,flush=True)
        continue
    result={'model':model,'probe':'minimal_text','request_sha256':hashlib.sha256(encoded).hexdigest()}
    req=urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',data=encoded,headers={'Content-Type':'application/json','x-goog-api-key':key},method='POST')
    start=time.monotonic()
    try:
        with urllib.request.urlopen(req,timeout=45) as response:
            result['http_status']=response.status
            body=json.loads(response.read(2000000))
        result['model_version']=body.get('modelVersion')
        candidates=body.get('candidates',[])
        result['finish_reasons']=[c.get('finishReason') for c in candidates]
        result['candidate_count']=len(candidates)
        result['has_non_thought_text']=any(isinstance(p.get('text'),str) and bool(p['text']) and not p.get('thought') for c in candidates for p in c.get('content',{}).get('parts',[]))
        result['usage']={k:v for k,v in body.get('usageMetadata',{}).items() if isinstance(v,int)}
    except urllib.error.HTTPError as error:
        result['http_status']=error.code
        result['retry_after']=error.headers.get('Retry-After')
        try:
            body=json.loads(error.read(100000))
            detail=body.get('error',{})
            result['error']={k:v.replace(key,'[REDACTED]') if isinstance(v,str) else v for k,v in detail.items() if k in ('code','status','message') and isinstance(v,(str,int))}
        except (ValueError,UnicodeError):
            result['error']={'message':'Non-JSON error body withheld'}
    except (urllib.error.URLError,OSError,ValueError):
        result['error']={'message':'Transport/JSON failure; raw details withheld'}
    result['elapsed_seconds']=round(time.monotonic()-start,3)
    report['probes'].append(result)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False),flush=True)
