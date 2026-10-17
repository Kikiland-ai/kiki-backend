(() => {
  const $ = id => document.getElementById(id);
  let stream = null, session = null, timer = null, generation = 0, sequence = 0;
  let paused = false, ending = false, busy = false, started = 0, upload = null;
  let captureViewRevision=1,lastSourceWidth=0,lastSourceHeight=0;
  let imageURL = null, currentSnapshot = null, lastReport = null, analysisMeta = null;
  let analysisBusy = false, analysisAbort = null, nextAnalysisAt = 0, analysisDisabled = false;
  let analysisVersion = 0, localAnalysisAttempts = 0;
  const receipts = [];
  const canvas = document.createElement('canvas');
  const status = message => { $('status').textContent = message; };
  const decode = value => JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(value), c => c.charCodeAt(0))));

  async function api(path, method = 'GET') {
    const response = await fetch(path, {method, credentials: 'same-origin', signal: AbortSignal.timeout(10000)});
    const data = await response.json().catch(() => ({detail: 'Receiver returned an unexpected response.'}));
    if (!response.ok) throw Object.assign(new Error(data.detail || `Receiver returned ${response.status}.`),{fatal:true});
    return data;
  }
  function list(id, values) {
    $(id).replaceChildren(...values.map(text => {
      const item = document.createElement('li'); item.textContent = text; return item;
    }));
  }
  function renderAnalysis(data) {
    const report = data.observation?.mode === 'vision_observation' ? data.observation : null;
    if (report) {
      $('analysis-summary').textContent = report.summary;
      list('analysis-facts', report.facts.map(fact => fact.description));
      list('analysis-uncertainties', report.uncertainties.map(text => `Uncertain: ${text}`));
      $('analysis-changes').textContent = report.changes.map(change => `Compared with the previous report: ${change.description}`).join(' ');
      $('analysis-changes').hidden = !report.changes.length;
      const age = Math.max(0, Math.round((Date.now() - report.source_frame.server_received_unix_ms) / 1000));
      $('analysis-source').textContent = `Based on frame ${report.source_frame.sequence}, received ${age}s ago · ${report.model}. Newest received frame: ${data.observation.latest_frame?.sequence || '—'}.`;
    }
    if (!analysisBusy) {
      const messages = {available:'DESCRIPTION AVAILABLE', failed:'ANALYSIS FAILED — CAPTURE CONTINUES',
        waiting_for_provider:'WAITING FOR PROVIDER — SHARING CONTINUES', not_enabled:'ANALYSIS NOT CONFIGURED',
        awaiting_first_analysis:'WAITING FOR ANALYSIS'};
      $('analysis-state').textContent = !$('enable-analysis').checked ? 'ANALYSIS OFF' :
        messages[data.analysis?.status] || 'WAITING FOR A FRAME';
      if (data.analysis?.stale && report) $('analysis-state').textContent += ' · OLDER FRAME';
    }
  }
  function show(data, receipt, fromAnalysis = false) {
    if (!fromAnalysis) currentSnapshot = data;
    const report = data.observation?.mode === 'vision_observation' ? data.observation : null;
    if (report && (!lastReport || report.completed_unix_ms >= lastReport.completed_unix_ms)) lastReport = report;
    if (data.analysis && (!analysisMeta || data.analysis.attempts >= analysisMeta.attempts)) analysisMeta = data.analysis;
    if (!currentSnapshot) return;
    const displayed = {...currentSnapshot};
    if (analysisMeta) displayed.analysis = {...analysisMeta, browser_attempt_count:localAnalysisAttempts};
    const receivedAge = displayed.observation?.latest_frame ? Math.max(0, Date.now()-displayed.observation.latest_frame.server_received_unix_ms) : null;
    displayed.freshness = {received_age_ms:receivedAge, stale:receivedAge === null || receivedAge > 10000};
    if (lastReport) {
      displayed.schema = 'screen-awareness/v1';
      displayed.observation = {...lastReport, analysis_status:analysisMeta?.status,
        latest_frame:currentSnapshot.observation?.latest_frame || null};
      displayed.analysis.age_ms = Math.max(0, Date.now() - lastReport.source_frame.server_received_unix_ms);
      displayed.analysis.stale = displayed.analysis.age_ms > 20000;
    }
    $('json').textContent = JSON.stringify(displayed, null, 2);
    $('count').textContent = displayed.received_frame_count;
    const frame = displayed.observation?.latest_frame;
    if (frame) {
      $('dimensions').textContent = `${frame.width} × ${frame.height}`;
      $('received').textContent = new Date(frame.server_received_at).toLocaleTimeString();
    }
    renderAnalysis(displayed);
    if (receipt || fromAnalysis) receipts.push({observation:displayed, signed_receipt:receipt || null});
    if(receipts.length>100)receipts.splice(0,receipts.length-100);
  }
  async function maybeAnalyze(blob, meta, current) {
    if (!$('enable-analysis').checked || analysisBusy || analysisDisabled || paused || ending ||
        Date.now() < nextAnalysisAt) return;
    analysisBusy = true; localAnalysisAttempts++; nextAnalysisAt = Date.now() + 10000;
    analysisAbort = new AbortController();
    const version = analysisVersion, controller = analysisAbort;
    const timeout = setTimeout(() => controller.abort(), 25000);
    $('analysis-state').textContent = `ANALYZING FRAME ${meta.sequence} · CAPTURE CONTINUES`;
    try {
      const response = await fetch(`/screen-sessions/${session}/analyze`, {method:'POST',
        headers:{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta)},
        body:blob, credentials:'same-origin', signal:controller.signal});
      const data = await response.json();
      if (current !== generation || version !== analysisVersion) return;
      if (data.snapshot) {show(data.snapshot, null, true);if(data.snapshot.analysis?.retry_after_ms)nextAnalysisAt=Math.max(nextAnalysisAt,Date.now()+data.snapshot.analysis.retry_after_ms);}
      if (!response.ok) {
        const problem = data.analysis;
        $('analysis-state').textContent = `${problem?.error || data.detail || 'Analysis is temporarily unavailable.'} Capture continues.`;
        if (problem?.retry_after_ms) nextAnalysisAt = Date.now() + Math.max(2000, problem.retry_after_ms);
        if (['unconfigured'].includes(problem?.status) || [401,403,404,410,422].includes(response.status)) analysisDisabled = true;
      } else if (data.snapshot?.analysis.status === 'failed') {
        nextAnalysisAt = Date.now() + 10000;
        $('analysis-state').textContent = `Analysis failed (${data.snapshot.analysis.error}). Capture continues.`;
      }
    } catch (error) {
      if (current === generation && version === analysisVersion) {
        nextAnalysisAt = Date.now() + 10000;
        $('analysis-state').textContent = 'Analysis timed out or could not connect. Capture continues.';
      }
    } finally {
      clearTimeout(timeout);
      if (analysisAbort === controller) { analysisBusy = false; analysisAbort = null; }
    }
  }
  async function frame() {
    if (!stream || paused || busy || ending) return;
    const video = $('preview');
    if (!video.videoWidth || !video.videoHeight) return;
    const current = generation;
    busy = true;
    let writingTicket=null;
    try {
      writingTicket=await window.KikiWriting?.prepareFrame(video);
      const freshSample=window.KikiWriting?.sample(writingTicket),source=freshSample?.image||video;
      const sourceWidth=freshSample?.width||video.videoWidth,sourceHeight=freshSample?.height||video.videoHeight;
      captureViewRevision=Math.max(captureViewRevision,window.KikiLab?.viewRevision()||1);
      if(lastSourceWidth && (lastSourceWidth!==sourceWidth||lastSourceHeight!==sourceHeight)){captureViewRevision++;window.KikiLab?.onViewChange(captureViewRevision);}
      lastSourceWidth=sourceWidth;lastSourceHeight=sourceHeight;
      const scale = Math.min(1, 1600 / Math.max(sourceWidth, sourceHeight));
      canvas.width = Math.max(1, Math.round(sourceWidth * scale));
      canvas.height = Math.max(1, Math.round(sourceHeight * scale));
      canvas.getContext('2d').drawImage(source, 0, 0, canvas.width, canvas.height);
      const visualFingerprint=writingTicket?window.KikiWriting.fingerprint(writingTicket,canvas):null;
      // The immutable canvas already contains clean pixels. Restore the user's
      // guidance before asynchronous JPEG encoding, which can take a full frame
      // interval in a throttled reader tab. Encoding must not mask live ink.
      const writingBinding=await window.KikiWriting?.finishFrame(writingTicket,canvas);
      writingTicket=null;
      if (current !== generation || ending || paused) return;
      let blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .8));
      if (blob?.size > 1000000) blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .55));
      if (current !== generation || ending || paused) return;
      if (!blob || blob.size > 1000000) throw Object.assign(new Error('Frame exceeds 1 MB. Try a smaller shared window.'),{fatal:true});
      const meta = {type: 'frame', capture_epoch: 1, view_revision:captureViewRevision, sequence: ++sequence,
        captured_elapsed_ms: Math.round(performance.now() - started),
        width: canvas.width, height: canvas.height, source_width: sourceWidth,
        source_height: sourceHeight, byte_count: blob.size, mime_type: 'image/jpeg'};
      upload = fetch(`/screen-sessions/${session}/frame`, {method: 'POST',
        headers: {'Content-Type': 'image/jpeg', 'X-Capture-Frame': JSON.stringify(meta)},
        body: blob, credentials: 'same-origin', signal: AbortSignal.timeout(12000)});
      const response = await upload;
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        if ([429,500,502,503,504].includes(response.status)) {
          if (current === generation && !ending && !paused) {
            status('Receiver requested a short wait. Screen sharing remains active.');
          }
          return Math.max(2000, data.retry_after_ms||Number(response.headers.get('Retry-After'))*1000||5000);
        }
        throw Object.assign(new Error(data.detail || `Receiver returned ${response.status}.`),{fatal:true});
      }
      const observation = decode(response.headers.get('X-Capture-Observation'));
      const receipt = response.headers.get('X-Capture-Receipt');
      const returnedImage = await response.blob();
      if (current !== generation || ending) return;
      show(observation, receipt);
      if (imageURL) URL.revokeObjectURL(imageURL);
      imageURL = URL.createObjectURL(returnedImage);
      $('remote').src = imageURL;
      $('remote').hidden = false;
      $('remote-empty').hidden = true;
      status('Sharing active. Frames are arriving at the server.');
      // Analysis runs independently; provider latency never holds the capture timer.
      const admittedWriting=await window.KikiWriting?.admitFrame(writingBinding,observation.observation?.latest_frame,returnedImage);
      window.KikiLab?.onFrame(returnedImage,meta,observation.observation?.latest_frame,admittedWriting,admittedWriting?visualFingerprint:null);
      void maybeAnalyze(returnedImage, meta, current);
    } catch (error) {
      if (current === generation && !ending) {if(error.fatal){status(error.message);await stop(true);}else{status('Connection interrupted. Sharing remains active; a fresh frame will be retried.');return 5000;}}
    } finally {
      if(writingTicket)await window.KikiWriting?.finishFrame(writingTicket,canvas).catch(()=>{});
      upload = null; busy = false;
    }
    return 2000;
  }
  async function tick() {
    if (!stream || ending) return;
    const current = generation;
    const delay = await frame();
    // Schedule after completion, so a delayed timer cannot catch up with a burst.
    if (current === generation && stream && !ending) timer = setTimeout(tick, delay || 2000);
  }
  async function stop(preserveMessage = false) {
    if (ending) return;
    ending = true; generation++; analysisVersion++;
    analysisAbort?.abort(); analysisBusy = false; analysisAbort = null;
    clearTimeout(timer);
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;window.KikiWriting?.setStream(null);
    $('preview').srcObject = null; $('local-empty').hidden = false;
    // Serialize cookie receipt updates before writing the ended receipt.
    if (upload) await upload.catch(() => {});
    if (session) {
      try { show(await api(`/screen-sessions/${session}/stop`, 'POST')); }
      catch (error) { if (!preserveMessage) status(`Capture stopped. ${error.message}`); }
    }
    await window.KikiLab?.onCaptureStop();
    busy = false; paused = false;
    $('share').disabled = false; $('stop').disabled = true; $('pause').disabled = true;
    $('pause').textContent = 'Pause';
    if (!preserveMessage) status('Sharing stopped. No new frames are being sent.');
    ending = false;
  }
  $('share').addEventListener('click', async () => {
    $('share').disabled = true;
    try {
      stream = await navigator.mediaDevices.getDisplayMedia({video: {frameRate: {ideal: 10, max: 10}}, audio: false});
      const current = ++generation;
      sequence = 0; captureViewRevision=window.KikiLab?.viewRevision()||1;lastSourceWidth=0;lastSourceHeight=0; started = performance.now(); receipts.length = 0;
      currentSnapshot = null; lastReport = null; analysisMeta = null;
      nextAnalysisAt = 0; analysisDisabled = false; localAnalysisAttempts = 0; analysisVersion++;
      $('analysis-summary').textContent = 'Waiting for a description of the first selected frame.';
      list('analysis-facts', []); list('analysis-uncertainties', []);
      $('analysis-changes').hidden = true; $('analysis-source').textContent = '';
      if (imageURL) { URL.revokeObjectURL(imageURL); imageURL = null; }
      $('remote').hidden = true; $('remote-empty').hidden = false;
      $('count').textContent = '0'; $('dimensions').textContent = '—'; $('received').textContent = '—';
      $('preview').srcObject = stream;
      stream.getVideoTracks()[0].addEventListener('ended', () => stop());
      await $('preview').play();window.KikiWriting?.setStream(stream);
      if (current !== generation) return;
      $('local-empty').hidden = true;
      const created = await api('/screen-sessions', 'POST');
      if (current !== generation) { await api(`/screen-sessions/${created.session_id}/stop`, 'POST'); return; }
      session = created.session_id;
      window.KikiLab?.onCaptureStart(session);
      show(created.observation);
      $('json-link').href = `/screen-sessions/${session}/observation`; $('json-link').hidden = false;
      $('pause').disabled = false; $('stop').disabled = false;
      status('Sharing active. Waiting for the first received frame.');
      tick();
    } catch (error) {
      status(error.name === 'NotAllowedError' ? 'Sharing was cancelled or declined. Open this site in its own browser tab and try again.' : error.message);
      await stop(true);
    }
  });
  $('pause').addEventListener('click', async () => {
    if (ending) return;
    $('pause').disabled = true;
    const desiredPaused = !paused;void window.KikiWriting?.invalidate('Sharing lifecycle changed.');
    // Keep sampling blocked throughout the lifecycle request, including resume.
    paused = true;
    if (upload) await upload.catch(() => {});
    try {
      show(await api(`/screen-sessions/${session}/${desiredPaused ? 'pause' : 'resume'}`, 'POST'));
      paused = desiredPaused;
      window.KikiLab?.onCapturePause(paused,session);
      $('pause').textContent = paused ? 'Resume' : 'Pause';
      status(paused ? 'Paused. No new frames are being sent.' : 'Sharing resumed.');
      if (!ending) $('pause').disabled = false;
    } catch (error) { status(error.message); await stop(true); }
  });
  $('enable-analysis').addEventListener('change', () => {
    analysisVersion++; analysisAbort?.abort(); analysisAbort = null; analysisBusy = false;
    analysisDisabled = false; nextAnalysisAt = Date.now() + 10000;
    $('analysis-state').textContent = $('enable-analysis').checked ? 'WAITING FOR NEXT SELECTED FRAME' : 'ANALYSIS OFF';
  });
  $('stop').addEventListener('click', () => stop());
  window.addEventListener('pagehide', () => {
    analysisAbort?.abort();
    clearTimeout(timer);
    if (stream) stream.getTracks().forEach(track => track.stop());
  });
  setInterval(() => { if (currentSnapshot) show(currentSnapshot); }, 1000);
  if (!window.isSecureContext || !navigator.mediaDevices?.getDisplayMedia) {
    $('share').disabled = true;
    status('Open this HTTPS site in a desktop browser such as Chrome or Edge.');
  } else if (window.top !== window.self) {
    status('For screen sharing, open this site in its own browser tab using its link.');
  }
})();
