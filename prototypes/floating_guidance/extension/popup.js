// Explicit user binding of the current tab; nothing binds automatically.
(async () => {
 const $=id=>document.getElementById(id);
 const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
 async function refresh(){
  const s=await chrome.runtime.sendMessage({type:'popup_status',tabId:tab.id});
  $('bind').hidden=!s.bindable||s.bound;$('unbind').hidden=!s.bound;
  $('state').textContent=!s.bindable?'Open MATLAB Online in this tab, then show Kiki here.':s.bound?(s.tracker_open?'Kiki is shown on this tab and connected to the tracker.':'Kiki is shown on this tab. Open the Kiki tracker to connect it.'):'Show Kiki’s current step and screen context on this tab.';
 }
 $('bind').onclick=async()=>{const r=await chrome.runtime.sendMessage({type:'bind_tab',tabId:tab.id});if(!r.ok)$('state').textContent=r.error;await refresh();};
 $('unbind').onclick=async()=>{await chrome.runtime.sendMessage({type:'unbind'});await refresh();};
 await refresh();
})();
