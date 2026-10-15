"""Opt-in drawing producer v1. No routes, renderer, model retry or progress policy.

Trusted input/runtime are supplied by an authenticated integration adapter. Sequence
allocation and publication must share its durable CAS transaction; these pure helpers
never claim persistence or live capability. No model text is logged.
"""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource
from PIL import Image
from prototypes.lab_tracking.provider import AnalysisFailure

ROOT = Path(__file__).resolve().parents[2]
from .drawing_context import MODEL_CONTRACT, PROMPT_VERSION, DRAWING_RUN
SOURCE_KEYS = ('lab_session_id', 'experiment_id', 'workspace_id', 'capture_epoch',
               'view_revision', 'parameter_revision', 'condition')
SCHEMA = json.loads((ROOT/'contracts/lab_observer_drawing.v1.schema.json').read_text())
BUNDLE = json.loads((ROOT/'contracts/analysis_owned_guidance.v0_1.schema.json').read_text())
LEGACY = json.loads((ROOT/'contracts/screen_writing.schema.json').read_text())
REGISTRY = Registry().with_resource(LEGACY['$id'], Resource.from_contents(LEGACY))
MODEL_VALIDATOR = Draft202012Validator(SCHEMA, registry=REGISTRY, format_checker=FormatChecker())
BUNDLE_VALIDATOR = Draft202012Validator(BUNDLE, registry=REGISTRY, format_checker=FormatChecker())


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.utcoffset() == timedelta(0), 'server_utc_required')
    return result


def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def ids(rows, key):
    result = [row[key] for row in rows]
    require(len(result) == len(set(result)), 'duplicate_'+key)
    return set(result)


def strict_decoder():
    from .parser import unique_object
    def finite(value):
        parsed = float(value)
        require(math.isfinite(parsed), 'nonfinite_number')
        return parsed
    def invalid(value):
        raise ValueError('nonfinite_number')
    return json.JSONDecoder(object_pairs_hook=unique_object, parse_float=finite, parse_constant=invalid)


def validate_input(admission, pixels, checkpoint, state_context):
    try:
        BUNDLE_VALIDATOR.validate(admission)
    except ValidationError as error:
        raise ValueError('invalid_admission_schema') from error
    require(admission['message_type'] == 'analysis_input', 'wrong_input_type')
    require(admission['admitted_context'] == state_context, 'foreign_admission_context')
    require(checkpoint['id'] == state_context['checkpoint_id'], 'foreign_checkpoint')
    actions = admission['eligible_actions']
    ids(actions, 'action_id')
    require(actions[0]['action_id'] == admission['current_action_id'], 'input_action_order')
    require(actions[0]['checkpoint_id'] == checkpoint['id'], 'foreign_current_checkpoint')
    for action in actions:
        targets = action['required_target_ids']
        require(len(set(targets)) == len(targets), 'duplicate_required_target')
        require(set(action['target_labels']) == set(targets) == set(action['subcriteria']), 'target_catalogue_mismatch')
        ids(action['relationships'], 'relationship_id')
        require(all(r['from_target_id'] in targets and r['to_target_id'] in targets for r in action['relationships']), 'foreign_relationship_target')
        # Check instruction/labels against the unchanged packet bounds at admission.
        require(len(action['canonical_instruction']) <= 1000, 'canonical_instruction_too_long')
        require(all(len(x) <= 160 for x in action['overlay_texts'].values()), 'overlay_text_too_long')
    frame = admission['frame']
    require(frame['view_revision'] == state_context['view_revision'], 'foreign_frame_view')
    require(len(pixels) == frame['byte_count'] and hashlib.sha256(pixels).hexdigest() == frame['sha256'], 'foreign_frame_pixels')
    with Image.open(io.BytesIO(pixels)) as image:
        require(image.format == 'JPEG' and image.size == (frame['encoded_width'], frame['encoded_height']), 'foreign_frame_dimensions')
    require(instant(frame['received_at']) <= instant(frame['admitted_at']) < instant(admission['frame_handle']['expires_at']), 'invalid_admission_clock')
    return deepcopy(admission)


def validate_model(value, admission, checkpoint, action_ids):
    try:
        MODEL_VALIDATOR.validate(value)
    except ValidationError as error:
        raise ValueError('invalid_drawing_schema') from error
    require(ids(value['criteria'], 'criterion_id') == {c['id'] for c in checkpoint['completion_criteria']}, 'foreign_or_missing_criteria')
    require(ids(value['action_findings'], 'action_id') == set(action_ids), 'foreign_or_missing_findings')
    require(all(len(r['evidence']) <= 180 and (r['status'] == 'unknown' or r['evidence'].strip()) for r in value['criteria']+value['action_findings']), 'invalid_evidence')
    ids(value['screen_guidance'], 'action_id')
    catalogue = {a['action_id']: a for a in admission['eligible_actions']}
    for candidate in value['screen_guidance']:
        require(candidate['action_id'] in catalogue, 'ineligible_action')
        action = catalogue[candidate['action_id']]
        ids(candidate['targets'], 'target_id'); ids(candidate['marks'], 'cue_id')
        if candidate['mode'] == 'none':
            continue
        require({t['target_id'] for t in candidate['targets']} == set(action['required_target_ids']), 'foreign_or_missing_targets')
        for target in candidate['targets']:
            region = target['region']
            if region is not None:
                require(region['x']+region['width'] <= 1 and region['y']+region['height'] <= 1, 'out_of_frame_region')
        for mark in candidate['marks']:
            refs = ([mark['target_id']] if mark['kind'] in ('box', 'ellipse') else
                    [mark['anchor']['target_id']] if mark['kind'] == 'text' else
                    [mark['from']['target_id'], mark['to']['target_id']])
            require(set(refs) <= set(action['required_target_ids']), 'unrelated_operation_target')
            if mark['kind'] == 'text':
                require(mark['text_ref'] in action['overlay_texts'], 'foreign_text_reference')
            if mark['kind'] == 'arrow':
                rel = next((r for r in action['relationships'] if r['relationship_id'] == mark['relationship_id']), None)
                require(rel is not None and refs == [rel['from_target_id'], rel['to_target_id']], 'foreign_relationship')
    return value


def provider_schema(checkpoint, actions, admission):
    """Compile only provider-supported structural keywords; final schema stays strict."""
    def compile_schema(node):
        if isinstance(node, list):
            return [compile_schema(v) for v in node]
        if not isinstance(node, dict):
            return node
        if '$ref' in node:
            urn, pointer = node['$ref'].split('#', 1)
            require(urn == LEGACY['$id'], 'unsupported_schema_reference')
            source = LEGACY
            for part in pointer.lstrip('/').split('/'):
                source = source[part]
            return compile_schema(source)
        allowed = {'type', 'properties', 'required', 'additionalProperties', 'items', 'minItems', 'maxItems',
                   'minimum', 'maximum', 'minLength', 'maxLength', 'enum', 'oneOf'}
        out = {}
        for key, val in node.items():
            if key == 'properties':
                out[key] = {k: compile_schema(v) for k, v in val.items()}
            elif key == 'const':
                out['enum'] = [val]
            elif key == 'oneOf':
                out['anyOf'] = compile_schema(val)
            elif key == 'exclusiveMinimum':
                out['minimum'] = val  # full validator enforces the exclusive bound
            elif key in allowed:
                out[key] = compile_schema(val)
        return out
    result = compile_schema(SCHEMA)
    for key, name, values in [('criteria', 'criterion_id', [c['id'] for c in checkpoint['completion_criteria']]),
                               ('action_findings', 'action_id', actions)]:
        row = result['properties'][key]
        row['minItems'] = row['maxItems'] = len(values)
        row['items']['properties'][name]['enum'] = values
        row['items']['properties']['evidence']['maxLength'] = 180
    candidate = result['properties']['screen_guidance']['items']
    candidate['properties']['action_id']['enum'] = [a['action_id'] for a in admission['eligible_actions']]
    target_ids = sorted({t for a in admission['eligible_actions'] for t in a['required_target_ids']})
    def scope_targets(node):
        if isinstance(node, dict):
            if 'target_id' in node.get('properties', {}):node['properties']['target_id']['enum'] = target_ids
            for child in node.values():scope_targets(child)
        elif isinstance(node, list):
            for child in node:scope_targets(child)
    scope_targets(candidate)
    return result


DRAWING_PROMPT = '''\nDRAWING CONTRACT lab-observer-drawing/v1 overrides the earlier three-field close instruction. Return exactly criteria, action_findings, uncertainties, screen_guidance in that order, then finish. Keep every authored finding ID exactly once. screen_guidance has at most two distinct eligible action candidates. Do not choose or complete a lab step. For each offered action, locate ALL its required stable target IDs in this exact image; similar controls in different blocks are different targets. Use normalized encoded-frame rectangles. If any required target is unreadable/ambiguous, use text_only with every target and no marks; if inappropriate, omit the candidate or use none with empty targets/marks. annotate requires every target resolved and 1-4 typed marks. No more than two targets. Box/ellipse reference a target; arrows reference the authored relationship and target-relative endpoints (u,v); text uses an authored text_ref and target-relative anchor. Do not invent instructions, labels, frame metadata, clocks, URLs, HTML, SVG or code. Occluded paths remain unknown. Drawing is a proposal for deterministic rendering, never checkpoint evidence.'''


def extend_request(body, checkpoint, actions, admission):
    # Remove superseded serialization prose only in this explicit new-contract arm.
    text=body['systemInstruction']['parts'][0]['text'].split('\nSHORT DECISION CONTRACT',1)[0]
    prefix='\nSerialize top-level JSON fields in this order:'
    if prefix in text:
        before,tail=text.split(prefix,1)
        text=before+'\nOcclusion check'+tail.split('\nOcclusion check',1)[1]
    body['systemInstruction']['parts'][0]['text']=text
    body['generationConfig']['responseJsonSchema'] = provider_schema(checkpoint, actions, admission)
    body['systemInstruction']['parts'][0]['text'] += DRAWING_PROMPT
    body['contents'][0]['parts'][0]['text'] += '\nAuthored drawing catalogue: '+json.dumps(admission['eligible_actions'], separators=(',', ':'))
    return body


class DrawingRun:
    """One request-scoped run; never share this instance across requests/retries."""
    def __init__(self, admit, trace=None):
        self.admit = admit
        self.trace = trace
        self.admission = None
        self.used = False
        self.model = None

    def admission_for(self, pixels, checkpoint, state):
        require(not self.used, 'drawing_run_reused')
        self.used = True
        from prototypes.lab_tracking.service import LabService
        context = LabService.context(None, state)
        self.admission = validate_input(self.admit(pixels, checkpoint, deepcopy(state)), pixels, checkpoint, context)
        if self.trace:self.trace.emit('admitted', image_bytes=len(pixels))
        return self.admission


def build_committed(admission, model, runtime):
    """Pure post-tracker projection. Caller must CAS sequence+publish against context.

    runtime is trusted current state, NEVER the model or request body. Live rendering
    still requires renderer final source/transform checks immediately before paint.
    """
    require(runtime['session_status'] == 'active' and runtime['observation_status'] == 'available', 'inactive_context')
    context = runtime['current_context']
    validate_model(model, admission, {'completion_criteria':[{'id':i} for i in runtime['expected_criterion_ids']]}, runtime['expected_action_ids'])
    require(runtime['admitted_context'] == admission['admitted_context'], 'foreign_admission')
    require(all(context[k] == admission['admitted_context'][k] for k in SOURCE_KEYS), 'stale_source_context')
    require(context['lab_revision'] > admission['admitted_context']['lab_revision'], 'uncommitted_revision')
    if context['checkpoint_id'] == admission['admitted_context']['checkpoint_id']:
        require(context['visit_id'] == admission['admitted_context']['visit_id'], 'stale_visit')
    require(runtime['analysis_request_id'] == admission['analysis_request_id'], 'foreign_request')
    require(runtime['frame'] == admission['frame'] and runtime['frame_handle'] == admission['frame_handle'] and runtime['source_binding'] == admission['source_binding'], 'foreign_frame_provenance')
    require(type(runtime['cue_sequence']) is int and runtime['cue_sequence'] > runtime['last_cue_sequence'], 'older_or_cancelled_sequence')
    action = next((a for a in admission['eligible_actions'] if a['action_id'] == runtime['current_action_id']), None)
    require(action is not None and action['checkpoint_id'] == context['checkpoint_id'], 'unoffered_current_action')
    # Canonical strings must still agree with tracker at the point of commit.
    require(runtime['canonical_instruction'] == action['canonical_instruction'], 'changed_canonical_instruction')
    created = instant(runtime['now'])
    received = instant(admission['frame']['received_at'])
    require(received <= instant(admission['frame']['admitted_at']) <= created, 'invalid_commit_clock')
    expires = min(created+timedelta(seconds=8), received+timedelta(seconds=20), instant(admission['frame_handle']['expires_at']))
    require(created < expires, 'expired_frame')
    selected = next((c for c in model['screen_guidance'] if c['action_id'] == action['action_id']), None)
    mode = selected['mode'] if selected else 'none'
    reason = ('model_declined' if selected else 'no_matching_candidate') if mode == 'none' else 'unresolved_required_target' if mode == 'text_only' else 'none'
    value = {'schema':'analysis-owned-guidance/v0.1', 'message_type':'committed_guidance',
             'model_contract':MODEL_CONTRACT, 'stream_contract':'lab-analysis-stream/v3', 'projection_contract':'committed-decision/v2',
             'analysis_request_id':admission['analysis_request_id'], 'guidance_stream_id':runtime['guidance_stream_id'], 'cue_sequence':runtime['cue_sequence'],
             'context':deepcopy(context), 'admitted_context':deepcopy(admission['admitted_context']), 'action_id':action['action_id'],
             **{k:deepcopy(admission[k]) for k in ('frame','frame_handle','source_binding')},
             'replacement':'replace_complete_guidance_layer', 'validity':{'created_at':stamp(created),'expires_at':stamp(expires),'max_frame_age_ms':20000},
             'outcome':mode,'reason':reason,'teaching_intent':action['teaching_intent'],'target_criteria':[], 'text_bindings':[], 'packet':None}
    if mode != 'none':
        binding = admission['source_binding']; live = binding['surface'] == 'live_workspace'
        if live:
            require(type(binding['transform_revision']) is int and binding['transform_revision'] > 0, 'unverified_live_binding')
            proof = runtime.get('trusted_live_bindings', {}).get(binding['binding_id'])
            require(isinstance(proof, dict) and proof.get('owner_id') == runtime['owner_id'] and
                    proof.get('binding_revision') == binding['binding_revision'] and proof.get('transform_revision') == binding['transform_revision'] and
                    proof.get('verified_frame') == admission['frame'] and proof.get('proof_kind') == 'native_capture_handle_and_pixel_match', 'unverified_live_binding')
        operations = []
        for mark in selected['marks']:
            operation = deepcopy(mark)
            if mark['kind'] == 'arrow':
                rel = next(r for r in action['relationships'] if r['relationship_id'] == mark['relationship_id'])
                label = {'compares_with':'Compare the indicated targets.', 'connects_to':'Connect the indicated targets.', 'influences':'Show the indicated relationship.'}[rel['kind']]
            else:
                label = action['target_labels'][mark['target_id'] if mark['kind'] in ('box','ellipse') else mark['anchor']['target_id']]
            operation.update(meaning='lab', accessible_label=label)
            if mark['kind'] == 'text':
                operation['text'] = action['overlay_texts'][operation.pop('text_ref')]
                value['text_bindings'].append({'cue_id':mark['cue_id'],'text_ref':mark['text_ref']})
            operations.append(operation)
        value['target_criteria'] = [{'target_id':t,'criterion_ids':action['subcriteria'][t]} for t in action['required_target_ids']]
        packet_id = runtime.get('packet_id') or str(uuid4())
        require(packet_id not in runtime.get('seen_packet_ids', []), 'duplicate_packet_id')
        value['packet'] = {'schema':'screen-writing/v0.2','message_type':'resolved_packet','packet_id':packet_id,
                           'request_id':admission['analysis_request_id'],'guidance_stream_id':runtime['guidance_stream_id'],'cue_sequence':runtime['cue_sequence'],
                           'context':deepcopy(context),'frame':deepcopy(admission['frame']),
                           'resolved_targets':[{**deepcopy(t),'method':'model_vision','reason':'Located in the admitted analysis frame.' if t['status']=='resolved' else 'Required target is not established in the admitted frame.'} for t in selected['targets']],
                           'relationships':deepcopy(action['relationships']),'operations':operations,'replacement':value['replacement'],
                           'delivery':{'surface':binding['surface'],'coordinate_space':'normalized_encoded_frame','adapter_binding_id':binding['binding_id'] if live else None,
                                       'transform_revision':binding['transform_revision'] if live else None,'pointer_events':'none','clip_to_frame':True},
                           'validity':deepcopy(value['validity']),'fallback':{'instruction':action['canonical_instruction'],'reason':reason}}
    BUNDLE_VALIDATOR.validate(value)
    require(len(json.dumps(value).encode()) <= 32768, 'oversized_payload')
    return value


def committed_state(state, packet):
    from .decision import committed_projection
    value = committed_projection(state)
    value['projection'] = 'committed-decision/v2'
    value['screen_guidance'] = deepcopy(packet)
    return value
