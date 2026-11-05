const {test} = require('node:test');
const assert = require('node:assert/strict');
const {mergeWords, wordsToSegments, sessionAudio} = require('./static/streaming.js');

test('a new overlapping hypothesis replaces the cut word instead of appending it', () => {
  const previous = [{start:0,end:1,text:'Uma'}, {start:1,end:2.5,text:'transcri...'}];
  const result = mergeWords(previous, [{start:0,end:1,text:'transcrição'},{start:1,end:2,text:'local.'}],1);
  assert.deepEqual(result.map(w=>w.text),['Uma','transcrição','local.']);
  assert.equal(previous[1].text,'transcri...');
});
test('real repetition stays and overlapping words group into readable segments', () => {
  const result = mergeWords([{start:0,end:0.5,text:'não'}], [{start:0,end:0.5,text:'não'},{start:0.5,end:1,text:'agora.'}],0.5);
  assert.equal(wordsToSegments(result)[0].text, 'não não agora.');
});
test('session audio reconstructs overlaps once and preserves silent gaps', () => {
  const data = sessionAudio([{start:0,rate:4,samples:new Float32Array([1,2,3,4])},
                            {start:0.5,rate:4,samples:new Float32Array([3,4,5,6])},
                            {start:2,rate:4,samples:new Float32Array([7,8])}]);
  assert.deepEqual(Array.from(data.samples),[1,2,3,4,5,6,0,0,7,8]);
});
test('a word crossing the buffer boundary is kept instead of replaced by its cut suffix', () => {
  const result = mergeWords([{start:3.8,end:4.1,text:'O'},{start:4.1,end:4.9,text:'aplicativo'}],
    [{start:0,end:0.2,text:'o'},{start:0.2,end:0.4,text:'ativo'},{start:0.5,end:1,text:'transforma'}],4.5);
  assert.deepEqual(result.map(w=>w.text),['O','aplicativo','transforma']);
});
