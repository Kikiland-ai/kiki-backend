"""Free isolated producer v1 acceptance + repeatable trace artifact bundle."""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'work/evaluations/guidance-v1');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('GEMINI_API_KEY','GOOGLE_API_KEY'))}
    jobs=[('schema-parity',['python','scripts/sync-guidance-contracts.py','--check']),
          ('reference',['python','scripts/check-analysis-owned-guidance-contract.py']),
          ('python-producer',['python','-m','unittest','discover','-s','prototypes/json_stream/tests','-q']),
          ('worker-producer',['node','--test','prototypes/json_stream_site/scripts/test-guidance-producer.mjs']),
          ('paired-replay',['python','scripts/replay-guidance-producer.py','--pairs','10','--output',str(args.output)])]
    if args.full:jobs.append(('reader-regression',['python','scripts/run-screen-reader-evaluation.py','--output',str(args.output/'reader-regression')]))
    checks=[]
    for name,cmd in jobs:
        started=time.monotonic()
        try:
            completed=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
            code=completed.returncode;log=completed.stdout
        except subprocess.TimeoutExpired:code=124;log='Evaluation timed out.\n'
        (args.output/(name+'.log')).write_text(log)
        checks.append({'name':name,'returncode':code,'seconds':round(time.monotonic()-started,3),'log':name+'.log'})
        print(name+(': PASS' if code==0 else ': FAIL'),flush=True)
        if code:print(log[-12000:],flush=True)
    report={'schema':'guidance-producer-acceptance/v1','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':all(c['returncode']==0 for c in checks),'checks':checks,'paid_model_calls':0,'sample_kind':'offline_replay','site_deployed':False,'renderer_interoperability_verified':False,'paint_ack_verified':False}
    (args.output/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'report':str(args.output/'acceptance.json')}));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
