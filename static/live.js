let liveMode = true, capturing = false, stream = null, context = null, capture = null;
let liveQueue = [], draining = false, finishing = false, flushResolve = null, liveError = false;
let liveWarning = '';
let listingMicrophones = false;
let liveWords = [], sessionChunks = [], finalizing = false;
let sessionTimer = null;
async function refreshMicrophones(authorize = false) {
  if (listingMicrophones || busy) return;
  listingMicrophones = true; updateLiveButtons();
  let permissionStream = null;
  try {
    if (!navigator.mediaDevices?.enumerateDevices) throw new Error('Use Chrome ou Edge para selecionar uma entrada.');
    if (authorize) permissionStream = await navigator.mediaDevices.getUserMedia({audio:true, video:false});
    const inputs = (await navigator.mediaDevices.enumerateDevices()).filter(device => device.kind === 'audioinput' && device.deviceId && !['default','communications'].includes(device.deviceId));
    const previous = $('microphone').value;
    $('microphone').replaceChildren(new Option('Padrão do sistema', ''));
    inputs.forEach((device, index) => $('microphone').append(new Option(device.label || `Microfone ${index + 1}`, device.deviceId)));
    const available = inputs.some(device => device.deviceId === previous);
    $('microphone').value = available ? previous : '';
    $('mic-help').textContent = previous && !available ? 'A entrada anterior foi desconectada. Selecione outra antes de iniciar.' :
      inputs.some(device => device.label) ? 'Confira a entrada antes de ativar. Para trocar durante a sessão, pare o microfone.' : 'Autorize em “Identificar entradas” para exibir os nomes dos microfones.';
  } catch (error) {
    $('mic-help').textContent = error.name === 'NotAllowedError' ? 'Permita o microfone no navegador para listar as entradas.' : `Não foi possível listar: ${error.message}`;
  } finally {
    permissionStream?.getTracks().forEach(track => track.stop());
    listingMicrophones = false; updateLiveButtons();
  }
}
function updateLiveButtons() {
  $('live-start').disabled = !ready || listingMicrophones || (busy && !capturing);
  $('microphone').disabled = busy || listingMicrophones;
  $('refresh-mics').disabled = busy || listingMicrophones;
  $('live-start').textContent = capturing ? 'Parar e concluir ■' : 'Ativar microfone ●';
  $('live-start').classList.toggle('recording', capturing);
  $('mode-live').disabled = busy; $('mode-file').disabled = busy;
}
function setMode(live) {
  if (busy) return;
  liveMode = live; $('live-panel').hidden = !live; $('file-controls').hidden = live;
  $('mic-controls').hidden = !live;
  $('live-start').hidden = !live; $('start').hidden = live;
  $('mode-live').setAttribute('aria-pressed', String(live)); $('mode-file').setAttribute('aria-pressed', String(!live));
  updateButtons();
}
$('mode-live').onclick = () => setMode(true); $('mode-file').onclick = () => setMode(false);
function wav(samples, rate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2), view = new DataView(buffer);
  function text(offset, value) { for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i)); }
  text(0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true); text(8, 'WAVE');
  text(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  text(36, 'data'); view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) view.setInt16(44 + i * 2, Math.round(Math.max(-1, Math.min(1, samples[i])) * 32767), true);
  return new Blob([buffer], {type:'audio/wav'});
}
async function recognizeLocal(blob, modelName, live, showProgress = false) {
  const form = new FormData(); form.append('file', blob, 'microfone.wav');
  form.append('language', $('language').value); form.append('model_name', modelName);
  form.append('live', String(live)); form.append('glossary', $('glossary').value);
  const {id} = await json(await fetch('/api/jobs', {method:'POST', headers:{'X-Local-App':'1'}, body:form}));
  while (true) {
    const job = await json(await fetch(`/api/jobs/${id}`));
    if (job.status === 'error') throw new Error(job.message);
    if (showProgress) {
      status(`Revisão final com Turbo: ${job.message}`);
      if (job.progress > 0) $('progress').value = job.progress;
    }
    if (job.status === 'done') return job;
    await new Promise(resolve => setTimeout(resolve, 350));
  }
}
async function drainLive() {
  if (draining) return; draining = true;
  try {
    while (liveQueue.length) {
      const chunk = liveQueue.shift();
      status(`Reconhecendo fala localmente… ${liveQueue.length ? `${liveQueue.length} trecho(s) na fila.` : ''}`);
      const job = await recognizeLocal(wav(chunk.samples, chunk.rate), $('live-model').value, true);
      liveWords = mergeWords(liveWords, job.words, chunk.start);
      segments = wordsToSegments(liveWords);
      render(); $('segments').scrollTop = $('segments').scrollHeight;
    }
    if (capturing) status('Ouvindo. Continue falando; o texto aparece a cada trecho.');
  } catch (error) {
    liveError = true; status(`Transcrição interrompida: ${error.message}`, true);
    liveQueue = []; if (capturing) await stopCapture();
  } finally { draining = false; completeLive(); }
}
async function completeLive() {
  if (!finishing || draining || liveQueue.length || finalizing) return;
  finalizing = true;
  try {
    if (!liveError && sessionChunks.length && $('final-review').checked) {
      status('Revisão final: reconhecendo a sessão inteira com Turbo…');
      $('progress').hidden = false; $('progress').removeAttribute('value');
      const audio = sessionAudio(sessionChunks);
      const job = await recognizeLocal(wav(audio.samples, audio.rate), 'turbo', false, true);
      if (job.segments.length) segments = job.segments;
      else if (segments.length) liveWarning = 'A revisão final não detectou fala. A prévia foi preservada.';
      $('progress').value = 100;
    }
  } catch (error) {
    liveWarning = `A revisão final falhou; a prévia foi preservada. ${error.message}`;
  } finally { sessionChunks = []; finalizing = false; }
  finishing = false; busy = false; render(); updateButtons();
  $('live-title').textContent = 'Sua voz, em tempo real.';
  $('live-detail').textContent = 'Microfone desligado'; $('mic-level').value = 0;
  $('doc-hint').textContent = 'Revise e exporte. O áudio temporário desta sessão foi liberado.';
  if (!liveError) status(liveWarning || (segments.length ? 'Sessão concluída. Revise e exporte o texto.' : 'Sessão concluída. Nenhuma fala detectada.'), Boolean(liveWarning));
}
async function stopCapture() {
  if (!capturing) return;
  capturing = false; finishing = true; updateButtons();
  clearTimeout(sessionTimer); sessionTimer = null;
  stream?.getTracks().forEach(track => track.stop());
  if (!liveError) status('Microfone desligado. Concluindo os últimos trechos…');
  if (capture) {
    await new Promise(resolve => {
      const timer = setTimeout(resolve, 1200);
      flushResolve = () => { clearTimeout(timer); resolve(); };
      capture.port.postMessage('flush');
    });
  }
  stream?.getTracks().forEach(track => track.stop());
  capture?.disconnect(); if (context && context.state !== 'closed') await context.close();
  stream = context = capture = null; $('mic-level').value = 0;
  completeLive();
}
$('live-start').onclick = async () => {
  if (capturing) { await stopCapture(); return; }
  if (segments.length && !confirm('Iniciar uma nova sessão e substituir a transcrição atual? Exporte sua revisão antes.')) return;
  busy = true; updateButtons();
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('Este navegador não oferece acesso ao microfone. Abra no Edge ou Chrome.');
    const deviceId = $('microphone').value;
    stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1, echoCancellation:true, noiseSuppression:true,
      ...(deviceId ? {deviceId:{exact:deviceId}} : {})}, video:false});
    context = new AudioContext({sampleRate:16000}); await context.resume();
    await context.audioWorklet.addModule('/static/recorder.js');
    capture = new AudioWorkletNode(context, 'voice-capture');
    context.createMediaStreamSource(stream).connect(capture); capture.connect(context.destination);
    liveQueue = []; liveWords = []; sessionChunks = []; finalizing = false;
    liveError = false; liveWarning = ''; finishing = false; segments = []; selected = null;
    if (sourceUrl) URL.revokeObjectURL(sourceUrl); sourceUrl = null;
    $('player').removeAttribute('src'); $('player').hidden = true;
    $('file').value = ''; $('file-name').textContent = 'Solte seu áudio aqui'; $('file-detail').textContent = 'ou clique para selecionar um arquivo';
    $('progress').hidden = true; capturing = true;
    sessionTimer = setTimeout(() => {
      if (capturing) {
        liveWarning = 'Limite de 30 minutos atingido. Sessão concluída; exporte e inicie outra.';
        stopCapture();
      }
    }, 30 * 60 * 1000);
    capture.port.onmessage = event => {
      const data = event.data;
      if (data.level !== undefined) $('mic-level').value = data.level;
      if (data.flushed) { flushResolve?.(); flushResolve = null; }
      if (data.samples && !liveError) {
        sessionChunks.push(data);
        liveQueue.push(data); drainLive();
        if (data.start + data.samples.length / data.rate >= 1800 && capturing) {
          liveWarning = 'Limite de 30 minutos atingido. Sessão concluída; exporte e inicie outra.';
          stopCapture();
        }
        if (liveQueue.length >= 6 && capturing) {
          liveWarning = 'A captura foi interrompida porque a CPU ficou atrasada. Os trechos captados foram concluídos; revise e exporte.';
          status('O computador ficou atrasado. Microfone pausado; concluindo os trechos já captados.', true); stopCapture();
        }
      }
    };
    stream.getAudioTracks()[0].onended = () => { if (capturing) stopCapture(); };
    $('live-title').textContent = 'Ouvindo sua voz…'; $('live-detail').textContent = stream.getAudioTracks()[0].label || 'Microfone ativo · reconhecimento local';
    $('doc-hint').textContent = 'A transcrição aparece em trechos. Pare o microfone para revisar.';
    status('Microfone ativo. Comece a falar.'); render(); updateButtons();
  } catch (error) {
    stream?.getTracks().forEach(track => track.stop());
    if (context && context.state !== 'closed') await context.close();
    stream = context = capture = null; capturing = false; busy = false;
    status(error.name === 'NotAllowedError' ? 'Microfone não autorizado. Permita o acesso no navegador e tente novamente.' :
      ['NotFoundError','OverconstrainedError'].includes(error.name) ? 'Entrada indisponível. Use “Identificar entradas” e selecione outro microfone.' : `Não foi possível ativar: ${error.message}`, true);
    updateButtons();
  }
};
$('refresh-mics').onclick = () => refreshMicrophones(true);
navigator.mediaDevices?.addEventListener('devicechange', () => refreshMicrophones());
refreshMicrophones();
