"""Prompt-design-engineering experiment: fixed rubric, examples-only revision."""
import argparse
import ast
import copy
import json
import os
from pathlib import Path
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prototypes.mixed_script.pipeline import (
    DEFAULT_INPUT, GeminiGenerator, PipelineError, digest, make_request,
    occurrences, read_json, run_pipeline, save_result, validate_input, validate_stage,
)

TREE=ast.parse(Path('work/trial-learner-language-profile-attempt3.py').read_text())
CONSTANTS={node.targets[0].id:ast.literal_eval(node.value) for node in TREE.body
           if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
           and node.targets[0].id in ('PROFILE','POLICY')}
PROFILE=CONSTANTS['PROFILE']
POLICY=CONSTANTS['POLICY']
COUNT_RULE=(
    'Respect protected_glossary_counts_by_sentence exactly, including zero counts. '
    'In s3 the carrier means the carrier SIGNAL; do not change it to carrier frequency. '
    'The phrase carrier frequency must appear only in s4. '
    'In s3 preserve instantaneous frequency once and amplitude once, alongside the '
    'ideal linear model qualification and unchanged equation. '
    'Do not add Odia duplicates of an already retained English phrase (e.g. direct). '
    'Perform a silent final check of each ID, phrase, glossary count, and language label.'
)
EXAMPLES='''# Hard examples — annotations, not extra source sentences
These examples illustrate the existing rules. Return only entries from the live original input.

## Correct overlap and spoken expansion
English: Here f_c is the carrier frequency, K_v is the VCO sensitivity in Hz/V, and m(t) is the message voltage.
Retain: VCO sensitivity; message voltage. Original VCO count: 1.
Correct sentence entry:
{"id":"s4","spans":[{"language":"or","text":"ଏଠାରେ "},{"language":"en","text":"f_c"},{"language":"or","text":" ହେଉଛି "},{"language":"en","text":"carrier frequency"},{"language":"or","text":", "},{"language":"en","text":"K_v"},{"language":"or","text":" ହେଉଛି "},{"language":"en","text":"VCO sensitivity"},{"language":"or","text":" "},{"language":"en","text":"Hz/V"},{"language":"or","text":" ରେ, ଏବଂ "},{"language":"en","text":"m(t)"},{"language":"or","text":" ହେଉଛି "},{"language":"en","text":"message voltage"},{"language":"or","text":"।"}],"speech_text":"ଏଠାରେ f c ହେଉଛି carrier frequency, K v ହେଉଛି V C O sensitivity hertz per volt ରେ, ଏବଂ m of t ହେଉଛି message voltage।"}
Why correct: VCO occurs once inside VCO sensitivity; no separate VCO is needed. The spoken version uses V C O once and expands each symbol/unit exactly.
Bad: "VCO ର VCO sensitivity" duplicates VCO. A speech_text containing "VCO sensitivity" without changing VCO to V C O misses the required spoken expansion.

## Incorrect script label
Bad span: {"language":"or","text":"ଗୋଟିଏ VCO"}
Why it fails: the Latin letters VCO are in an Odia-labelled span.
Correct spans: [{"language":"or","text":"ଗୋଟିଏ "},{"language":"en","text":"VCO"}]
Script labels describe the actual characters, including when an Odia suffix follows an English phrase. Split the suffix into an or span; preserve the text and spaces.

## Incorrect added scientific term
English: In an ideal linear model, f_i(t) = f_c + K_v m(t), so the carrier's instantaneous frequency varies while its amplitude remains constant.
Bad phrase: "carrier frequency ର instantaneous frequency"
Why it fails: carrier frequency has source count zero in this sentence and changes the carrier into its frequency.
Keep the carrier signal reference, ideal linear model qualification, unchanged equation, instantaneous frequency once, and amplitude once. Preserve the claim that amplitude remains constant.
'''
SPAN_RULE="""# Exact language field rule
The language label describes the actual script of every letter, not whether a word
is a protected technical term. Every Latin word, including ordinary helping words
and phrases such as the carrier, so, while, and remains constant, belongs in an en
span. Every Odia letter belongs in an or span. Whitespace and punctuation may
belong to either adjacent span. Split a clause at each script change while keeping
all words, spaces, and punctuation in their correct order.
For example, this span is invalid:
{"language":"or","text":", ତେଣୁ the carrier ର "}
Use these spans instead:
[{"language":"or","text":", ତେଣୁ "},{"language":"en","text":"the carrier"},{"language":"or","text":" ର "}]
Before returning, scan every or span for A-Z/a-z and move those words into en
spans; scan every en span for Odia letters and move those letters into or spans.
Keep the text itself unchanged during this final label check."""
ROOT=Path('work/prompt-hardening')
ROOT.mkdir(exist_ok=True)

def build_request(source,stage,translation=None,version='v0'):
    request=make_request(source,stage,translation)
    request['systemInstruction']['parts'].append({'text':POLICY})
    data=json.loads(request['contents'][0]['parts'][0]['text'])
    data['learner_language_profile']=PROFILE
    data['protected_glossary_counts_by_sentence']={
        s['id']:{t['english']:occurrences(s['english'],t['english']) for t in source['glossary']}
        for s in source['sentences']
    }
    request['systemInstruction']['parts'].append({'text':COUNT_RULE})
    if version in ('v1','v2'):request['systemInstruction']['parts'].append({'text':EXAMPLES})
    if version=='v2':request['systemInstruction']['parts'].append({'text':SPAN_RULE})
    request['contents'][0]['parts'][0]['text']=json.dumps(data,ensure_ascii=False)
    return request


def check_preferences(source,stage):
    checks=[]
    for original,candidate in zip(source['sentences'],stage['sentences']):
        for phrase in PROFILE['retain_english_phrases']:
            expected=occurrences(original['english'],phrase)
            spoken=phrase
            for term in source['glossary']:
                pattern=r'(?<![A-Za-z0-9_])'+re.escape(term['english'])+r'(?![A-Za-z0-9_])'
                spoken=re.sub(pattern,lambda _:term['spoken_en'],spoken)
            actual=occurrences(candidate['display_text'],phrase)
            actual_spoken=occurrences(candidate['speech_text'].casefold(),spoken.casefold())
            if actual!=expected or actual_spoken!=expected:
                raise PipelineError(f'Profile phrase mismatch: {original["id"]}: {phrase}')
            checks.append({'sentence_id':original['id'],'phrase':phrase,'count':expected,'passed':True})
    return checks


def count_diagnostics(source,raw):
    counts=[]
    for original,candidate in zip(source['sentences'],raw.get('sentences',[])):
        if not isinstance(candidate,dict):continue
        display=''.join(s.get('text','') for s in candidate.get('spans',[]) if isinstance(s,dict))
        speech=candidate.get('speech_text','')
        for term in source['glossary']:
            expected=occurrences(original['english'],term['english'])
            actual=occurrences(display,term['english'])
            spoken=occurrences(speech.casefold(),term['spoken_en'].casefold())
            if actual!=expected or spoken!=expected:
                counts.append({'sentence_id':original['id'],'term':term['english'],
                               'expected':expected,'display_count':actual,'speech_count':spoken})
    return counts


class TrialGenerator(GeminiGenerator):
    def __init__(self,source,version,run_id):
        super().__init__(os.environ.get('GEMINI_API_KEY',''),model='gemini-3.5-flash-lite')
        self.source,self.version,self.run_id=source,version,run_id
        self.phrase_checks=[]
        self.stage_metrics=[]
        self.last_stage=None
        self.count_errors=[]

    def generate(self,stage,request):
        self.last_stage=stage
        data=json.loads(request['contents'][0]['parts'][0]['text'])
        request=build_request(self.source,stage,data.get('draft_translation'),self.version)
        save_result(request,ROOT/f'{self.run_id}-{stage}.request.json')
        print('Request:',self.run_id,stage,flush=True)
        start=time.monotonic()
        try:
            generated=super().generate(stage,request)
        finally:
            self.stage_metrics.append({'stage':stage,'elapsed_seconds':round(time.monotonic()-start,3)})
        save_result({'response':generated,'call':self.calls[-1]},ROOT/f'{self.run_id}-{stage}.raw.json')
        self.count_errors=count_diagnostics(self.source,generated)
        checked=validate_stage(self.source,generated,validate_input(self.source))
        self.phrase_checks.extend({'stage':stage,**c} for c in check_preferences(self.source,checked))
        print('Passed raw validation:',self.run_id,stage,flush=True)
        return generated


def run_trial(case,version,run_id):
    path=ROOT/f'{run_id}.summary.json'
    if path.exists():raise SystemExit('Run already exists; preserved')
    source=read_json(DEFAULT_INPUT) if case=='vco' else read_json(ROOT/'heldout.input.json')
    generator=TrialGenerator(source,version,run_id)
    summary={'run_id':run_id,'case':case,'version':version,'model':generator.model,
             'raw_output_validation':True,'postprocessing':False,'semantic_review':'pending','native_Odia_review':'pending'}
    try:
        result=run_pipeline(source,generator)
        result['prompt_version']='learner-profile-fewshot/'+version
        result['language_profile']=PROFILE
        result['experiment']={'case':case,'run_id':run_id,'phrase_checks':generator.phrase_checks,
                              'postprocessing':False,'review_status':'pending'}
        save_result(result,ROOT/f'{run_id}.result.json')
        summary['outcome']='passed_all_automated_checks'
        print('PASS:',run_id,flush=True)
    except PipelineError as error:
        summary.update({'outcome':'failed','stage':generator.last_stage,'error':str(error),
                        'term_count_diagnostics':generator.count_errors})
        print('FAIL:',run_id,str(error),flush=True)
    summary.update({'calls':generator.calls,'stage_metrics':generator.stage_metrics})
    save_result(summary,path)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary


def prepare():
    source=read_json(DEFAULT_INPUT)
    original=read_json(Path('work/vco-profile-en5-or7-attempt3-translation.raw.json'))
    assert digest(build_request(source,'translation',version='v0'))==original['call']['request_sha256']
    for version in ('v0','v1'):
        request=build_request(source,'translation',version=version)
        save_result(request,ROOT/f'{version}-translation.template.json')
        with (ROOT/f'{version}-system-prompt.txt').open('x',encoding='utf-8') as f:
            f.write('\n\n'.join(p['text'] for p in request['systemInstruction']['parts'])+'\n')
    heldout=copy.deepcopy(source)
    heldout['id']='heldout-values-negation'
    heldout['title']='Synthetic evaluation: values and limits of an ideal assumption'
    heldout['sentences']=[
        {'id':'h1','english':'At a control voltage of 0.7 V, the VCO has an output frequency of 1000 Hz in this illustrative example.',
         'term_ids':['t-vco','t-frequency','t-control'],
         'literals':[{'text':'0.7 V','spoken':'zero point seven volts'},{'text':'1000 Hz','spoken':'one thousand hertz'}]},
        {'id':'h2','english':'A change in control voltage does not by itself establish that the amplitude remains constant in a real VCO.',
         'term_ids':['t-vco','t-control','t-amplitude'],'literals':[]},
    ]
    validate_input(heldout)
    save_result(heldout,ROOT/'heldout.input.json')
    fixture=read_json(Path('fixtures/mixed-script/vco.generated.fixture.json'))
    negative=copy.deepcopy(fixture['mixed'])
    extra=' This always holds in every real circuit.'
    negative['sentences'][2]['spans'].append({'language':'en','text':extra})
    negative['sentences'][2]['speech_text']+=extra
    validate_stage(source,negative,validate_input(source))
    save_result({'label':'intentionally unsupported synthetic negative control; not usable content',
                 'added_claim':extra,'automated_preservation_validator':'passed',
                 'meaning_review':'fails source grounding; human review required',
                 'candidate':negative},ROOT/'semantic-negative-control.json')
    print('Prior v0 request digest matched: PASS')
    print('Prepared v0/v1 copies, untouched held-out input, and semantic negative control')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','run'])
    parser.add_argument('--case',choices=['vco','heldout'],default='vco')
    parser.add_argument('--version',choices=['v0','v1','v2'],default='v1')
    parser.add_argument('--run-id')
    args=parser.parse_args()
    if args.command=='prepare':prepare()
    else:
        if not args.run_id:parser.error('--run-id is required')
        run_trial(args.case,args.version,args.run_id)
