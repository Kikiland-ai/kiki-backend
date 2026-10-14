/* Native screen sharing, one in-flight frame, and actual server acknowledgments. */
(() => {
  const $ = (id) => document.getElementById(id);
  let stream = null, socket = null, session = null, timer = null, heartbeat = null;
  let sequence = 0, started = 0, paused = false, pending = false, ending = false;
  let imageURL = null, generation = 0, pendingSince = 0, displayedSequence = 0;
  let sourceSize = null;
  const canvas = document.createElement('canvas');
  const status = (message) => { $('status').textContent = message; };

  async function request(path, options = {}) {
    const response = await fetch(path, {credentials: 'same-origin', signal: AbortSignal.timeout(10000), ...options});
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(typeof data.detail === 'string' ? data.detail : `Server returned ${response.status}.`);
    }
    return response.json();
  }

  function display(data) {
    $('json').textContent = JSON.stringify(data, null, 2);
    $('count').textContent = data.received_frame_count;
    const frame = data.observation?.latest_frame;
    if (frame) {
      $('dimensions').textContent = `${frame.width} × ${frame.height}`;
      $('received').textContent = new Date(frame.server_received_at).toLocaleTimeString();
    }
  }

  async function receiveImage(currentGeneration) {
    const response = await fetch(`/screen-sessions/${session}/frame`, {cache: 'no-store'});
    if (!response.ok) return;
    const frameSequence = Number(response.headers.get('X-Frame-Sequence'));
    const blob = await response.blob();
    if (currentGeneration !== generation || ending || frameSequence < displayedSequence) return;
    displayedSequence = frameSequence;
    const nextURL = URL.createObjectURL(blob);
    if (imageURL) URL.revokeObjectURL(imageURL);
    imageURL = nextURL;
    $('remote').src = imageURL;
    $('remote').hidden = false;
    $('remote-empty').hidden = true;
  }

  async function sample() {
    if (!stream || paused || ending || pending || socket?.readyState !== WebSocket.OPEN) return;
    const video = $('preview');
    if (!video.videoWidth || !video.videoHeight) return;
    const currentGeneration = generation;
    pending = true;
    pendingSince = performance.now();
    try {
      const scale = Math.min(1, 1600 / Math.max(video.videoWidth, video.videoHeight));
      const dimensions = `${video.videoWidth}x${video.videoHeight}`;
      if (sourceSize && sourceSize !== dimensions && window.KikiLab) {
        await window.KikiLab.onViewChange(window.KikiLab.viewRevision() + 1);
      }
      sourceSize = dimensions;
      canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
      canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      let blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
      if (blob?.size > 1000000) blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.55));
      if (currentGeneration !== generation || ending || paused) { pending = false; return; }
      if (!blob || blob.size > 1000000) throw new Error('Frame exceeds the receiver size limit. Try sharing a smaller window.');
      sequence += 1;
      const meta = {type: 'frame', capture_epoch: 1, sequence, view_revision: window.KikiLab?.viewRevision() || 1,
        captured_elapsed_ms: Math.round(performance.now() - started),
        width: canvas.width, height: canvas.height,
        source_width: video.videoWidth, source_height: video.videoHeight,
        byte_count: blob.size, mime_type: 'image/jpeg'};
      socket.send(JSON.stringify(meta));
      socket.send(blob);
    } catch (error) {
      pending = false;
      status(error.message);
      await end(true);
    }
  }

  async function end(preserveMessage = false) {
    if (ending) return;
    ending = true;
    generation += 1;
    clearInterval(timer); clearInterval(heartbeat);
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
    $('preview').srcObject = null;
    $('local-empty').hidden = false;
    if (session) {
      try { display(await request(`/screen-sessions/${session}/stop`, {method: 'POST'})); }
      catch (error) { if (!preserveMessage) status(`Sharing stopped. ${error.message}`); }
    }
    if (socket) { socket.onclose = null; socket.close(); }
    socket = null; pending = false; paused = false;
    await window.KikiLab?.onCaptureState();
    $('share').disabled = false; $('pause').disabled = true; $('stop').disabled = true;
    $('pause').textContent = 'Pause';
    if (!preserveMessage) status('Sharing stopped. No new frames are being sent.');
    ending = false;
  }

  $('share').addEventListener('click', async () => {
    if (!window.isSecureContext || !navigator.mediaDevices?.getDisplayMedia) {
      status('Open this page on localhost or HTTPS in a browser that supports screen sharing.'); return;
    }
    $('share').disabled = true;
    status('Choose the screen, window or tab to share.');
    try {
      // Invoke before network awaits: the browser requires a direct user gesture.
      stream = await navigator.mediaDevices.getDisplayMedia({video: {frameRate: {ideal: 5, max: 10}}, audio: false});
      const currentGeneration = ++generation;
      sequence = 0; displayedSequence = 0; started = performance.now(); pending = false; sourceSize = null;
      $('count').textContent = '0'; $('dimensions').textContent = '—'; $('received').textContent = '—';
      $('remote').hidden = true; $('remote-empty').hidden = false;
      if (imageURL) { URL.revokeObjectURL(imageURL); imageURL = null; }
      $('preview').srcObject = stream;
      stream.getVideoTracks()[0].addEventListener('ended', () => end());
      await $('preview').play();
      if (currentGeneration !== generation) return;
      $('local-empty').hidden = true;
      const created = await request('/screen-sessions', {method: 'POST'});
      if (currentGeneration !== generation) {
        await request(`/screen-sessions/${created.session_id}/stop`, {method: 'POST'});
        return;
      }
      session = created.session_id;
      $('json-link').href = `/screen-sessions/${session}/observation`;
      $('json-link').hidden = false;
      const url = new URL(created.stream_path, location.href);
      url.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(url);
      socket.onopen = () => {
        if (currentGeneration !== generation) return;
        socket.send(JSON.stringify({type: 'capture_started'}));
        $('pause').disabled = false; $('stop').disabled = false;
        status('Sharing active. Waiting for the server’s first frame.');
        sample();
        timer = setInterval(() => {
          if (pending && performance.now() - pendingSince > 12000) {
            status('Server acknowledgment timed out. Sharing has stopped.'); end(true);
          } else sample();
        }, created.sample_interval_ms);
        heartbeat = setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({type: 'heartbeat'}));
        }, 8000);
      };
      socket.onmessage = async (event) => {
        if (currentGeneration !== generation) return;
        const data = JSON.parse(event.data);
        if (data.observation) display(data.observation);
        if (data.type === 'ack') {
          pending = false;
          window.KikiLab?.onFrame(data.observation.observation.latest_frame);
          await receiveImage(currentGeneration);
          if (!paused && currentGeneration === generation) status('Sharing active. Frames are arriving at the server.');
        } else if (data.type === 'skipped') {
          pending = false;
        } else if (data.type === 'status' && data.observation.capture_status === 'sharing') {
          window.KikiLab?.onCaptureStart(session);
        } else if (data.type === 'status') {
          void window.KikiLab?.onCaptureState();
        } else if (data.type === 'error') {
          status(data.message); await end(true);
        }
      };
      socket.onerror = () => { status('Could not connect to the frame receiver.'); end(true); };
      socket.onclose = () => {
        if (currentGeneration === generation && !ending) { status('Receiver disconnected. Sharing has stopped.'); end(true); }
      };
    } catch (error) {
      status(error.name === 'NotAllowedError' ? 'Sharing was cancelled or permission was declined.' : error.message);
      await end(true);
    }
  });

  $('pause').addEventListener('click', () => {
    if (socket?.readyState !== WebSocket.OPEN) return;
    paused = !paused;
    socket.send(JSON.stringify({type: paused ? 'pause' : 'resume'}));
    $('pause').textContent = paused ? 'Resume' : 'Pause';
    status(paused ? 'Paused. No new frames are being sent.' : 'Sharing resumed.');
  });
  $('stop').addEventListener('click', () => end());
  window.addEventListener('pagehide', () => {
    if (stream) stream.getTracks().forEach(track => track.stop());
    if (socket) socket.close();
  });
  if (!window.isSecureContext || !navigator.mediaDevices?.getDisplayMedia) {
    $('share').disabled = true;
    status('Screen sharing requires localhost or HTTPS and a supported desktop browser.');
  }
})();
