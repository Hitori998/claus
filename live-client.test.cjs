const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const {sessionAudio} = require('./static/streaming.js');

function client(fail = false) {
  const elements = new Map(), calls = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {value:'', checked:id==='final-review', textContent:'',
      classList:{toggle(){}}, setAttribute(){}, replaceChildren(){}, append(){}, removeAttribute(){}});
    return elements.get(id);
  };
  element('language').value='pt'; element('live-model').value='small';
  const scope = vm.createContext({$:element, ready:true, busy:true, segments:[{start:0,end:1,text:'prévia'}],
    navigator:{}, Option:class{}, sessionAudio, FormData, Blob, Float32Array, clearTimeout, setTimeout,
    updateButtons(){}, render(){}, status(){}, json:async response=>response,
    fetch:async (url, options) => {
      if(options) { calls.push(options.body.get('model_name')); return {id:'final'}; }
      if(fail) throw new Error('Falha de teste na revisão');
      return {status:'done',progress:100,segments:[{start:0,end:1,text:'reconhecimento final'}]};
    },
  });
  vm.runInContext(fs.readFileSync(`${__dirname}/static/live.js`,'utf8'),scope);
  return {scope,calls};
}
test('stopping runs the final Turbo pass and releases captured audio', async () => {
  const {scope,calls}=client();
  await vm.runInContext(`sessionChunks=[{start:0,rate:16000,samples:new Float32Array(16000)}]; finishing=true; completeLive()`, scope);
  assert.deepEqual(calls,['turbo']);
  assert.equal(scope.segments[0].text,'reconhecimento final');
  assert.equal(scope.busy,false);
  assert.equal(vm.runInContext('sessionChunks.length',scope),0);
});
test('a failed final pass keeps the preview available to export', async () => {
  const {scope}=client(true);
  await vm.runInContext(`sessionChunks=[{start:0,rate:16000,samples:new Float32Array(16000)}]; finishing=true; completeLive()`, scope);
  assert.equal(scope.segments[0].text,'prévia'); assert.equal(scope.busy,false);
  assert.match(vm.runInContext('liveWarning',scope),/prévia foi preservada/);
});
