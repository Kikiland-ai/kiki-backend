// Hosted adapter: receive pixels, return the actual bytes, sign receipt metadata.
// No raw images or full recordings are persisted by this Worker.
const LIMIT = 1000000;
const enc = new TextEncoder();
const dec = new TextDecoder();
const COOKIE = 'kiki_capture_receipt';
const ANALYSIS_COOKIE = 'kiki_analysis_receipt';
const base64 = bytes => btoa(String.fromCharCode(...bytes));
const unbase64 = text => Uint8Array.from(atob(text), c => c.charCodeAt(0));
const hex = bytes => [...bytes].map(v => v.toString(16).padStart(2, '0')).join('');
const fail = (status, detail, extra = {}) => { throw {status, detail, ...extra}; };

function response(body, status = 200, headers = {}) {
  return new Response(body, {status, headers: {
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'same-origin', ...headers,
  }});
}
const json = (value, status = 200, headers = {}) => response(JSON.stringify(value), status,
  {'Content-Type': 'application/json; charset=utf-8', ...headers});

async function key(env) {
  if (!env.CAPTURE_RECEIPT_KEY) fail(503, 'Receiver signing configuration is missing.');
  return crypto.subtle.importKey('raw', enc.encode(env.CAPTURE_RECEIPT_KEY),
    {name: 'HMAC', hash: 'SHA-256'}, false, ['sign', 'verify']);
}
async function sign(state, env) {
  const payload = enc.encode(JSON.stringify(state));
  const signature = new Uint8Array(await crypto.subtle.sign('HMAC', await key(env), payload));
  return base64(payload) + '.' + base64(signature);
}
async function readState(request, env, id, owner) {
  const cookie = (request.headers.get('cookie') || '').split(';').map(s => s.trim())
    .find(s => s.startsWith(COOKIE + '='));
  if (!cookie) fail(401, 'Start a new screen-sharing session.');
  try {
    const [payload, signature] = cookie.slice(COOKIE.length + 1).split('.');
    const bytes = unbase64(payload);
    if (bytes.length > 3000 || !await crypto.subtle.verify('HMAC', await key(env), unbase64(signature), bytes)) fail(401, 'Invalid receipt.');
    const state = JSON.parse(dec.decode(bytes));
    if (state.id !== id || state.owner !== owner) fail(404, 'Session not found.');
    return state;
  } catch (error) {
    if (error.status) throw error;
    fail(401, 'Invalid receipt. Start a new share.');
  }
}
async function receiptHeaders(state, env) {
  const receipt = await sign(state, env);
  return {
    'Set-Cookie': `${COOKIE}=${receipt}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Strict`,
    'X-Capture-Receipt': receipt,
    'X-Capture-Observation': base64(enc.encode(JSON.stringify(snapshot(state)))),
  };
}
async function analysisState(request, env, capture) {
  const cookie=(request.headers.get('cookie') || '').split(';').map(s=>s.trim()).find(s=>s.startsWith(ANALYSIS_COOKIE+'='));
  if (cookie) {
    try {
      const [payload, signature]=cookie.slice(ANALYSIS_COOKIE.length+1).split('.');
      const bytes=unbase64(payload);
      if (bytes.length<=3000 && await crypto.subtle.verify('HMAC',await key(env),unbase64(signature),bytes)) {
        const value=JSON.parse(dec.decode(bytes));
        if(value.kind==='analysis' && value.id===capture.id && value.owner===capture.owner) return value;
      }
    } catch {}
  }
  return {kind:'analysis',id:capture.id,owner:capture.owner,attempts:0,last_started:0,status:providerConfigured(env) ? 'awaiting_first_analysis' : 'not_enabled',last:null};
}
async function analysisHeaders(state, env) {
  const receipt=await sign(state,env);
  if(receipt.length>3900) fail(422,'Analysis exceeds the receipt size limit.');
  return {'Set-Cookie':`${ANALYSIS_COOKIE}=${receipt}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Strict`};
}
function snapshot(state, analysis=null) {
  const age = state.latest ? Date.now() - state.latest.server_received_unix_ms : null;
  const last=analysis?.last;
  return {schema: last ? 'screen-awareness/v1' : 'screen-receiver/v1', session_id: state.id, capture_epoch: 1,
    capture_status: state.status, received_frame_count: state.count,
    observation: last ? {mode:'vision_observation', analysis_status:analysis.status, ...last,
      latest_frame:state.latest} : state.latest ? {mode: 'frame_receipt', analysis_status: analysis?.status || 'not_enabled',
      summary: null, latest_frame: state.latest} : null,
    analysis: analysis ? {status:analysis.status,attempts:analysis.attempts,max_attempts:null,retry_at_ms:analysis.retry_at_ms||null,retry_after_ms:Math.max(0,(analysis.retry_at_ms||0)-Date.now()),error:analysis.error || null,
      last_analyzed_frame_id:last?.source_frame.frame_id || null,
      age_ms:last ? Date.now()-last.source_frame.server_received_unix_ms : null,
      stale:!last || Date.now()-last.source_frame.server_received_unix_ms>20000,
      minimum_interval_ms:10000} : null,
    freshness: {received_age_ms: age, stale: age === null || age > 10000},
    evidence: {retention: 'returned_to_browser_only', server_image_archive: false},
    last_event_sequence: state.revision};
}
function metadata(text) {
  if (!text || text.length > 2000) fail(422, 'Frame metadata missing or oversized.');
  let m;
  try { m = JSON.parse(text); } catch { fail(422, 'Invalid frame metadata.'); }
  const limits = {sequence: [1, Number.MAX_SAFE_INTEGER], capture_epoch: [1, 1], captured_elapsed_ms: [0, Number.MAX_SAFE_INTEGER],
    width: [1, 1600], height: [1, 1600], view_revision: [1, Number.MAX_SAFE_INTEGER], source_width: [1, 16384], source_height: [1, 16384],
    byte_count: [1, LIMIT]};
  if (!m || typeof m !== 'object' || Array.isArray(m)) fail(422, 'Invalid metadata.');
  const allowed = new Set(['type', 'mime_type', ...Object.keys(limits)]);
  if (Object.keys(m).some(k => !allowed.has(k)) || m.type !== 'frame' || m.mime_type !== 'image/jpeg') fail(422, 'Unsupported frame format.');
  for (const [name, [low, high]] of Object.entries(limits)) {
    if (!Number.isInteger(m[name]) || m[name] < low || m[name] > high) fail(422, 'Frame metadata is out of bounds.');
  }
  if (Math.abs(m.width / m.height - m.source_width / m.source_height) > .02) fail(422, 'Frame aspect ratio mismatch.');
  return m;
}
function jpegDimensions(bytes) {
  if (bytes.length < 10 || bytes[0] !== 255 || bytes[1] !== 216 || bytes.at(-2) !== 255 || bytes.at(-1) !== 217) fail(422, 'Expected a complete JPEG.');
  let offset = 2;
  while (offset + 4 < bytes.length) {
    if (bytes[offset++] !== 255) fail(422, 'Invalid JPEG marker.');
    while (bytes[offset] === 255) offset++;
    const marker = bytes[offset++];
    if (marker === 218 || marker === 217) break;
    if (marker === 1 || marker >= 208 && marker <= 215) continue;
    const length = bytes[offset] * 256 + bytes[offset + 1];
    if (length < 2 || offset + length > bytes.length) fail(422, 'Truncated JPEG.');
    if ([192, 193, 194].includes(marker)) {
      if (length < 8) fail(422, 'Invalid JPEG dimensions.');
      return {height: bytes[offset + 3] * 256 + bytes[offset + 4], width: bytes[offset + 5] * 256 + bytes[offset + 6]};
    }
    offset += length;
  }
  fail(422, 'JPEG dimensions unavailable.');
}
async function boundedImage(request) {
  if (request.headers.get('content-type')?.split(';')[0] !== 'image/jpeg') fail(415, 'Expected image/jpeg.');
  if (Number(request.headers.get('content-length')) > LIMIT) fail(413, 'Frame exceeds 1 MB.');
  if (!request.body) fail(422, 'Missing frame.');
  const reader = request.body.getReader();
  const chunks = []; let length = 0;
  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    length += value.length;
    if (length > LIMIT) { await reader.cancel(); fail(413, 'Frame exceeds 1 MB.'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return bytes;
}

export default {
  async fetch(request, env, executionContext) {
    try {
      const url = new URL(request.url);
      // Enable only after a verified Python deployment; unset keeps the earlier demo.
      if(env.KIKI_FASTAPI_ORIGIN)return await pythonProxy(request,env);
      if (request.method === 'GET' && url.pathname === '/') return response(ASSETS.html, 200, {'Content-Type': 'text/html; charset=utf-8'});
      if (request.method === 'GET' && url.pathname === '/static/style.css') return response(ASSETS.css, 200, {'Content-Type': 'text/css'});
      if (request.method === 'GET' && url.pathname === '/static/capture.js') return response(ASSETS.js, 200, {'Content-Type': 'application/javascript'});
      if(request.method==='GET' && url.pathname==='/static/lab-cadence.js') return response(ASSETS.labcadence,200,{'Content-Type':'application/javascript'});
      if(request.method==='GET' && url.pathname==='/static/json-stream-client.js')return response(ASSETS.streamclient,200,{'Content-Type':'application/javascript'});
      if(request.method==='GET' && url.pathname==='/static/lab.js') return response(ASSETS.labjs,200,{'Content-Type':'application/javascript'});
      if(request.method==='GET' && url.pathname==='/static/floating-guidance.js') return response(ASSETS.floatingguidance,200,{'Content-Type':'application/javascript'});
      if(request.method==='GET' && url.pathname==='/static/floating-bridge.js') return response(ASSETS.floatingbridge,200,{'Content-Type':'application/javascript'});
      if (request.method === 'GET' && url.pathname === '/health') {
        let keys=[],configuration_valid=true;try{keys=providerKeys(env);}catch{configuration_valid=false;}
        return json({latency_experiment:{id:'stream-context-batch/v1',provider_io_mode:env.KIKI_PROVIDER_IO||'batched',context_validation_mode:env.KIKI_STREAM_CONTEXT_MODE||'per_chunk'},json_stream:{available:true,wire_format:'lab-analysis-stream/v2',priority:['criteria','action_findings','uncertainties'],commit_before_auxiliary:true},status:'ok',mode:'hosted_frame_receipt',sample_hz:.5,image_storage:'none',analysis:{provider:'gemini',configured:providerConfigured(env),configuration_valid,key_count:keys.length,rotation_enabled:keys.length>1,quota_pool_count:new Set(keys.map(v=>v.quota_pool)).size,model:env.GEMINI_SCREEN_MODEL||ANALYSIS_MODEL,lab_model:env.GEMINI_LAB_MODEL||env.GEMINI_SCREEN_MODEL||ANALYSIS_MODEL}});
      }
      const owner = request.headers.get('oai-authenticated-user-id');
      if(url.pathname==='/mcp' && request.method==='POST') return await labMCP(request,env,owner);
      if (!owner) fail(401, 'Open this private site while signed in to ChatGPT.');
      if (['POST','DELETE'].includes(request.method) && request.headers.get('origin') !== url.origin) fail(403, 'Same-origin request required.');
      const streamResult=await labStreamRoute(request,env,owner,executionContext);if(streamResult)return streamResult;
      const labResult=await labRoute(request,env,owner);
      if(labResult) return labResult;
      if (request.method === 'POST' && url.pathname === '/screen-sessions') {
        const state = {id: crypto.randomUUID(), owner, created: Date.now(), status: 'sharing',
          count: 0, revision: 1, latest: null};
        return json({session_id: state.id, sample_interval_ms: 2000, session_limit_seconds: null,
          observation: snapshot(state,await analysisState(request,env,state))}, 201, await receiptHeaders(state, env));
      }
      const match = /^\/screen-sessions\/([a-f0-9-]{36})\/(frame|analyze|observation|pause|resume|stop)$/.exec(url.pathname);
      if (!match) fail(404, 'Not found.');
      const [, id, action] = match;
      const state = await readState(request, env, id, owner);
      const analysis=await analysisState(request,env,state);
      if (action === 'observation' && request.method === 'GET') return json(snapshot(state,analysis));
      if (request.method !== 'POST') fail(405, 'Method not allowed.');
      if (['pause', 'resume', 'stop'].includes(action)) {
        if (state.status === 'ended' && action !== 'stop') fail(409, 'Session has ended.');
        state.status = {pause: 'paused', resume: 'sharing', stop: 'ended'}[action];
        state.revision++;
        return json(snapshot(state,analysis), 200, await receiptHeaders(state, env));
      }
      if (state.status !== 'sharing') fail(409, 'Sharing is not active.');
      const m = metadata(request.headers.get('x-capture-frame'));
      if(action==='analyze') {
        if(!providerConfigured(env)) return json({analysis:{status:'unconfigured',error:'Gemini server secret is missing.'}},503);
        if(analysis.retry_at_ms>Date.now())return json({snapshot:snapshot(state,analysis)},200);
        const remaining=10000-(Date.now()-analysis.last_started);
        if(remaining>0) return json({analysis:{status:'waiting',retry_after_ms:remaining}},429);
        const bytes=await boundedImage(request);
        const digest=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));
        if(!state.latest || state.latest.sha256!==digest || state.latest.sequence!==m.sequence ||
           bytes.length!==m.byte_count || Object.keys(m).some(field=>field!=='type' && m[field]!==state.latest[field])) return json({analysis:{status:'frame_changed',error:'Select the next received frame.'}},409);
        if(analysis.last?.source_frame.frame_id===state.latest.frame_id) return json({analysis:{status:'already_analyzed'}},409);
        analysis.attempts++;analysis.last_started=Date.now();
        try {
          const result=await analyzeFrame(bytes,analysis.last,env,typeof env.ANALYSIS_FETCH==='function' ? env.ANALYSIS_FETCH : fetch);
          const previousId=analysis.last?.source_frame.frame_id || null;
          const currentId=`${id}:analysis:${analysis.attempts}`;
          const completed=Date.now();
          analysis.status='available';delete analysis.error;delete analysis.retry_at_ms;
          analysis.last={summary:result.result.summary,
            facts:result.result.facts.map((description,i)=>({id:`${currentId}:fact:${i+1}`,description,evidence_frame_id:state.latest.frame_id})),
            changes:result.result.changes && previousId ? [{description:result.result.changes,
              basis:'current_frame_vs_previous_report',previous_frame_id:previousId,evidence_frame_id:state.latest.frame_id}] : [],
            uncertainties:result.result.uncertainties,analysis_id:currentId,
            source_frame:{frame_id:state.latest.frame_id,sha256:digest,sequence:state.latest.sequence,captured_elapsed_ms:state.latest.captured_elapsed_ms,
              server_received_at:state.latest.server_received_at,server_received_unix_ms:state.latest.server_received_unix_ms},
            completed_at:new Date(completed).toISOString(),completed_unix_ms:completed,
            model:result.model,prompt_version:result.prompt_version};
        } catch(error) {
          analysis.retry_at_ms=error.retry_at_ms||Date.now()+10000;analysis.status='waiting_for_provider';analysis.error=/^(provider_[a-z0-9_]+|invalid_provider_configuration|invalid_output|incomplete_output|invalid_model_configuration)$/.test(error.message) ? error.message : 'provider_timeout_or_network_error';
        }
        return json({snapshot:snapshot(state,analysis)},200,await analysisHeaders(analysis,env));
      }
      if (state.latest) {
        if(m.view_revision<state.latest.view_revision) fail(409,'View revision cannot decrease within a capture segment.');
        if (m.sequence <= state.latest.sequence || m.captured_elapsed_ms < state.latest.captured_elapsed_ms) fail(409, 'Frame order must increase.');
        const remaining = 1800 - (Date.now() - state.latest.server_received_unix_ms);
        if (remaining > 0) fail(429, 'Wait for the next sample interval.', {
          code: 'sampling_rate_limited', retry_after_ms: remaining,
          headers: {'Retry-After': String(Math.ceil(remaining / 1000))},
        });
      }
      const bytes = await boundedImage(request);
      if (bytes.length !== m.byte_count) fail(422, 'Image byte count mismatch.');
      const dimensions = jpegDimensions(bytes);
      if (dimensions.width !== m.width || dimensions.height !== m.height) fail(422, 'JPEG dimensions mismatch.');
      const digest = hex(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)));
      const previous = state.latest?.sha256 || null;
      const previousSequence = state.latest?.sequence || 0;
      const time = Date.now();
      state.count++; state.revision++;
      state.latest = {...m, frame_id: `${id}:1:${m.sequence}`, event_id: `${id}:${state.revision}`,
        sha256: digest, previous_frame_sha256: previous, skipped_sequences: m.sequence - previousSequence - 1,
        server_received_at: new Date(time).toISOString(), server_received_unix_ms: time};
      delete state.latest.type;
      const headers=await receiptHeaders(state,env);
      headers['X-Capture-Observation']=base64(enc.encode(JSON.stringify(snapshot(state,analysis))));
      return response(bytes, 200, {'Content-Type': 'image/jpeg', ...headers});
    } catch (error) {
      return json({detail: error.status ? error.detail : 'Receiver error. Start a new share.',
        ...(error.code ? {code: error.code, retry_after_ms: error.retry_after_ms} : {}),
      }, error.status || 500, error.headers || {});
    }
  },
};
