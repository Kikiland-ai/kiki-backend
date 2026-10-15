"""Summarize transparent JSONL logs. Never infer live latency from offline replay."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from statistics import median

def summarize(rows):
    requests={}
    for row in rows:
        if row.get('schema')!='guidance-producer-timing/v1':raise ValueError('unknown_log_contract')
        key=(row['runtime'],row['configuration_id'],row['sample_kind'],row['model'],row['arm'],row.get('run_id','legacy-unspecified'),row['request_id'])
        state=requests.setdefault(key,{'stages':[],'pair_id':row['pair_id']})
        state['stages'].append(row['stage'])
        for k,v in row.items():
            if k not in ('stage','elapsed_ms','reason'):state[k]=v
        state['outcome']=row['stage'];state['reason']=row['reason'];state['terminal_elapsed_ms']=row['elapsed_ms']
    groups={}
    for key,r in requests.items():
        group=groups.setdefault(key[:5],[]);group.append(r)
    result=[]
    measures=['terminal_elapsed_ms','first_finding_ms','critical_fields_ms','drawing_fields_ms','provider_stop_ms','decision_validated_ms','commit_finished_ms','publication_ms','packet_prepared_ms','request_prepared_ms','validation_ms','drawing_tail_ms','frame_age_at_commit_ms','screen_guidance_bytes','provider_db_operations','provider_db_ms','provider_http_attempts','provider_http_ms','context_db_reads','context_db_ms','input_tokens','output_tokens','request_text_characters','image_bytes']
    for key,samples in groups.items():
        metrics={}
        for field in measures:
            values=sorted(r[field] for r in samples if type(r.get(field)) in (int,float) and math.isfinite(r[field]))
            metrics[field]={'n':len(values),'median':median(values) if values else None,'p95':values[max(0,math.ceil(len(values)*.95)-1)] if values else None}
        result.append({'runtime':key[0],'configuration_id':key[1],'sample_kind':key[2],'model':key[3],'arm':key[4],
                       'requests':len(samples),'outcomes':dict(Counter(r['outcome'] for r in samples)),
                       'reasons':dict(Counter(r['reason'] for r in samples)),
                       'source_revisions':sorted({r['source_revision'] for r in samples}),'metrics':metrics})
    pairs={}
    for key,r in requests.items():pairs.setdefault((*key[:4],r.get('run_id','legacy-unspecified'),r['pair_id']),set()).add(key[4])
    return {'schema':'guidance-producer-comparison/v1','groups':result,
            'paired_cases':sum(v=={'control','drawing_v1'} for v in pairs.values()),
            'unpaired_cases':sum(v!={'control','drawing_v1'} for v in pairs.values()),
            'limitations':['Offline replay measures parser/tracker/projection overhead only; provider generation, network, Site delivery and paint are not measured.',
                          'Each metric retains its own denominator; failed/discarded requests remain in outcome counts. Token counts are null unless reported by the provider.',
                          'Compare matching configuration/runtime/sample/model groups. Paired IDs identify cases, not randomized real-user trials. Rendering never supplies checkpoint evidence.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('logs',nargs='+',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    rows=[json.loads(line) for p in args.logs for line in p.read_text().splitlines() if line.strip()]
    value=json.dumps(summarize(rows),indent=2)
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(value+'\n')
    print(value)
