"""Full-ID findings first; tentative events precede a complete final observation."""
from contextvars import ContextVar
import json,time
from prototypes.lab_tracking.procedure import PROCEDURES, OBSERVER_VERSION
from prototypes.lab_tracking.analysis import GeminiAnalyzer, build_request, AnalysisFindings
from prototypes.lab_tracking.provider import AnalysisFailure
from .parser import FindingParser,SSEDecoder,unique_object
from .provider import StreamingProviderPool

STREAM_SINK=ContextVar('json_stream_sink',default=None)
SHORT_DECISION=ContextVar('json_short_decision',default=True)
PROMPT_VERSION='dsb-step-observer/v4-short-decision1'

def priority_request(pixels,checkpoint,state,model,decision_only=False):
    body=build_request(pixels,checkpoint,state,model)
    schema=body['generationConfig']['responseJsonSchema']
    order=('criteria','action_findings','uncertainties','summary')
    schema['properties']={k:schema['properties'][k] for k in order}
    schema['required']=list(order)
    schema['properties']['criteria']['minItems']=len(checkpoint['completion_criteria'])
    schema['properties']['action_findings']['minItems']=len(PROCEDURES[checkpoint['id']])
    body['systemInstruction']['parts'][0]['text']+='\nSerialize top-level JSON fields in this order: criteria, action_findings, uncertainties, summary. Put the complete authored checkpoint decision findings first, then complete action findings, then critical uncertainties, and the short visible summary last. Keep every ID, status and supporting evidence. Do not emit a completion claim or generate next-step instructions.\nOcclusion check is mandatory before any wire or receiver_structure match: inspect the ENTIRE path from the named source output to the named destination input. A foreground settings dialog, panel or other window covering ANY part of that path makes the connection UNKNOWN, even when both endpoints and line pieces on both sides are visible and appear aligned. Never mentally join separated line fragments through an opaque window. receiver_structure requires BOTH receiver input paths fully visible end-to-end. modulated-wire and local-wire must each be unknown when their own paths are partly covered. Expected circuit topology, aligned line pieces and block names are not visible connection evidence.'
    if decision_only:
        schema['properties'].pop('summary');schema['required'].remove('summary')
        body['systemInstruction']['parts'][0]['text']+='\nSHORT DECISION CONTRACT overrides the earlier summary/serialization instruction: return exactly criteria, action_findings, uncertainties, in that order, then close the JSON object and finish. Include EVERY authored criterion and action exactly once. Keep all decisive evidence and critical uncertainties, with concise factual evidence clauses. Do not generate a summary, explanation, teaching instruction, history or auxiliary text. The server derives display prose after the complete decision. A match is not a checkpoint completion claim.'
    return body

class JsonStreamingAnalyzer(GeminiAnalyzer):
    supports_stream=True
    def __init__(self,api_key=None,transport=None,model=None,io_mode=None):
        super().__init__(api_key,transport,model)
        self.provider=StreamingProviderPool(api_key=api_key,transport=transport,io_mode=io_mode)
    @property
    def prompt_version(self):
        from .drawing_context import DRAWING_RUN,PROMPT_VERSION as DRAWING_PROMPT_VERSION
        if DRAWING_RUN.get() is not None:return DRAWING_PROMPT_VERSION
        return (PROMPT_VERSION if SHORT_DECISION.get() else 'dsb-step-observer/v3-json-stream2') if STREAM_SINK.get() is not None else OBSERVER_VERSION
    async def analyze(self,pixels,checkpoint,state):
        sink=STREAM_SINK.get()
        from .drawing_context import DRAWING_RUN,MODEL_CONTRACT
        drawing_run=DRAWING_RUN.get()
        if drawing_run is not None and sink is None:raise AnalysisFailure('drawing_requires_stream_adapter')
        if sink is None:return await super().analyze(pixels,checkpoint,state)
        short=True if drawing_run is not None else SHORT_DECISION.get()
        started=time.monotonic();attempt=0;first_byte=None;first_finding=None;critical_ms=None;provider_stop_ms=None;drawing_ready_ms=None;validation_ms=None;provider_metrics={}
        await sink({'type':'admitted','state':state})
        admission=None
        async def reset():
            nonlocal attempt,first_byte,first_finding,critical_ms,provider_stop_ms,drawing_ready_ms
            attempt+=1
            first_byte=first_finding=critical_ms=None
            provider_stop_ms=drawing_ready_ms=None
            if attempt>1:await sink({'type':'attempt_reset','attempt':attempt})
        async def consume(response):
            nonlocal first_byte,first_finding,critical_ms,provider_stop_ms,drawing_ready_ms,validation_ms
            parser=FindingParser(checkpoint,decision_only=short,drawing_input=admission);sse=SSEDecoder();stopped=False;usage={};critical=False
            async for chunk in response.aiter_bytes():
                if first_byte is None:first_byte=round((time.monotonic()-started)*1000)
                pending=[]
                if hasattr(sink,'metrics'):sink.metrics['provider_chunks']=sink.metrics.get('provider_chunks',0)+1
                for data in sse.feed(chunk):
                    if data=='[DONE]':continue
                    try:raw=json.loads(data,object_pairs_hook=unique_object)
                    except ValueError:raise AnalysisFailure('invalid_output') from None
                    candidates=raw.get('candidates',[])
                    if len(candidates)>1:raise AnalysisFailure('invalid_output')
                    if candidates:
                        candidate=candidates[0]
                        parts=candidate.get('content',{}).get('parts',[])
                        text=''.join(p['text'] for p in parts if isinstance(p.get('text'),str) and not p.get('thought'))
                        if stopped and (text or candidate.get('finishReason')):raise AnalysisFailure('invalid_output')
                        for event in parser.feed(text.encode()):
                            if event['type']=='provisional_findings':
                                if first_finding is None:first_finding=round((time.monotonic()-started)*1000)
                                pending.append({**event,'attempt':attempt})
                        if not critical and {'criteria','action_findings','uncertainties'}<=parser.completed:
                            critical=True;critical_ms=round((time.monotonic()-started)*1000)
                            pending.append({'type':'critical_fields_ready','attempt':attempt})
                        if candidate.get('finishReason'):
                            if candidate['finishReason']!='STOP':raise AnalysisFailure('incomplete_output')
                            stopped=True
                            provider_stop_ms=round((time.monotonic()-started)*1000)
                        if drawing_ready_ms is None and 'screen_guidance' in parser.completed:
                            drawing_ready_ms=round((time.monotonic()-started)*1000)
                    if isinstance(raw.get('usageMetadata'),dict):usage=raw['usageMetadata']
                if hasattr(sink,'batch'):await sink.batch(pending)
                else:
                    for event in pending:await sink(event)
            sse.finish()
            if not stopped:raise AnalysisFailure('incomplete_output')
            validation_started=time.monotonic()
            result=parser.finish()
            validation_ms=round((time.monotonic()-validation_started)*1000)
            if drawing_run is not None:drawing_run.model=parser.drawing_result
            return result,usage
        try:
            if drawing_run is not None:admission=drawing_run.admission_for(pixels,checkpoint,state)
            body=priority_request(pixels,checkpoint,state,self.model,decision_only=short)
            if admission is not None:
                from .guidance import extend_request
                extend_request(body,checkpoint,[a['id'] for a in PROCEDURES[checkpoint['id']]],admission)
            request_prepared_ms=round((time.monotonic()-started)*1000)
            result,usage=await self.provider.stream(self.model,body,consume,reset,provider_metrics.update)
            counts={target:usage.get(source) if type(usage.get(source)) is int and usage[source]>=0 else None for target,source in {'input_tokens':'promptTokenCount','cached_tokens':'cachedContentTokenCount','thinking_tokens':'thoughtsTokenCount','output_tokens':'candidatesTokenCount','total_tokens':'totalTokenCount'}.items()}
            output=AnalysisFindings(result,{**provider_metrics,**{k:v for k,v in getattr(sink,'metrics',{}).items() if not k.startswith('context_delivery_')},**counts,'image_bytes':len(pixels),'request_text_characters':len(body['systemInstruction']['parts'][0]['text'])+len(body['contents'][0]['parts'][0]['text'])+len(json.dumps(body['generationConfig']['responseJsonSchema'])),'provider_ms':round((time.monotonic()-started)*1000),'decision_validated_ms':round((time.monotonic()-started)*1000),'first_byte_ms':first_byte,'first_finding_ms':first_finding,'critical_fields_ms':critical_ms,'provider_stop_ms':provider_stop_ms,'drawing_fields_ms':drawing_ready_ms,**({'validation_ms':validation_ms,'request_prepared_ms':request_prepared_ms,'drawing_tail_ms':round((time.monotonic()-started)*1000)-critical_ms if critical_ms is not None else None} if admission is not None else {}),'wire_format':MODEL_CONTRACT if admission is not None else 'lab-observer-decision/v1' if short else 'lab-observer-json-stream/v1','observer_prompt_version':self.prompt_version})
            if drawing_run is not None and drawing_run.trace:drawing_run.trace.emit('analysis_validated',**output.metrics)
            return output
        except AnalysisFailure as error:
            if drawing_run is not None:drawing_run.model=None
            if drawing_run is not None and drawing_run.trace:drawing_run.trace.emit('failed',reason=str(error),**getattr(error,'provider_metrics',{}))
            raise
        except (ValueError,TypeError,KeyError,IndexError):
            if drawing_run is not None:drawing_run.model=None
            if drawing_run is not None and drawing_run.trace:drawing_run.trace.emit('failed',reason='invalid_output')
            raise AnalysisFailure('invalid_output') from None
