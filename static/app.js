const $ = id => document.getElementById(id);
let selected = null, sourceUrl = null, segments = [], busy = false, ready = false;
function status(message, error = false) {
  $('status-text').textContent = message;
  $('status-text').parentElement.classList.toggle('error', error);
}
function updateButtons() {
  $('start').disabled = busy || !selected || !ready;
  $('file').disabled = busy;
  $('language').disabled = busy;
  ['live-model','final-review','glossary'].forEach(id => $(id).disabled = busy);
  ['copy', 'txt', 'srt'].forEach(id => $(id).disabled = busy || segments.length === 0);
  if (typeof updateLiveButtons === 'function') updateLiveButtons();
}
function choose(file) {
  if (!file || busy) return;
  if (!/\.(mp3|wav|m4a|mp4|ogg|flac|webm|aac|wma|opus)$/i.test(file.name) || file.size === 0 || file.size > 500 * 1024 ** 2) {
    status('Selecione um áudio válido, não vazio, de até 500 MB.', true); return;
  }
  selected = file;
  if (sourceUrl) URL.revokeObjectURL(sourceUrl);
  sourceUrl = URL.createObjectURL(file);
  $('player').src = sourceUrl; $('player').hidden = false;
  $('file-name').textContent = file.name;
  $('file-detail').textContent = `${(file.size / 1024 ** 2).toFixed(1)} MB · arquivo selecionado`;
  segments = []; render(); $('progress').hidden = true;
  status(ready ? 'Áudio preparado. Acione “Transcrever áudio”.' : 'Modelo indisponível. Execute INSTALAR.cmd.');
  updateButtons();
}
$('file').addEventListener('change', e => choose(e.target.files[0]));
['dragover', 'dragleave', 'drop'].forEach(type => $('drop').addEventListener(type, e => {
  e.preventDefault(); $('drop').classList.toggle('drag', type === 'dragover');
  if (type === 'drop') choose(e.dataTransfer.files[0]);
}));
document.addEventListener('dragover', e => e.preventDefault());
document.addEventListener('drop', e => e.preventDefault());
function clock(seconds) {
  const s = Math.floor(seconds); return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
}
function count() {
  const text = segments.map(s => s.text).join(' ').trim();
  const n = text ? text.split(/\s+/u).length : 0;
  $('word-count').textContent = `${n} ${n === 1 ? 'palavra' : 'palavras'}`;
}
function render() {
  $('empty').hidden = segments.length > 0;
  $('segments').hidden = segments.length === 0;
  $('segments').replaceChildren();
  segments.forEach((segment, index) => {
    const row = document.createElement('div'); row.className = 'segment';
    const time = document.createElement('button'); time.textContent = clock(segment.start);
    time.title = `Ouvir trecho em ${clock(segment.start)}`;
    time.disabled = !sourceUrl;
    time.onclick = () => { $('player').currentTime = segment.start; $('player').play().catch(() => status('Use o player para ouvir o áudio.')); };
    const text = document.createElement('p'); text.textContent = segment.text;
    text.contentEditable = busy ? 'false' : 'plaintext-only'; text.setAttribute('role', 'textbox');
    text.setAttribute('aria-label', `Editar trecho ${index + 1}`);
    text.addEventListener('input', () => { segment.text = text.textContent; count(); });
    row.append(time, text); $('segments').append(row);
  }); count();
}
async function json(response) {
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Pedido inválido. Confira o arquivo.');
  return body;
}
$('start').onclick = async () => {
  if (segments.length && !confirm('Iniciar novamente e substituir o texto atual? Exporte sua revisão antes de continuar.')) return;
  busy = true; segments = []; render(); updateButtons();
  $('progress').hidden = false; $('progress').removeAttribute('value');
  $('start').textContent = 'Transcrevendo…'; status('Transferindo para o motor neste computador…');
  try {
    const form = new FormData(); form.append('file', selected); form.append('language', $('language').value);
    form.append('model_name', 'turbo'); form.append('glossary', $('glossary').value);
    const { id } = await json(await fetch('/api/jobs', { method: 'POST', headers: { 'X-Local-App': '1' }, body: form }));
    while (true) {
      const job = await json(await fetch(`/api/jobs/${id}`));
      status(job.message, job.status === 'error');
      if (job.progress > 0) $('progress').value = job.progress;
      if (job.segments.length !== segments.length) { segments = job.segments; render(); }
      if (job.status === 'error') throw new Error(job.message);
      if (job.status === 'done') {
        segments = job.segments; $('progress').value = 100;
        $('doc-hint').textContent = segments.length ? 'Clique no texto para revisar; no tempo para ouvir.' : 'Tente outro arquivo ou confira o idioma.';
        break;
      }
      await new Promise(resolve => setTimeout(resolve, 900));
    }
  } catch (error) { status(`${error.message} Se a conexão caiu, o motor pode continuar trabalhando.`, true); }
  finally { busy = false; $('start').textContent = 'Transcrever áudio ↗'; render(); updateButtons(); }
};
function stamp(seconds) {
  let ms = Math.max(0, Math.round(seconds * 1000));
  const hours = Math.floor(ms / 3600000); ms %= 3600000;
  const minutes = Math.floor(ms / 60000); ms %= 60000;
  return `${String(hours).padStart(2,'0')}:${String(minutes).padStart(2,'0')}:${String(Math.floor(ms/1000)).padStart(2,'0')},${String(ms%1000).padStart(3,'0')}`;
}
function download(extension) {
  const text = extension === 'txt' ? segments.map(s => s.text.trim()).join('\n\n') : segments.map((s, i) => `${i+1}\n${stamp(s.start)} --> ${stamp(s.end)}\n${s.text.trim()}\n`).join('\n');
  const url = URL.createObjectURL(new Blob(['\uFEFF', text], { type: 'text/plain;charset=utf-8' }));
  const a = document.createElement('a'); a.href = url; a.download = `${(selected?.name || 'transcricao-microfone').replace(/\.[^.]+$/, '')}.${extension}`;
  a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('txt').onclick = () => download('txt'); $('srt').onclick = () => download('srt');
$('copy').onclick = async () => {
  try { await navigator.clipboard.writeText(segments.map(s => s.text.trim()).join('\n\n')); status('Texto copiado.'); }
  catch { status('Não foi possível copiar. Exporte em TXT.', true); }
};
window.addEventListener('beforeunload', e => {
  if (busy || segments.length) { e.preventDefault(); e.returnValue = ''; }
});
fetch('/api/health').then(json).then(health => {
  ready = health.ready; $('engine-state').textContent = ready ? 'Pronto' : 'Ausente';
  status(ready ? 'Motor pronto. Ative o microfone ou selecione um arquivo.' : 'Instale o modelo executando INSTALAR.cmd.'); updateButtons();
}).catch(() => { $('engine-state').textContent = 'Indisponível'; status('Motor indisponível. Abra pelo atalho ABRIR-TRANSCRITOR.cmd.', true); });
