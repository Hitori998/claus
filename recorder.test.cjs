const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function recorder() {
  let Capture;
  const emitted = [];
  vm.runInNewContext(fs.readFileSync(`${__dirname}/static/recorder.js`, 'utf8'), {
    AudioWorkletProcessor: class { constructor() { this.port = {postMessage: data => emitted.push(data)}; } },
    registerProcessor: (_, ctor) => Capture = ctor, sampleRate:16000, Float32Array, Math,
  });
  return {capture:new Capture(), emitted};
}
test('continuous speech emits a bounded six-second chunk with accurate position', () => {
  const {capture, emitted} = recorder();
  const block = new Float32Array(128).fill(0.1);
  for(let i=0;i<750;i++) capture.process([[block]]);
  const chunks = emitted.filter(e=>e.samples);
  assert.equal(chunks.length,1); assert.equal(chunks[0].samples.length,96000);
  assert.equal(chunks[0].start,0); assert.equal(chunks[0].rate,16000);
  capture.process([[block]]); capture.port.onmessage({data:'flush'});
  assert.equal(emitted.at(-1).flushed,true);
});
test('silence is discarded and the next speech retains its real timeline offset', () => {
  const {capture, emitted} = recorder();
  for(let i=0;i<750;i++) capture.process([[new Float32Array(128)]]);
  assert.equal(emitted.filter(e=>e.samples).length,0);
  for(let i=0;i<150;i++) capture.process([[new Float32Array(128).fill(0.1)]]);
  capture.port.onmessage({data:'flush'});
  const chunk = emitted.find(e=>e.samples);
  assert.equal(chunk.start,6); assert.equal(chunk.samples.length,19200);
});
test('rolling context grows then stays bounded without cutting the next hypothesis into isolated chunks', () => {
  const {capture, emitted} = recorder();
  const block = new Float32Array(128).fill(0.1);
  for(let i=0;i<3000;i++) capture.process([[block]]);
  const chunks = emitted.filter(e=>e.samples);
  assert.equal(chunks.length,4);
  assert.equal(chunks[1].start,0);
  assert.equal(chunks[0].continuation,true);
  assert.equal(chunks[1].samples.length,192000);
  assert.equal(chunks[3].samples.length,288000);
  assert.equal(chunks[3].start,6);
});
