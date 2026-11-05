function mergeWords(previous, incoming, offset) {
  const kept = previous.filter(word => word.start < offset - 0.05);
  for (const word of incoming) {
    const next = {...word, start:word.start + offset, end:word.end + offset};
    const last = kept.at(-1);
    if (last && next.end <= last.end + 0.03) continue;
    if (last && next.start < last.end - 0.05) continue;
    kept.push(next);
  }
  return kept;
}
function wordsToSegments(words) {
  const result = []; let count = 0;
  for (const word of words) {
    const last = result.at(-1);
    if (!last || count >= 12 || word.start - last.end > 1.5 || /[.!?]$/.test(last.text)) {
      result.push({...word}); count = 1;
    } else { last.text += ' ' + word.text; last.end = word.end; count++; }
  }
  return result;
}
function sessionAudio(chunks) {
  const rate = chunks[0].rate;
  const length = Math.max(...chunks.map(chunk => Math.round(chunk.start * rate) + chunk.samples.length));
  if (length > rate * 1806) throw new Error('A sessão excedeu o limite de 30 minutos.');
  const samples = new Float32Array(length);
  for (const chunk of chunks) {
    if (chunk.rate !== rate) throw new Error('A taxa do microfone mudou durante a sessão.');
    samples.set(chunk.samples, Math.round(chunk.start * rate));
  }
  return {samples, rate};
}
if (typeof module !== 'undefined') module.exports = {mergeWords, wordsToSegments, sessionAudio};
