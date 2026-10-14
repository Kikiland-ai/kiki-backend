"""Bounded incremental UTF-8/JSON parsing; emit only whole identified findings."""
import codecs
import json
from contracts.lab_tracking import CriterionFinding, ActionFinding
from prototypes.lab_tracking.analysis import validate_result
from prototypes.lab_tracking.provider import AnalysisFailure
from prototypes.lab_tracking.procedure import PROCEDURES
from .decision import decision_summary

def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key]=value
    return result

class FindingParser:
    def __init__(self, checkpoint, decision_only=False):
        self.checkpoint=checkpoint
        self.fields={'criteria','action_findings','uncertainties'} | (set() if decision_only else {'summary'})
        self.decision_only=decision_only
        self.expected={'criteria':{c['id'] for c in checkpoint['completion_criteria']},
                       'action_findings':{a['id'] for a in PROCEDURES[checkpoint['id']]}}
        self.seen={key:set() for key in self.expected};self.keys=set();self.completed=set()
        self.decoder=json.JSONDecoder(object_pairs_hook=unique_object)
        self.utf8=codecs.getincrementaldecoder('utf-8')('strict')
        self.text='';self.pos=0;self.state='start';self.field=None;self.closed=False
    def feed(self, chunk):
        try:
            self.text+=self.utf8.decode(chunk)
            if len(self.text)>262144: raise ValueError('size')
            return self._parse()
        except (ValueError,UnicodeError) as error:
            raise AnalysisFailure('invalid_output') from error
    def _skip(self):
        while self.pos<len(self.text) and self.text[self.pos] in ' \r\n\t':self.pos+=1
    def _value(self):
        try:return self.decoder.raw_decode(self.text,self.pos)
        except json.JSONDecodeError:return None
    def _parse(self):
        events=[]
        while True:
            self._skip()
            if self.pos>=len(self.text):return events
            ch=self.text[self.pos]
            if self.state=='start':
                if ch!='{':raise ValueError('object required')
                self.pos+=1;self.state='key'
            elif self.state=='key':
                value=self._value()
                if value is None:return events
                key,end=value
                if key not in self.fields or key in self.keys:raise ValueError('field')
                self.field=key;self.keys.add(key);self.pos=end;self.state='colon'
            elif self.state=='colon':
                if ch!=':':raise ValueError('colon')
                self.pos+=1;self.state='array_start' if self.field in self.expected else 'value'
            elif self.state=='array_start':
                if ch!='[':raise ValueError('array required')
                self.pos+=1;self.state='row_or_end'
            elif self.state in ('row','row_or_end'):
                if ch==']' and self.state=='row_or_end':
                    if self.seen[self.field]!=self.expected[self.field]:raise ValueError('missing finding')
                    self.completed.add(self.field);self.pos+=1;self.state='field_delim';continue
                value=self._value()
                if value is None:return events
                row,end=value
                model=CriterionFinding if self.field=='criteria' else ActionFinding
                row=model.model_validate(row).model_dump()
                id_key='criterion_id' if self.field=='criteria' else 'action_id';identifier=row[id_key]
                if identifier not in self.expected[self.field] or identifier in self.seen[self.field] or (row['status']!='unknown' and not row['evidence'].strip()):raise ValueError('finding')
                self.seen[self.field].add(identifier);self.pos=end;self.state='row_delim'
                events.append({'type':'provisional_findings','field':self.field,'finding':row})
            elif self.state=='row_delim':
                if ch==',':self.pos+=1;self.state='row'
                elif ch==']':
                    if self.seen[self.field]!=self.expected[self.field]:raise ValueError('missing finding')
                    self.completed.add(self.field);self.pos+=1;self.state='field_delim'
                else:raise ValueError('array delimiter')
            elif self.state=='value':
                value=self._value()
                if value is None:return events
                data,end=value
                if self.field=='summary' and (not isinstance(data,str) or not data.strip() or len(data)>220):raise ValueError('summary')
                if self.field=='uncertainties' and (not isinstance(data,list) or len(data)>3 or any(not isinstance(x,str) or len(x)>150 for x in data)):raise ValueError('uncertainties')
                self.completed.add(self.field);self.pos=end;self.state='field_delim'
                events.append({'type':'field_ready','field':self.field})
            elif self.state=='field_delim':
                if ch==',':self.pos+=1;self.state='key'
                elif ch=='}':self.pos+=1;self.state='end';self.closed=True
                else:raise ValueError('object delimiter')
            else:raise ValueError('trailing content')
    def finish(self):
        try:
            self.text+=self.utf8.decode(b'',final=True);self._parse();self._skip()
            if not self.closed or self.pos!=len(self.text) or self.keys!=self.fields:raise ValueError('incomplete')
            value=self.decoder.decode(self.text)
            if self.decision_only:value['summary']=decision_summary(value)
            if self.seen['action_findings']!=self.expected['action_findings']:raise ValueError('missing actions')
            return validate_result(value,self.checkpoint)
        except (ValueError,UnicodeError) as error:raise AnalysisFailure('invalid_output') from error

class SSEDecoder:
    def __init__(self):self.utf8=codecs.getincrementaldecoder('utf-8')('strict');self.pending='';self.data=[];self.total=0
    def feed(self,chunk):
        self.total+=len(chunk)
        if self.total>2_000_000:raise AnalysisFailure('invalid_output')
        try:self.pending+=self.utf8.decode(chunk)
        except UnicodeError:raise AnalysisFailure('invalid_output') from None
        events=[]
        while '\n' in self.pending:
            line,self.pending=self.pending.split('\n',1);line=line.removesuffix('\r')
            if not line:
                if self.data:events.append('\n'.join(self.data));self.data=[]
            elif line.startswith('data:'):self.data.append(line[5:].removeprefix(' '))
            if sum(map(len,self.data))+len(self.pending)>131072:raise AnalysisFailure('invalid_output')
        return events
    def finish(self):
        try:self.pending+=self.utf8.decode(b'',final=True)
        except UnicodeError:raise AnalysisFailure('invalid_output') from None
        if self.pending.strip() or self.data:raise AnalysisFailure('incomplete_output')
