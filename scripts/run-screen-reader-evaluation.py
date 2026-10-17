"""Free deterministic acceptance by default; --live adds five bounded paid vision calls."""
import argparse,datetime,glob,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'work/evaluations/latest');args=parser.parse_args()
 output=args.output.resolve();output.mkdir(parents=True,exist_ok=True);site=ROOT/'prototypes/json_stream_site'
 report={'schema':'screen-reader-evaluation/v1','started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),'experiment':'stream-context-batch/v1','runtime':{'python':sys.version.split()[0],'node':subprocess.check_output(['node','--version'],text=True).strip()},'vision_mocked_in_offline_checks':True,'real_simulink_accuracy_claim':False,'paid_model_calls':0,'fixture_sha256':{},'checks':[],'passed':False}
 manifest=json.loads((ROOT/'fixtures/json-stream/manifest.json').read_text(encoding='utf-8'))
 for case in manifest['cases']:
  actual=hashlib.sha256((ROOT/case['image']).read_bytes()).hexdigest()
  if actual!=case['sha256']:raise SystemExit('Fixture integrity failure: '+case['id'])
  report['fixture_sha256'][case['id']]=actual
 def run(name,command,cwd=ROOT):
  started=time.monotonic()
  # Offline checks receive no provider secrets, even when the shell has them.
  env={k:v for k,v in os.environ.items() if not k.startswith(('GEMINI_','GOOGLE_API_KEY'))}
  if name=='live-vision':env=os.environ.copy()
  # Child Python processes read UTF-8 sources; Windows otherwise defaults to the ANSI code page.
  env['PYTHONUTF8']='1'
  try:
   result=subprocess.run(command,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
   status=result.returncode;log=result.stdout
  except subprocess.TimeoutExpired:
   status=124;log='Evaluation timed out after 180 seconds; output omitted.\n'
  (output/(name+'.log')).write_text(log,encoding='utf-8')
  report['checks'].append({'name':name,'command':command,'returncode':status,'seconds':round(time.monotonic()-started,3),'log':name+'.log'})
  print(f'{name}: {"PASS" if status==0 else "FAIL"}',flush=True)
  if status and name!='live-vision':
   print(f'Failed offline check diagnostics ({name}; full log in artifact):\n'+log[-18000:],flush=True)
  return status==0
 jobs=[('site-build',['node','scripts/build.mjs'],site),('python',['python','-m','unittest','discover','-s','tests','-q'],ROOT),('node',['node','--test',*sorted(str(Path(p).relative_to(site)) for p in glob.glob(str(site/'scripts/test-*.mjs')))],site),('replay-serial',['node','scripts/replay-lab.mjs','--io-mode','serial','--output',str(output/'replay-serial.json')],site),('replay-batched',['node','scripts/replay-lab.mjs','--io-mode','batched','--output',str(output/'replay-batched.json')],site),('replay-context-control',['node','scripts/replay-lab.mjs','--io-mode','batched','--context-mode','per_event','--output',str(output/'replay-context-control.json')],site),('context-benchmark',['node','scripts/benchmark-context-batch.mjs','--rtt-ms','20','--repeats','3','--output',str(output/'context-benchmark.json')],site),('database-benchmark',['node','scripts/benchmark-provider-io.mjs','--rtt-ms','20','--repeats','3','--output',str(output/'database-benchmark.json')],site),('pinned-context',['python','scripts/verify-context.py'],ROOT),('frozen-baseline',['python','scripts/check-screen-reader-baseline.py'],ROOT)]
 results=[run(*job) for job in jobs]
 if args.live:
  live=output/'live-vision.json';ok=run('live-vision',['python','scripts/compare-json-stream.py','--live','--arms','stream','--manifest','fixtures/json-stream/manifest.json','--repeats','1','--output',str(live)])
  rows=json.loads(live.read_text(encoding='utf-8'))['records'] if live.exists() else []
  report['paid_model_calls']=len(rows);report['live_vision']={'expected':5,'observed':len(rows),'passed':sum(bool(r.get('passed')) for r in rows),'fixture_scope':'five synthetic local-carrier cases only'}
  results.append(ok and len(rows)==5 and all(r.get('passed') for r in rows))
 report['passed']=all(results);report['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'passed':report['passed'],'report':str(output/'report.json'),'paid_model_calls':report['paid_model_calls']}));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
