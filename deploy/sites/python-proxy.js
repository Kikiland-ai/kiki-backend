// Private Site edge only: no model calls, progress decisions or drawing logic.
async function pythonProxy(request,env){
 let backend;
 try {
  backend=new URL(env.KIKI_FASTAPI_ORIGIN);
  if(backend.protocol!=='https:'||backend.username||backend.password||backend.pathname!=='/'||backend.search||backend.hash||backend.hostname.endsWith('.chatgpt.site'))throw Error();
 }catch{ return json({detail:'Python backend origin is not a valid HTTPS service root.'},503); }
 if(typeof env.KIKI_PROXY_SECRET!=='string'||env.KIKI_PROXY_SECRET.length<32)return json({detail:'Python bridge secret is not configured.'},503);
 const incoming=new URL(request.url),mcp=incoming.pathname==='/mcp',health=incoming.pathname==='/health';
 const owner=request.headers.get('oai-authenticated-user-id');
 if(!owner&&!mcp&&!health)return json({detail:'Open this private Site while signed in.'},401);
 const websocket=request.headers.get('upgrade')?.toLowerCase()==='websocket';
 if((!mcp&&['POST','DELETE','PUT','PATCH'].includes(request.method)||websocket)&&request.headers.get('origin')!==incoming.origin)
  return json({detail:'Same-origin request required.'},403);
 // Fixed destination; caller data can never choose an upstream host or credentials.
 backend.pathname=incoming.pathname;backend.search=incoming.search;
 const headers=new Headers();
 for(const name of ['content-type','accept','idempotency-key','upgrade','sec-websocket-key','sec-websocket-version','sec-websocket-protocol']){
  const value=request.headers.get(name);if(value)headers.set(name,value);
 }
 headers.set('origin',backend.origin);
 headers.set('x-kiki-proxy-key',env.KIKI_PROXY_SECRET);
 if(owner)headers.set('x-kiki-owner',owner);
 const options={method:request.method,headers,redirect:'manual'};
 if(!['GET','HEAD'].includes(request.method)){options.body=request.body;options.duplex='half';}
 try {
  const upstream=await (typeof env.PYTHON_PROXY_FETCH==='function'?env.PYTHON_PROXY_FETCH:fetch)(new Request(backend,options));
  if(upstream.status>=300&&upstream.status<400)return json({detail:'Python backend redirected; bridge refused.'},502);
  // Cloudflare's fetch() owns the WebSocket handoff. Do not consume/recreate a 101.
  return upstream;
 }catch{ return json({detail:'Python backend unavailable. Existing progress was not moved to another backend.'},502); }
}
