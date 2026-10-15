const $=id=>document.getElementById(id);
async function send(message){
 const result=await Promise.race([chrome.runtime.sendMessage({to:'background',...message}),new Promise((_,reject)=>setTimeout(()=>reject(Error('The extension did not respond within 8 seconds. Refresh the tab and reconnect.')),8000))]);
 if(!result)throw Error('The extension returned no response.');if(result.error)throw Error(result.error);return result;
}
async function diagnostics(){try{const d=await send({type:'diagnostics'});$('diagnostics').textContent=JSON.stringify(d,null,2);$('version').textContent='Adapter '+d.adapter_version;return d;}catch(e){$('status').textContent=e.message;}}
async function command(message,close=false){
 $('status').textContent='Sending drawing…';
 try{const result=await send(message);if(close&&result.last_ack?.status==='tab_rendered'){window.close();return;}if(result.last_error)throw Error(result.last_error);$('status').textContent=result.capturing?'Periodic capture started.':'Command completed.';await diagnostics();}
 catch(e){$('status').textContent='Error: '+e.message;await diagnostics();}
}
$('start').onclick=async()=>{try{const[tab]=await chrome.tabs.query({active:true,currentWindow:true});await command({type:'start',tabId:tab.id},true);}catch(e){$('status').textContent=e.message;}};
$('draw').onclick=()=>command({type:'draw_demo'},true);
$('render').onclick=()=>{try{command({type:'draw_json',operations:JSON.parse($('json').value)},true);}catch(e){$('status').textContent='Invalid JSON: '+e.message;}};
$('stop').onclick=async()=>{await command({type:'stop'});$('status').textContent='Stopped. Annotations cleared.';};
$('capture').onclick=()=>command({type:'start_capture'});
$('logs').onclick=()=>diagnostics();
$('copy').onclick=async()=>{const d=await diagnostics();if(!d)return;try{await navigator.clipboard.writeText(JSON.stringify(d,null,2));$('status').textContent='Diagnostics copied. No pixels are included.';}catch{$('status').textContent='Select and copy the diagnostic text below.';$('diag-details').open=true;}};
void diagnostics();

$('tutor').onclick=async()=>{$('status').textContent='Connecting to tutor…';try{const[tab]=await chrome.tabs.query({active:true,currentWindow:true});const result=await send({type:'start',tabId:tab.id,mode:'tutor'});if(result.mode!=='live_tutor')throw Error('Tutor did not connect.');$('status').textContent='Connected to tutor. Keep the reader sharing this same tab, close this popup, and leave Simulink visible. Guidance appears after a fresh lab analysis.';await diagnostics();}catch(e){$('status').textContent=e.message;}};
